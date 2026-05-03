# GalacticX RAG

This repository includes a local retrieval layer for project-aware questions about the Godot game, scripts, scenes, assets, and Claude project agents.

The canonical RAG-indexed wiki is `docs/repo-wiki.md`. Use the `galacticx-rag-wiki-documenter` Claude project agent when that wiki needs to be refreshed.

Build the lexical index:

```bash
python3 scripts/rag.py index
```

Build embeddings:

```bash
# Uses OpenAI when OPENAI_API_KEY is present; otherwise uses the offline hash provider.
python3 scripts/rag.py embed

# Force real semantic embeddings through OpenAI.
OPENAI_API_KEY=... python3 scripts/rag.py embed --provider openai --model text-embedding-3-small

# Offline deterministic vectors. Useful for testing the embedding pipeline without network/API cost.
python3 scripts/rag.py embed --provider hash
```

Search the index with lexical, semantic, or hybrid retrieval:

```bash
python3 scripts/rag.py search "8-direction animation loader"
python3 scripts/rag.py search "PixelLab tileset asset pipeline" --mode semantic
python3 scripts/rag.py search "starship boarding scene level design" --mode hybrid
```

Create copyable context for an AI prompt:

```bash
python3 scripts/rag.py context "how should the starship boarding scene guide level design" --mode hybrid
```

The lexical index is written to `.rag/index.jsonl`; embeddings are written to `.rag/embeddings.jsonl`. Both are intentionally ignored by git.

The generated asset inventory includes image paths from `assets/sprites/`, `assets/tilesets/`, and `assets/maps/`, including imported spaceship tileset sheets.

The OpenAI provider uses the embeddings endpoint directly through Python's standard library, so the OpenAI Python package is not required. `text-embedding-3-small` is the default model for OpenAI embeddings, and `RAG_OPENAI_EMBEDDING_MODEL` / `RAG_OPENAI_EMBEDDING_DIMENSIONS` can override it.

The retriever does not call an LLM by itself; use `context` output as the grounding payload for Claude, Codex, or another model.
