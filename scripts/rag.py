#!/usr/bin/env python3
"""
Local RAG index, embeddings, and retrieval for GalacticX.

The base retriever is dependency-free BM25. Optional embedding retrieval
uses either OpenAI's embeddings API through the standard library or a
deterministic offline hash provider for no-key validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_INDEX = ".rag/index.jsonl"
DEFAULT_EMBEDDINGS = ".rag/embeddings.jsonl"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_HASH_DIMENSIONS = 384
MAX_TEXT_FILE_BYTES = 512_000
CHUNK_MAX_LINES = 90
CHUNK_OVERLAP_LINES = 12
CHUNK_MAX_CHARS = 9_000

INCLUDE_SUFFIXES = {
    ".gd",
    ".tscn",
    ".godot",
    ".md",
    ".json",
    ".toml",
    ".py",
    ".cfg",
    ".txt",
}

EXCLUDE_DIRS = {
    ".git",
    ".godot",
    ".import",
    ".rag",
    "__pycache__",
    "sandbox",
}

EXCLUDE_FILES = {
    ".env",
    ".mcp.json",
    ".DS_Store",
}
EXCLUDE_PATHS = {
    "docs/rag.md",
}

TOKEN_RE = re.compile(r"[a-z0-9_]+")
STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "can",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "should",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "with",
    "work",
}


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    path: str
    kind: str
    start_line: int
    end_line: int
    text: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and query the GalacticX local RAG index.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Build the local RAG index.")
    index_parser.add_argument("--root", default=".", help="Repository root to index.")
    index_parser.add_argument("--out", default=DEFAULT_INDEX, help="Index JSONL output path.")

    embed_parser = subparsers.add_parser("embed", help="Build semantic embeddings for the local RAG index.")
    embed_parser.add_argument("--index", default=DEFAULT_INDEX, help="Index JSONL path.")
    embed_parser.add_argument("--out", default=DEFAULT_EMBEDDINGS, help="Embeddings JSONL output path.")
    embed_parser.add_argument("--provider", choices=["auto", "openai", "hash"], default="auto", help="Embedding provider.")
    embed_parser.add_argument("--model", default=None, help="Embedding model. Defaults to text-embedding-3-small for OpenAI.")
    embed_parser.add_argument("--dimensions", type=int, default=None, help="Embedding dimensions when supported.")
    embed_parser.add_argument("--batch-size", type=int, default=64, help="Texts per embedding request.")
    embed_parser.add_argument("--force", action="store_true", help="Recompute all embeddings instead of reusing matching cached rows.")

    search_parser = subparsers.add_parser("search", help="Search the RAG index.")
    search_parser.add_argument("query", help="Search query.")
    search_parser.add_argument("--index", default=DEFAULT_INDEX, help="Index JSONL path.")
    search_parser.add_argument("--embeddings", default=DEFAULT_EMBEDDINGS, help="Embeddings JSONL path.")
    search_parser.add_argument("--top", type=int, default=8, help="Number of chunks to return.")
    add_retrieval_mode_args(search_parser)

    context_parser = subparsers.add_parser("context", help="Print retrieved context for an AI prompt.")
    context_parser.add_argument("query", help="Question or task to ground.")
    context_parser.add_argument("--index", default=DEFAULT_INDEX, help="Index JSONL path.")
    context_parser.add_argument("--embeddings", default=DEFAULT_EMBEDDINGS, help="Embeddings JSONL path.")
    context_parser.add_argument("--top", type=int, default=8, help="Number of chunks to retrieve.")
    context_parser.add_argument("--max-chars", type=int, default=8_000, help="Maximum context characters.")
    add_retrieval_mode_args(context_parser)

    args = parser.parse_args()

    if args.command == "index":
        chunks = build_index(Path(args.root).resolve())
        write_index(chunks, Path(args.out))
        print(f"Indexed {len(chunks)} chunks into {args.out}")
        return 0

    if args.command == "embed":
        records = read_index(Path(args.index))
        provider = resolve_provider(args.provider)
        model = resolve_model(provider, args.model)
        dimensions = resolve_dimensions(provider, args.dimensions)
        embed_records(records, Path(args.out), provider, model, dimensions, args.batch_size, args.force)
        return 0

    if args.command == "search":
        records = read_index(Path(args.index))
        results = retrieve(records, args.query, args.top, args, Path(args.embeddings))
        print_search_results(results)
        return 0

    if args.command == "context":
        records = read_index(Path(args.index))
        results = retrieve(records, args.query, args.top, args, Path(args.embeddings))
        print_context(args.query, results, args.max_chars)
        return 0

    return 1


def add_retrieval_mode_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--mode",
        choices=["lexical", "semantic", "hybrid"],
        default="lexical",
        help="Retrieval mode. Lexical is BM25, semantic uses embeddings, hybrid blends both.",
    )
    parser.add_argument("--semantic-weight", type=float, default=0.65, help="Hybrid semantic score weight.")
    parser.add_argument("--lexical-weight", type=float, default=0.35, help="Hybrid lexical score weight.")


def build_index(root: Path) -> list[Chunk]:
    chunks: list[Chunk] = []

    for path in iter_indexable_files(root):
        rel_path = path.relative_to(root).as_posix()
        text = read_text_file(path)
        if text is None:
            continue

        normalized = normalize_json_text(text, rel_path) if path.suffix == ".json" else text
        chunks.extend(chunk_text(rel_path, kind_for_path(path, rel_path), normalized))

    asset_inventory = build_asset_inventory(root)
    if asset_inventory:
        chunks.extend(chunk_text("assets/asset_inventory.generated", "asset_inventory", asset_inventory))

    return chunks


def iter_indexable_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        rel_parts = path.relative_to(root).parts
        rel_path = path.relative_to(root).as_posix()
        if rel_path in EXCLUDE_PATHS:
            continue
        if any(part in EXCLUDE_DIRS for part in rel_parts):
            continue
        if path.name in EXCLUDE_FILES:
            continue
        if path.suffix not in INCLUDE_SUFFIXES:
            continue
        if should_skip_json(path):
            continue
        if path.stat().st_size > MAX_TEXT_FILE_BYTES:
            continue

        yield path


def should_skip_json(path: Path) -> bool:
    if path.suffix != ".json":
        return False

    name = path.name
    if name == "metadata.json":
        return False
    if name.endswith(".summary.json"):
        return False
    if "job_result" in name or "submit" in name:
        return True
    return False


def read_text_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def normalize_json_text(text: str, rel_path: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text

    return json.dumps(data, indent=2, sort_keys=True) + f"\n\nSource: {rel_path}\n"


def build_asset_inventory(root: Path) -> str:
    image_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
    scan_roots = [
        root / "assets" / "sprites",
        root / "assets" / "tilesets",
        root / "assets" / "maps",
    ]
    lines = ["# Asset Image Inventory", ""]

    for asset_root in scan_roots:
        if not asset_root.exists():
            continue
        for path in sorted(asset_root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in image_suffixes:
                continue
            if any(part in EXCLUDE_DIRS for part in path.relative_to(root).parts):
                continue
            lines.append(path.relative_to(root).as_posix())

    return "\n".join(lines)


def kind_for_path(path: Path, rel_path: str) -> str:
    if rel_path == "docs/repo-wiki.md":
        return "repo_wiki"
    if path.suffix == ".gd":
        return "gdscript"
    if path.suffix == ".tscn":
        return "godot_scene"
    if path.name == "project.godot":
        return "godot_project"
    if path.suffix == ".md" and rel_path.startswith(".claude/"):
        return "claude_instruction"
    if path.suffix == ".json" and path.name == "metadata.json":
        return "asset_metadata"
    if path.suffix == ".py":
        return "python_tool"
    return path.suffix.lstrip(".") or "text"


def chunk_text(path: str, kind: str, text: str) -> list[Chunk]:
    lines = text.splitlines()
    chunks: list[Chunk] = []

    if not lines:
        return chunks

    start = 0
    while start < len(lines):
        end = min(start + CHUNK_MAX_LINES, len(lines))
        chunk_lines = lines[start:end]

        while len("\n".join(chunk_lines)) > CHUNK_MAX_CHARS and len(chunk_lines) > 20:
            chunk_lines = chunk_lines[: max(20, len(chunk_lines) // 2)]
            end = start + len(chunk_lines)

        chunk_id = f"{path}:{start + 1}-{end}"
        chunks.append(Chunk(
            chunk_id=chunk_id,
            path=path,
            kind=kind,
            start_line=start + 1,
            end_line=end,
            text="\n".join(chunk_lines).strip(),
        ))

        if end >= len(lines):
            break
        start = max(end - CHUNK_OVERLAP_LINES, start + 1)

    return chunks


def write_index(chunks: list[Chunk], index_path: Path) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            terms = Counter(tokenize(" ".join([chunk.path, chunk.kind, chunk.text])))
            record = {
                "id": chunk.chunk_id,
                "path": chunk.path,
                "kind": chunk.kind,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "text": chunk.text,
                "terms": dict(terms),
                "length": sum(terms.values()),
            }
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_index(index_path: Path) -> list[dict]:
    if not index_path.exists():
        raise SystemExit(f"Index not found: {index_path}. Run: python3 scripts/rag.py index")

    records: list[dict] = []
    with index_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def embed_records(
    records: list[dict],
    embeddings_path: Path,
    provider: str,
    model: str,
    dimensions: int | None,
    batch_size: int,
    force: bool,
) -> None:
    if not records:
        raise SystemExit("Index has no records. Run: python3 scripts/rag.py index")

    existing = {} if force else read_embeddings(embeddings_path, allow_missing=True)
    rows: list[dict] = []
    pending: list[dict] = []

    for record in records:
        source_hash = record_source_hash(record)
        cached = existing.get(record["id"])
        if cached and embedding_matches(cached, provider, model, dimensions, source_hash):
            rows.append(cached)
        else:
            pending.append(record)

    if pending:
        provider_client = EmbeddingProvider(provider, model, dimensions)
        for batch in batched(pending, max(batch_size, 1)):
            texts = [embedding_text(record) for record in batch]
            vectors = provider_client.embed(texts)
            for record, vector in zip(batch, vectors):
                rows.append({
                    "id": record["id"],
                    "path": record["path"],
                    "kind": record["kind"],
                    "provider": provider,
                    "model": model,
                    "dimensions": len(vector),
                    "requested_dimensions": dimensions,
                    "source_hash": record_source_hash(record),
                    "embedding": vector,
                })

    row_by_id = {row["id"]: row for row in rows}
    ordered_rows = [row_by_id[record["id"]] for record in records if record["id"] in row_by_id]

    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    with embeddings_path.open("w", encoding="utf-8") as handle:
        for row in ordered_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    reused = len(records) - len(pending)
    print(
        f"Embedded {len(pending)} chunks, reused {reused}, wrote {len(ordered_rows)} rows "
        f"to {embeddings_path} using {provider}:{model}"
    )


def read_embeddings(embeddings_path: Path, allow_missing: bool = False) -> dict[str, dict]:
    if not embeddings_path.exists():
        if allow_missing:
            return {}
        raise SystemExit(f"Embeddings not found: {embeddings_path}. Run: python3 scripts/rag.py embed")

    rows: dict[str, dict] = {}
    with embeddings_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def retrieve(records: list[dict], query: str, top: int, args: argparse.Namespace, embeddings_path: Path) -> list[tuple[float, dict]]:
    if args.mode == "lexical":
        return lexical_search(records, query, top)

    if args.mode == "semantic":
        embeddings = read_embeddings(embeddings_path)
        return semantic_search(records, embeddings, query, top)

    embeddings = read_embeddings(embeddings_path)
    return hybrid_search(
        records,
        embeddings,
        query,
        top,
        semantic_weight=args.semantic_weight,
        lexical_weight=args.lexical_weight,
    )


def search(records: list[dict], query: str, top: int) -> list[tuple[float, dict]]:
    return lexical_search(records, query, top)


def lexical_search(records: list[dict], query: str, top: int) -> list[tuple[float, dict]]:
    query_terms = tokenize(query)
    if not query_terms:
        return []

    doc_freq: dict[str, int] = defaultdict(int)
    for record in records:
        terms = record["terms"]
        for term in set(query_terms):
            if term in terms:
                doc_freq[term] += 1

    avg_len = sum(record["length"] for record in records) / max(len(records), 1)
    scored: list[tuple[float, dict]] = []

    for record in records:
        score = bm25_score(record, query_terms, doc_freq, len(records), avg_len)
        score += path_boost(record, query_terms)
        if score > 0.0:
            scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:top]


def semantic_search(records: list[dict], embeddings: dict[str, dict], query: str, top: int) -> list[tuple[float, dict]]:
    if not embeddings:
        return []

    embedding_rows = compatible_embedding_rows(records, embeddings)
    if not embedding_rows:
        raise SystemExit("No embeddings match the current index. Run: python3 scripts/rag.py embed --force")

    query_vector = embed_query(query, embedding_rows[0])
    record_by_id = {record["id"]: record for record in records}
    scored: list[tuple[float, dict]] = []

    for row in embedding_rows:
        record = record_by_id.get(row["id"])
        if record is None:
            continue
        score = cosine_similarity(query_vector, row["embedding"])
        scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:top]


def hybrid_search(
    records: list[dict],
    embeddings: dict[str, dict],
    query: str,
    top: int,
    semantic_weight: float,
    lexical_weight: float,
) -> list[tuple[float, dict]]:
    lexical = lexical_search(records, query, max(len(records), top))
    semantic = semantic_search(records, embeddings, query, max(len(records), top))

    lexical_scores = normalize_scores({record["id"]: score for score, record in lexical})
    semantic_scores = normalize_scores({record["id"]: score for score, record in semantic})
    record_by_id = {record["id"]: record for record in records}

    combined_ids = set(lexical_scores) | set(semantic_scores)
    scored: list[tuple[float, dict]] = []

    for record_id in combined_ids:
        record = record_by_id.get(record_id)
        if record is None:
            continue
        score = semantic_scores.get(record_id, 0.0) * semantic_weight
        score += lexical_scores.get(record_id, 0.0) * lexical_weight
        if score > 0.0:
            scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:top]


class EmbeddingProvider:
    def __init__(self, provider: str, model: str, dimensions: int | None) -> None:
        self.provider = provider
        self.model = model
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if self.provider == "hash":
            return [hash_embedding(text, self.dimensions or DEFAULT_HASH_DIMENSIONS) for text in texts]
        if self.provider == "openai":
            return openai_embeddings(texts, self.model, self.dimensions)
        raise SystemExit(f"Unsupported embedding provider: {self.provider}")


def resolve_provider(provider: str) -> str:
    if provider != "auto":
        return provider

    load_env_file()
    return "openai" if os.environ.get("OPENAI_API_KEY") else "hash"


def resolve_model(provider: str, model: str | None) -> str:
    if model:
        return model
    if provider == "openai":
        load_env_file()
        return os.environ.get("RAG_OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL)
    return "local-hash"


def resolve_dimensions(provider: str, dimensions: int | None) -> int | None:
    if dimensions is not None:
        return dimensions
    if provider == "hash":
        return DEFAULT_HASH_DIMENSIONS

    load_env_file()
    env_dimensions = os.environ.get("RAG_OPENAI_EMBEDDING_DIMENSIONS")
    if env_dimensions:
        return int(env_dimensions)
    return None


def load_env_file() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return

    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def openai_embeddings(texts: Sequence[str], model: str, dimensions: int | None) -> list[list[float]]:
    load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required for --provider openai")

    endpoint = os.environ.get("OPENAI_EMBEDDINGS_URL", "https://api.openai.com/v1/embeddings")
    payload: dict[str, object] = {
        "model": model,
        "input": list(texts),
    }
    if dimensions is not None:
        payload["dimensions"] = dimensions

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"OpenAI embeddings request failed ({error.code}): {detail}") from error
    except urllib.error.URLError as error:
        raise SystemExit(f"OpenAI embeddings request failed: {error}") from error

    rows = sorted(data.get("data", []), key=lambda item: item["index"])
    vectors = [normalize_vector(row["embedding"]) for row in rows]
    if len(vectors) != len(texts):
        raise SystemExit(f"Embedding count mismatch: expected {len(texts)}, got {len(vectors)}")

    time.sleep(0.05)
    return vectors


def hash_embedding(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    terms = tokenize(text)

    for term in terms:
        add_hashed_term(vector, term, 1.0)
        for index in range(max(len(term) - 2, 0)):
            add_hashed_term(vector, term[index:index + 3], 0.35)

    return normalize_vector(vector)


def add_hashed_term(vector: list[float], term: str, weight: float) -> None:
    digest = hashlib.sha256(term.encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "big") % len(vector)
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    vector[index] += sign * weight


def normalize_vector(vector: Sequence[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0.0:
        return [0.0 for _ in vector]
    return [float(value) / magnitude for value in vector]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def record_source_hash(record: dict) -> str:
    payload = json.dumps({
        "id": record["id"],
        "path": record["path"],
        "kind": record["kind"],
        "text": record["text"],
    }, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def embedding_text(record: dict) -> str:
    return "\n".join([
        f"path: {record['path']}",
        f"kind: {record['kind']}",
        record["text"],
    ])


def embedding_matches(row: dict, provider: str, model: str, dimensions: int | None, source_hash: str) -> bool:
    if row.get("provider") != provider:
        return False
    if row.get("model") != model:
        return False
    if row.get("requested_dimensions") != dimensions:
        return False
    return row.get("source_hash") == source_hash


def compatible_embedding_rows(records: list[dict], embeddings: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    for record in records:
        row = embeddings.get(record["id"])
        if row is None:
            continue
        if row.get("source_hash") != record_source_hash(record):
            continue
        rows.append(row)
    return rows


def embed_query(query: str, sample_row: dict) -> list[float]:
    provider = sample_row["provider"]
    model = sample_row["model"]
    dimensions = sample_row.get("requested_dimensions")
    provider_client = EmbeddingProvider(provider, model, dimensions)
    vectors = provider_client.embed([query])
    return vectors[0]


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}

    min_score = min(scores.values())
    max_score = max(scores.values())
    if math.isclose(max_score, min_score):
        return {key: 1.0 for key in scores}

    return {key: (value - min_score) / (max_score - min_score) for key, value in scores.items()}


def batched(items: Sequence[dict], batch_size: int) -> Iterable[Sequence[dict]]:
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def bm25_score(record: dict, query_terms: list[str], doc_freq: dict[str, int], total_docs: int, avg_len: float) -> float:
    k1 = 1.5
    b = 0.75
    terms = record["terms"]
    doc_len = max(record["length"], 1)
    score = 0.0

    for term in query_terms:
        freq = terms.get(term, 0)
        if freq == 0:
            continue

        df = doc_freq.get(term, 0)
        idf = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))
        denominator = freq + k1 * (1.0 - b + b * doc_len / max(avg_len, 1.0))
        score += idf * (freq * (k1 + 1.0)) / denominator

    return score


def path_boost(record: dict, query_terms: list[str]) -> float:
    path_terms = set(tokenize(record["path"]))
    kind_terms = set(tokenize(record["kind"]))
    boost = 0.0

    for term in set(query_terms):
        if term in path_terms:
            boost += 0.8
        if term in kind_terms:
            boost += 0.4

    return boost


def tokenize(text: str) -> list[str]:
    raw_terms = TOKEN_RE.findall(text.lower())
    terms: list[str] = []

    for term in raw_terms:
        terms.append(term)
        if "_" in term:
            terms.extend(part for part in term.split("_") if part)

    return [term for term in terms if len(term) > 1 and term not in STOPWORDS]


def print_search_results(results: list[tuple[float, dict]]) -> None:
    if not results:
        print("No matches.")
        return

    for rank, (score, record) in enumerate(results, start=1):
        snippet = first_snippet(record["text"])
        print(f"{rank}. {record['path']}:{record['start_line']}-{record['end_line']} [{record['kind']}] score={score:.3f}")
        print(f"   {snippet}")


def print_context(query: str, results: list[tuple[float, dict]], max_chars: int) -> None:
    print(f"# Retrieved context for: {query}\n")

    used = 0
    for rank, (score, record) in enumerate(results, start=1):
        header = f"## {rank}. {record['path']}:{record['start_line']}-{record['end_line']} [{record['kind']}] score={score:.3f}\n"
        body = record["text"].strip() + "\n\n"

        if used + len(header) + len(body) > max_chars:
            remaining = max_chars - used - len(header)
            if remaining <= 200:
                break
            body = body[:remaining].rstrip() + "\n\n"

        print(header + body)
        used += len(header) + len(body)


def first_snippet(text: str) -> str:
    compact = " ".join(line.strip() for line in text.splitlines() if line.strip())
    if len(compact) <= 160:
        return compact
    return compact[:157].rstrip() + "..."


if __name__ == "__main__":
    sys.exit(main())
