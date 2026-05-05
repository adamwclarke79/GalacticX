#!/usr/bin/env python3
"""Build a numbered HTML catalog from the imported spaceship tileset.

Tileset sheets are cut into 48x48 cells. RPG Maker-style character/object
sheets are cut into object frames:

- !$*.png: 3 columns x 4 rows
- !*.png: 12 columns x 8 rows
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "assets/tilesets/spaceship_tileset/Spaceship Tileset"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs/tileset_catalog"
TRANSPARENT_THRESHOLD = 4


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    category: str
    sheet: str
    source: str
    image: str
    row: int
    column: int
    x: int
    y: int
    width: int
    height: int


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return cleaned or "asset"


def is_visually_empty(image: Image.Image) -> bool:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if alpha.getbbox() is None:
        return True
    return max(alpha.getextrema()) <= TRANSPARENT_THRESHOLD


def iter_sheet_cells(source_root: Path) -> list[tuple[str, Path, int, int]]:
    cells: list[tuple[str, Path, int, int]] = []

    for path in sorted((source_root / "tilesets").glob("*.png")):
        cells.append(("tile", path, 48, 48))

    for path in sorted((source_root / "characters").glob("*.png")):
        with Image.open(path) as image:
            width, height = image.size
        name = path.name
        if name.startswith("!$"):
            cells.append(("object_frame", path, width // 3, height // 4))
        elif name.startswith("!"):
            cells.append(("object_frame", path, width // 12, height // 8))
        else:
            cells.append(("object_frame", path, 48, 48))

    return cells


def build_catalog(source_root: Path, output_dir: Path, include_empty: bool) -> list[CatalogEntry]:
    slices_dir = output_dir / "slices"
    if slices_dir.exists():
        shutil.rmtree(slices_dir)
    slices_dir.mkdir(parents=True, exist_ok=True)

    entries: list[CatalogEntry] = []
    next_number = 1

    for category, path, cell_width, cell_height in iter_sheet_cells(source_root):
        sheet_rel = path.relative_to(source_root).as_posix()
        sheet_slug = slugify(path.stem)
        sheet_output_dir = slices_dir / sheet_slug
        sheet_output_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(path) as source_image:
            rgba = source_image.convert("RGBA")
            columns = source_image.width // cell_width
            rows = source_image.height // cell_height

            for row in range(rows):
                for column in range(columns):
                    x = column * cell_width
                    y = row * cell_height
                    cell = rgba.crop((x, y, x + cell_width, y + cell_height))
                    if not include_empty and is_visually_empty(cell):
                        continue

                    entry_id = f"GX{next_number:04d}"
                    image_name = f"{entry_id}__{sheet_slug}__r{row:02d}_c{column:02d}.png"
                    image_path = sheet_output_dir / image_name
                    cell.save(image_path)

                    entries.append(
                        CatalogEntry(
                            id=entry_id,
                            category=category,
                            sheet=path.stem,
                            source=sheet_rel,
                            image=image_path.relative_to(output_dir).as_posix(),
                            row=row,
                            column=column,
                            x=x,
                            y=y,
                            width=cell_width,
                            height=cell_height,
                        )
                    )
                    next_number += 1

    return entries


def write_manifest(entries: list[CatalogEntry], source_root: Path, output_dir: Path) -> None:
    manifest = {
        "source_root": source_root.relative_to(PROJECT_ROOT).as_posix()
        if source_root.is_relative_to(PROJECT_ROOT)
        else source_root.as_posix(),
        "entry_count": len(entries),
        "entries": [asdict(entry) for entry in entries],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_html(entries: list[CatalogEntry], output_dir: Path) -> None:
    sheets = sorted({entry.sheet for entry in entries})
    categories = sorted({entry.category for entry in entries})

    cards: list[str] = []
    for entry in entries:
        cards.append(
            f"""
      <article class="card" data-id="{entry.id}" data-category="{html.escape(entry.category)}" data-sheet="{html.escape(entry.sheet)}" data-source="{html.escape(entry.source)}" data-image="{html.escape(entry.image)}" data-row="{entry.row}" data-column="{entry.column}" data-x="{entry.x}" data-y="{entry.y}" data-width="{entry.width}" data-height="{entry.height}" data-search="{html.escape((entry.id + ' ' + entry.sheet + ' ' + entry.source).lower())}">
        <div class="asset-header">
          <div class="asset-id">{entry.id}</div>
          <button class="copy-button" type="button" data-copy="{entry.id}" title="Copy {entry.id}">Copy</button>
        </div>
        <button class="preview" type="button" data-zoom title="Zoom {entry.id}">
          <img src="{html.escape(entry.image)}" alt="{entry.id} from {html.escape(entry.sheet)}" loading="lazy">
        </button>
        <dl>
          <dt>Sheet</dt><dd>{html.escape(entry.sheet)}</dd>
          <dt>Type</dt><dd>{html.escape(entry.category)}</dd>
          <dt>Cell</dt><dd>r{entry.row} c{entry.column}</dd>
          <dt>Atlas</dt><dd>x{entry.x} y{entry.y} {entry.width}x{entry.height}</dd>
        </dl>
      </article>"""
        )

    sheet_options = "\n".join(f'<option value="{html.escape(sheet)}">{html.escape(sheet)}</option>' for sheet in sheets)
    category_options = "\n".join(
        f'<option value="{html.escape(category)}">{html.escape(category)}</option>' for category in categories
    )
    cards_html = "".join(cards).lstrip("\n")

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GalacticX Spaceship Tileset Catalog</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0d1114;
      --panel: #151b20;
      --panel-2: #1c242a;
      --text: #eaf4f5;
      --muted: #93a4aa;
      --accent: #8cecff;
      --border: #2c3940;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: grid;
      gap: 12px;
      padding: 16px;
      background: rgba(13, 17, 20, 0.94);
      border-bottom: 1px solid var(--border);
      backdrop-filter: blur(10px);
    }}
    h1 {{
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .meta {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .filters {{
      display: grid;
      grid-template-columns: minmax(180px, 1fr) 180px minmax(220px, 320px);
      gap: 10px;
      align-items: center;
    }}
    select, input {{
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel);
      color: var(--text);
      padding: 9px 10px;
      font: inherit;
    }}
    main {{
      padding: 16px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 12px;
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel);
      overflow: hidden;
    }}
    .asset-header {{
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: center;
      gap: 8px;
      background: #050708;
      border-bottom: 1px solid var(--border);
    }}
    .asset-id {{
      padding: 8px 10px;
      color: var(--accent);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-weight: 700;
    }}
    .copy-button, .modal-button {{
      border: 1px solid var(--border);
      border-radius: 6px;
      background: var(--panel-2);
      color: var(--text);
      padding: 7px 9px;
      font: inherit;
      font-size: 12px;
      cursor: pointer;
    }}
    .copy-button {{
      margin-right: 8px;
    }}
    .preview {{
      display: grid;
      place-items: center;
      width: 100%;
      min-height: 112px;
      padding: 12px;
      border: 0;
      border-bottom: 1px solid var(--border);
      background:
        linear-gradient(45deg, #10161a 25%, transparent 25%),
        linear-gradient(-45deg, #10161a 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #10161a 75%),
        linear-gradient(-45deg, transparent 75%, #10161a 75%);
      background-color: var(--panel-2);
      background-size: 18px 18px;
      background-position: 0 0, 0 9px, 9px -9px, -9px 0;
      cursor: zoom-in;
    }}
    .preview img {{
      max-width: 128px;
      max-height: 128px;
      width: auto;
      height: auto;
      image-rendering: pixelated;
    }}
    dl {{
      display: grid;
      grid-template-columns: 42px 1fr;
      gap: 3px 8px;
      margin: 0;
      padding: 10px;
      font-size: 12px;
    }}
    dt {{
      color: var(--muted);
    }}
    dd {{
      min-width: 0;
      margin: 0;
      overflow-wrap: anywhere;
    }}
    .modal {{
      position: fixed;
      inset: 0;
      z-index: 100;
      display: grid;
      place-items: center;
      padding: 20px;
    }}
    .modal-backdrop {{
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.72);
    }}
    .modal-panel {{
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-rows: auto auto minmax(220px, 1fr) auto;
      width: min(960px, 100%);
      max-height: calc(100vh - 40px);
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel);
      overflow: hidden;
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
    }}
    .modal-titlebar {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: center;
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      background: #050708;
    }}
    .modal-titlebar h2 {{
      margin: 0;
      color: var(--accent);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 16px;
      letter-spacing: 0;
    }}
    .modal-toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
    }}
    .zoom-range {{
      width: min(280px, 44vw);
    }}
    .zoom-value {{
      min-width: 38px;
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
    }}
    .zoom-stage {{
      display: grid;
      align-items: start;
      justify-items: center;
      min-height: 260px;
      overflow: auto;
      padding: 24px;
      background:
        linear-gradient(45deg, #10161a 25%, transparent 25%),
        linear-gradient(-45deg, #10161a 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #10161a 75%),
        linear-gradient(-45deg, transparent 75%, #10161a 75%);
      background-color: var(--panel-2);
      background-size: 24px 24px;
      background-position: 0 0, 0 12px, 12px -12px, -12px 0;
    }}
    .zoom-stage img {{
      display: block;
      max-width: none;
      max-height: none;
      image-rendering: pixelated;
    }}
    .modal-details {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 6px 12px;
      margin: 0;
      padding: 12px 14px;
      border-top: 1px solid var(--border);
      font-size: 12px;
    }}
    .modal-details dt {{
      margin-bottom: 2px;
    }}
    .modal-open {{
      overflow: hidden;
    }}
    .hidden {{ display: none; }}
    @media (max-width: 720px) {{
      .filters {{
        grid-template-columns: 1fr;
      }}
      .modal {{
        padding: 10px;
      }}
      .modal-panel {{
        max-height: calc(100vh - 20px);
      }}
      .modal-details {{
        grid-template-columns: 1fr 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>GalacticX Spaceship Tileset Catalog</h1>
      <p class="meta"><span id="visible-count">{len(entries)}</span> / {len(entries)} numbered slices. Click a thumbnail to zoom; use Copy to copy its ID.</p>
    </div>
    <div class="filters">
      <select id="sheet-filter" aria-label="Filter by source sheet">
        <option value="">All sheets</option>
        {sheet_options}
      </select>
      <select id="category-filter" aria-label="Filter by category">
        <option value="">All types</option>
        {category_options}
      </select>
      <input id="search" type="search" placeholder="Search ID, sheet, source path">
    </div>
  </header>
  <main>
    <section class="grid" id="catalog">
{cards_html}
    </section>
  </main>
  <div class="modal hidden" id="zoom-modal" aria-hidden="true" role="dialog" aria-modal="true" aria-labelledby="zoom-title">
    <div class="modal-backdrop" data-close-modal></div>
    <section class="modal-panel">
      <div class="modal-titlebar">
        <h2 id="zoom-title">GX0000</h2>
        <button class="modal-button" type="button" id="zoom-close">Close</button>
      </div>
      <div class="modal-toolbar">
        <button class="modal-button" type="button" id="zoom-out">-</button>
        <input class="zoom-range" id="zoom-range" type="range" min="1" max="16" step="1" value="6" aria-label="Zoom level">
        <button class="modal-button" type="button" id="zoom-in">+</button>
        <span class="zoom-value" id="zoom-value">6x</span>
        <button class="modal-button" type="button" id="zoom-copy">Copy ID</button>
      </div>
      <div class="zoom-stage">
        <img id="zoom-image" alt="">
      </div>
      <dl class="modal-details">
        <div><dt>Sheet</dt><dd id="zoom-sheet"></dd></div>
        <div><dt>Type</dt><dd id="zoom-category"></dd></div>
        <div><dt>Cell</dt><dd id="zoom-cell"></dd></div>
        <div><dt>Atlas</dt><dd id="zoom-atlas"></dd></div>
        <div><dt>Source</dt><dd id="zoom-source"></dd></div>
      </dl>
    </section>
  </div>
  <script>
    const sheetFilter = document.getElementById('sheet-filter');
    const categoryFilter = document.getElementById('category-filter');
    const search = document.getElementById('search');
    const visibleCount = document.getElementById('visible-count');
    const cards = Array.from(document.querySelectorAll('.card'));
    const zoomModal = document.getElementById('zoom-modal');
    const zoomTitle = document.getElementById('zoom-title');
    const zoomImage = document.getElementById('zoom-image');
    const zoomRange = document.getElementById('zoom-range');
    const zoomValue = document.getElementById('zoom-value');
    const zoomSheet = document.getElementById('zoom-sheet');
    const zoomCategory = document.getElementById('zoom-category');
    const zoomCell = document.getElementById('zoom-cell');
    const zoomAtlas = document.getElementById('zoom-atlas');
    const zoomSource = document.getElementById('zoom-source');
    const zoomCopy = document.getElementById('zoom-copy');
    const zoomClose = document.getElementById('zoom-close');
    const zoomIn = document.getElementById('zoom-in');
    const zoomOut = document.getElementById('zoom-out');
    let activeCard = null;
    let activeZoom = 6;

    function applyFilters() {{
      const sheet = sheetFilter.value;
      const category = categoryFilter.value;
      const query = search.value.trim().toLowerCase();
      let visible = 0;

      for (const card of cards) {{
        const matchesSheet = !sheet || card.dataset.sheet === sheet;
        const matchesCategory = !category || card.dataset.category === category;
        const matchesQuery = !query || card.dataset.search.includes(query);
        const show = matchesSheet && matchesCategory && matchesQuery;
        card.classList.toggle('hidden', !show);
        if (show) visible += 1;
      }}

      visibleCount.textContent = String(visible);
    }}

    sheetFilter.addEventListener('change', applyFilters);
    categoryFilter.addEventListener('change', applyFilters);
    search.addEventListener('input', applyFilters);

    async function copyId(id, control) {{
      try {{
        await navigator.clipboard.writeText(id);
        if (control) control.title = `Copied ${{id}}`;
      }} catch (_error) {{
        if (control) control.title = id;
      }}
    }}

    function applyZoom(value) {{
      activeZoom = Math.max(1, Math.min(16, Number(value) || 1));
      zoomRange.value = String(activeZoom);
      zoomValue.textContent = `${{activeZoom}}x`;

      const width = Number(zoomImage.dataset.width) || zoomImage.naturalWidth || 48;
      const height = Number(zoomImage.dataset.height) || zoomImage.naturalHeight || 48;
      zoomImage.style.width = `${{width * activeZoom}}px`;
      zoomImage.style.height = `${{height * activeZoom}}px`;
    }}

    function openZoom(card) {{
      activeCard = card;
      const id = card.dataset.id;
      const width = Number(card.dataset.width) || 48;
      const height = Number(card.dataset.height) || 48;

      activeZoom = card.dataset.category === 'tile' ? 8 : 4;
      zoomTitle.textContent = `${{id}} - ${{card.dataset.sheet}}`;
      zoomImage.src = card.dataset.image;
      zoomImage.alt = `${{id}} from ${{card.dataset.sheet}}`;
      zoomImage.dataset.width = String(width);
      zoomImage.dataset.height = String(height);
      zoomSheet.textContent = card.dataset.sheet;
      zoomCategory.textContent = card.dataset.category;
      zoomCell.textContent = `r${{card.dataset.row}} c${{card.dataset.column}}`;
      zoomAtlas.textContent = `x${{card.dataset.x}} y${{card.dataset.y}} ${{width}}x${{height}}`;
      zoomSource.textContent = card.dataset.source;
      zoomCopy.dataset.copy = id;

      applyZoom(activeZoom);
      zoomModal.classList.remove('hidden');
      zoomModal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      zoomClose.focus();
    }}

    function closeZoom() {{
      zoomModal.classList.add('hidden');
      zoomModal.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      if (activeCard) {{
        const opener = activeCard.querySelector('[data-zoom]');
        if (opener) opener.focus();
      }}
      activeCard = null;
    }}

    document.addEventListener('click', async (event) => {{
      const button = event.target.closest('[data-copy]');
      if (button) {{
        await copyId(button.dataset.copy, button);
        return;
      }}

      const zoomButton = event.target.closest('[data-zoom]');
      if (zoomButton) {{
        const card = zoomButton.closest('.card');
        if (card) openZoom(card);
        return;
      }}

      if (event.target.closest('[data-close-modal]')) {{
        closeZoom();
      }}
    }});

    zoomRange.addEventListener('input', () => applyZoom(zoomRange.value));
    zoomIn.addEventListener('click', () => applyZoom(activeZoom + 1));
    zoomOut.addEventListener('click', () => applyZoom(activeZoom - 1));
    zoomClose.addEventListener('click', closeZoom);
    zoomImage.addEventListener('load', () => applyZoom(activeZoom));
    document.addEventListener('keydown', (event) => {{
      if (event.key === 'Escape' && !zoomModal.classList.contains('hidden')) {{
        closeZoom();
      }}
    }});
  </script>
</body>
</html>
"""
    (output_dir / "index.html").write_text(html_text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--include-empty", action="store_true", help="Keep fully transparent cells in the catalog.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    output_dir = args.output_dir.resolve()
    if not source_root.exists():
        raise SystemExit(f"Source root not found: {source_root}")

    output_dir.mkdir(parents=True, exist_ok=True)
    entries = build_catalog(source_root, output_dir, args.include_empty)
    write_manifest(entries, source_root, output_dir)
    write_html(entries, output_dir)
    print(f"Wrote {len(entries)} numbered slices to {output_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
