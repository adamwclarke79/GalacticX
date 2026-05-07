#!/usr/bin/env python3
"""Generate Tiled project files for the GalacticX spaceship tileset."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "assets/tilesets/spaceship_tileset/Spaceship Tileset"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "assets/maps/tiled"
DEFAULT_CATALOG_MANIFEST = PROJECT_ROOT / "docs/tileset_catalog/manifest.json"
DEFAULT_CATALOG_ROOT = PROJECT_ROOT / "docs/tileset_catalog"
STARWARS_TILE_ROOT = PROJECT_ROOT / "assets/tilesets/starwars"
DEFAULT_MAP_WIDTH = 80
DEFAULT_MAP_HEIGHT = 45
MAP_TILE_SIZE = 16
SMALL_PALETTE_COLUMNS = 16
MEDIUM_PALETTE_COLUMNS = 10
LARGE_PALETTE_COLUMNS = 8
MAX_PALETTE_ATLAS_WIDTH = 2048
MAX_PALETTE_ATLAS_HEIGHT = 2048
LAYER_NAMES = ["Floor", "WallsCollision", "Props", "Doors", "GameplayMarkers", "Labels"]
CATEGORY_LABELS = {
    "01_floor_tiles": "01 Floor",
    "02_wall_tiles": "02 Walls",
    "02_starwars_wall_tiles_48": "02 Star Wars Walls 48",
    "03_wall_detail_tiles": "03 Wall Detail",
    "04_doors_gates": "04 Doors",
    "04_starwars_doors_48": "04 Star Wars Doors 48",
    "05_consoles_computers": "05 Consoles",
    "06_reactors_medbay": "06 Reactor",
    "07_chests_storage": "07 Chests",
    "08_lights": "08 Lights",
    "09_decorations_switches": "09 Decor",
}
CUSTOM_STARWARS_WALL_TILES = [
    ("SW_WALL_BUTTONS", "wall_tile_buttons_48x96.png"),
    ("SW_WALL_PLAIN", "wall_tile_plain_48x96.png"),
    ("SW_WALL_V2_WHITE_OUTLINE", "wall_tile_v2_white_outline_48x96.png"),
    ("SW_WALL_V2_ORANGE_ALT", "wall_tile_v2_orange_alt_48x96.png"),
]
CUSTOM_STARWARS_TILE_DIRECTORIES = [
    (
        "SW_WALL_PANEL_96",
        "SW_DOOR_PANEL_96",
        "StarWars_Wall_Panels_96",
        "StarWars_Door_Panels_96",
        "wall_panels_bright_96",
        {(0, 3), (1, 0)},
        "starwars_wall",
        "starwars_door",
    ),
    (
        "SW_WALL_PANEL_48",
        "SW_DOOR_PANEL_48",
        "StarWars_Wall_Panels_48",
        "StarWars_Door_Panels_48",
        "wall_panels_48",
        {(1, 0), (1, 1)},
        "starwars_wall_48",
        "starwars_door_48",
    ),
]


@dataclass(frozen=True)
class PaletteTile:
    catalog_id: str
    category: str
    sheet: str
    source_image: Path
    preview_image: Path
    row: int
    column: int
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class TiledTileset:
    slug: str
    name: str
    output_path: Path
    atlas_path: Path
    tiles: list[PaletteTile]

    @property
    def tile_width(self) -> int:
        return max((tile.width for tile in self.tiles), default=MAP_TILE_SIZE)

    @property
    def tile_height(self) -> int:
        return max((tile.height for tile in self.tiles), default=MAP_TILE_SIZE)

    @property
    def tile_count(self) -> int:
        return len(self.tiles)

    @property
    def columns(self) -> int:
        if not self.tiles:
            return 1
        max_columns = max(1, MAX_PALETTE_ATLAS_WIDTH // self.tile_width)
        max_rows = max(1, MAX_PALETTE_ATLAS_HEIGHT // self.tile_height)
        if self.tile_width <= 48:
            base_columns = SMALL_PALETTE_COLUMNS
        elif self.tile_width <= 96:
            base_columns = MEDIUM_PALETTE_COLUMNS
        else:
            base_columns = LARGE_PALETTE_COLUMNS

        height_limited_columns = (self.tile_count + max_rows - 1) // max_rows
        return min(max(base_columns, height_limited_columns), max_columns, self.tile_count)

    @property
    def rows(self) -> int:
        return max(1, (self.tile_count + self.columns - 1) // self.columns)

    @property
    def image_width(self) -> int:
        return self.columns * self.tile_width

    @property
    def image_height(self) -> int:
        return self.rows * self.tile_height


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return cleaned or "tileset"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_palette_atlas(tileset: TiledTileset) -> None:
    tileset.atlas_path.parent.mkdir(parents=True, exist_ok=True)
    atlas = Image.new("RGBA", (tileset.image_width, tileset.image_height), (0, 0, 0, 0))

    for index, tile in enumerate(tileset.tiles):
        column = index % tileset.columns
        row = index // tileset.columns
        x = column * tileset.tile_width
        y = row * tileset.tile_height + (tileset.tile_height - tile.height)
        with Image.open(tile.preview_image) as source:
            source_rgba = source.convert("RGBA")
            atlas.paste(source_rgba, (x, y), source_rgba)

    atlas.save(tileset.atlas_path)


def write_tileset(tileset: TiledTileset) -> None:
    write_palette_atlas(tileset)
    payload = {
        "type": "tileset",
        "version": "1.10",
        "tiledversion": "1.12.1",
        "name": tileset.name,
        "objectalignment": "bottomleft",
        "tilewidth": tileset.tile_width,
        "tileheight": tileset.tile_height,
        "spacing": 0,
        "margin": 0,
        "columns": tileset.columns,
        "tilecount": tileset.tile_count,
        "image": Path(os.path.relpath(tileset.atlas_path, tileset.output_path.parent)).as_posix(),
        "imagewidth": tileset.image_width,
        "imageheight": tileset.image_height,
        "tiles": [tile_payload(index, tile) for index, tile in enumerate(tileset.tiles)],
    }
    write_json(tileset.output_path, payload)


def source_tile_size_for(path: Path, image_width: int, image_height: int) -> tuple[int, int]:
    if path.parent.name == "tilesets":
        return 48, 48
    if path.parent.name == "characters":
        if path.name.startswith("!$"):
            return image_width // 3, image_height // 4
        if path.name.startswith("!"):
            return image_width // 12, image_height // 8
    return 48, 48


def iter_source_images(source_root: Path) -> list[Path]:
    paths: list[Path] = []
    paths.extend(sorted((source_root / "tilesets").glob("*.png")))
    paths.extend(sorted((source_root / "characters").glob("*.png")))
    return paths


def write_compat_source_tilesets(source_root: Path, output_root: Path) -> None:
    compat_dir = output_root / "tilesets"
    compat_dir.mkdir(parents=True, exist_ok=True)
    for stale_palette in compat_dir.glob("[0-9][0-9]_*.json"):
        stale_palette.unlink()
    for source_image in iter_source_images(source_root):
        with Image.open(source_image) as image:
            image_width, image_height = image.size
        tile_width, tile_height = source_tile_size_for(source_image, image_width, image_height)
        columns = max(1, image_width // tile_width)
        rows = max(1, image_height // tile_height)
        output_path = compat_dir / f"{slugify(source_image.stem)}.json"
        payload = {
            "type": "tileset",
            "version": "1.10",
            "tiledversion": "1.12.1",
            "name": source_image.stem,
            "tilewidth": tile_width,
            "tileheight": tile_height,
            "spacing": 0,
            "margin": 0,
            "columns": columns,
            "tilecount": columns * rows,
            "image": Path(os.path.relpath(source_image, output_path.parent)).as_posix(),
            "imagewidth": image_width,
            "imageheight": image_height,
            "properties": [
                {
                    "name": "godot_source",
                    "type": "string",
                    "value": "res://" + source_image.relative_to(PROJECT_ROOT).as_posix(),
                }
            ],
        }
        write_json(output_path, payload)


def tile_payload(index: int, tile: PaletteTile) -> dict:
    return {
        "id": index,
        "properties": [
            {"name": "catalog_id", "type": "string", "value": tile.catalog_id},
            {"name": "category", "type": "string", "value": tile.category},
            {"name": "sheet", "type": "string", "value": tile.sheet},
            {"name": "row", "type": "int", "value": tile.row},
            {"name": "column", "type": "int", "value": tile.column},
            {"name": "godot_source", "type": "string", "value": "res://" + tile.source_image.relative_to(PROJECT_ROOT).as_posix()},
            {"name": "atlas_x", "type": "int", "value": tile.x},
            {"name": "atlas_y", "type": "int", "value": tile.y},
            {"name": "atlas_w", "type": "int", "value": tile.width},
            {"name": "atlas_h", "type": "int", "value": tile.height},
        ],
    }


def build_project(output_root: Path) -> None:
    payload = {
        "automappingRulesFile": "",
        "commands": [],
        "extensionsPath": "extensions",
        "folders": ["."],
        "propertyTypes": [],
    }
    write_json(output_root / "galacticx.tiled-project", payload)


def layer_payload(layer_id: int, name: str, width: int, height: int) -> dict:
    if name == "Floor":
        return {
            "id": layer_id,
            "name": name,
            "type": "tilelayer",
            "x": 0,
            "y": 0,
            "width": width,
            "height": height,
            "opacity": 1,
            "visible": True,
            "data": [0] * (width * height),
        }
    return {
        "id": layer_id,
        "name": name,
        "type": "objectgroup",
        "draworder": "topdown",
        "opacity": 1,
        "visible": True,
        "objects": [],
    }


def build_template(output_root: Path, tilesets: list[TiledTileset], width: int, height: int) -> None:
    first_gid = 1
    tiled_tilesets: list[dict] = []
    for tileset in tilesets:
        tiled_tilesets.append(
            {
                "firstgid": first_gid,
                "source": tileset.output_path.relative_to(output_root).as_posix(),
            }
        )
        first_gid += tileset.tile_count

    payload = {
        "type": "map",
        "version": "1.10",
        "tiledversion": "1.12.1",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "width": width,
        "height": height,
        "tilewidth": MAP_TILE_SIZE,
        "tileheight": MAP_TILE_SIZE,
        "infinite": False,
        "nextlayerid": len(LAYER_NAMES) + 1,
        "nextobjectid": 1,
        "tilesets": tiled_tilesets,
        "layers": [layer_payload(index + 1, name, width, height) for index, name in enumerate(LAYER_NAMES)],
        "properties": [
            {"name": "godot_grid_size", "type": "int", "value": MAP_TILE_SIZE},
            {"name": "godot_export", "type": "string", "value": "data/maps/starship_sector_painted.json"},
        ],
    }
    write_json(output_root / "starship_sector_template.json", payload)


def load_palette_tiles(manifest_path: Path, catalog_root: Path, source_root: Path) -> list[PaletteTile]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tiles: list[PaletteTile] = []
    for entry in manifest.get("entries", []):
        source_image = source_root / entry["source"]
        preview_image = catalog_root / entry["image"]
        if not source_image.exists() or not preview_image.exists():
            continue
        tiles.append(
            PaletteTile(
                catalog_id=str(entry["id"]),
                category=str(entry["category"]),
                sheet=str(entry["sheet"]),
                source_image=source_image,
                preview_image=preview_image,
                row=int(entry["row"]),
                column=int(entry["column"]),
                x=int(entry["x"]),
                y=int(entry["y"]),
                width=int(entry["width"]),
                height=int(entry["height"]),
                )
            )
    for column, (catalog_id, filename) in enumerate(CUSTOM_STARWARS_WALL_TILES):
        source_image = STARWARS_TILE_ROOT / filename
        if not source_image.exists():
            continue
        with Image.open(source_image) as image:
            width, height = image.size
        tiles.append(
            PaletteTile(
                catalog_id=catalog_id,
                category="starwars_wall",
                sheet="StarWars_Walls",
                source_image=source_image,
                preview_image=source_image,
                row=0,
                column=column,
                x=0,
                y=0,
                width=width,
                height=height,
            )
        )
    for (
        wall_prefix,
        door_prefix,
        wall_sheet,
        door_sheet,
        directory,
        door_cells,
        wall_category,
        door_category,
    ) in CUSTOM_STARWARS_TILE_DIRECTORIES:
        source_dir = STARWARS_TILE_ROOT / directory
        if not source_dir.exists():
            continue
        for index, source_image in enumerate(sorted(source_dir.glob("*.png"))):
            match = re.search(r"_r(\d+)_c(\d+)", source_image.stem)
            row = int(match.group(1)) if match else 0
            column = int(match.group(2)) if match else index
            is_door_panel = (row, column) in door_cells
            catalog_id_prefix = door_prefix if is_door_panel else wall_prefix
            catalog_id = f"{catalog_id_prefix}_R{row:02d}_C{column:02d}"
            with Image.open(source_image) as image:
                width, height = image.size
            tiles.append(
                PaletteTile(
                    catalog_id=catalog_id,
                    category=door_category if is_door_panel else wall_category,
                    sheet=door_sheet if is_door_panel else wall_sheet,
                    source_image=source_image,
                    preview_image=source_image,
                    row=row,
                    column=column,
                    x=0,
                    y=0,
                    width=width,
                    height=height,
                )
            )
    return tiles


def category_for(tile: PaletteTile) -> str:
    if tile.category == "starwars_wall":
        return "02_wall_tiles"
    if tile.category == "starwars_door":
        return "04_doors_gates"
    if tile.category == "starwars_wall_48":
        return "02_starwars_wall_tiles_48"
    if tile.category == "starwars_door_48":
        return "04_starwars_doors_48"
    sheet = tile.sheet.lower()
    if tile.source_image.parent.name == "tilesets":
        if sheet.endswith("_a4"):
            return "02_wall_tiles"
        if sheet.endswith("_b") or sheet.endswith("_c") or sheet.endswith("_d") or sheet.endswith("_e"):
            return "03_wall_detail_tiles"
        return "01_floor_tiles"
    if "door" in sheet or "gate" in sheet or "elevator" in sheet:
        return "04_doors_gates"
    if "console" in sheet or "computer" in sheet or "cpu" in sheet:
        return "05_consoles_computers"
    if "reactor" in sheet or "medbay" in sheet or "navigator" in sheet:
        return "06_reactors_medbay"
    if "chest" in sheet:
        return "07_chests_storage"
    if "light" in sheet:
        return "08_lights"
    return "09_decorations_switches"


def max_chunk_size_for(tiles: list[PaletteTile]) -> int:
    tile_width = max((tile.width for tile in tiles), default=MAP_TILE_SIZE)
    tile_height = max((tile.height for tile in tiles), default=MAP_TILE_SIZE)
    max_columns = max(1, MAX_PALETTE_ATLAS_WIDTH // tile_width)
    max_rows = max(1, MAX_PALETTE_ATLAS_HEIGHT // tile_height)
    return max(1, max_columns * max_rows)


def chunk_tiles(tiles: list[PaletteTile]) -> list[list[PaletteTile]]:
    chunk_size = max_chunk_size_for(tiles)
    if len(tiles) <= chunk_size:
        return [tiles]
    return [tiles[index : index + chunk_size] for index in range(0, len(tiles), chunk_size)]


def build_palette_tilesets(tiles: list[PaletteTile], output_root: Path) -> list[TiledTileset]:
    grouped: dict[str, list[PaletteTile]] = {slug: [] for slug in CATEGORY_LABELS}
    for tile in tiles:
        grouped.setdefault(category_for(tile), []).append(tile)

    tilesets: list[TiledTileset] = []
    for slug, label in CATEGORY_LABELS.items():
        category_tiles = grouped.get(slug, [])
        if not category_tiles:
            continue
        chunks = chunk_tiles(category_tiles)
        for index, chunk in enumerate(chunks, start=1):
            chunk_slug = slug if len(chunks) == 1 else f"{slug}_{index:02d}"
            chunk_label = label if len(chunks) == 1 else f"{label} {index}"
            tilesets.append(
                TiledTileset(
                    slug=chunk_slug,
                    name=chunk_label,
                    output_path=output_root / "palettes" / f"{chunk_slug}.json",
                    atlas_path=output_root / "palettes" / f"{chunk_slug}.png",
                    tiles=chunk,
                )
            )
    return tilesets


def reset_generated_palettes(output_root: Path) -> None:
    palette_dir = output_root / "palettes"
    if palette_dir.exists():
        shutil.rmtree(palette_dir)
    palette_dir.mkdir(parents=True, exist_ok=True)

    old_atlas_dir = output_root / "palette_atlases"
    if old_atlas_dir.exists():
        shutil.rmtree(old_atlas_dir)


def build_setup(
    source_root: Path,
    output_root: Path,
    catalog_manifest: Path,
    catalog_root: Path,
    width: int,
    height: int,
) -> list[TiledTileset]:
    if not catalog_manifest.exists():
        raise FileNotFoundError(f"Tileset catalog manifest missing: {catalog_manifest}")
    reset_generated_palettes(output_root)
    tiles = load_palette_tiles(catalog_manifest, catalog_root, source_root)
    tilesets = build_palette_tilesets(tiles, output_root)
    for tileset in tilesets:
        write_tileset(tileset)
    write_compat_source_tilesets(source_root, output_root)
    build_project(output_root)
    build_template(output_root, tilesets, width, height)
    return tilesets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--catalog-manifest", type=Path, default=DEFAULT_CATALOG_MANIFEST)
    parser.add_argument("--catalog-root", type=Path, default=DEFAULT_CATALOG_ROOT)
    parser.add_argument("--width", type=int, default=DEFAULT_MAP_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_MAP_HEIGHT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tilesets = build_setup(
        args.source_root.resolve(),
        args.output_root.resolve(),
        args.catalog_manifest.resolve(),
        args.catalog_root.resolve(),
        args.width,
        args.height,
    )
    print(f"Wrote {len(tilesets)} categorized Tiled palette tabs to {args.output_root}")
    print(f"Open {args.output_root / 'starship_sector_template.json'} in Tiled to start painting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
