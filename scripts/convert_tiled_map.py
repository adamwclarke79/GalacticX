#!/usr/bin/env python3
"""Convert Tiled JSON maps into the GalacticX Godot map JSON format."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORMAT = "galacticx_tiled_map_v1"
DEFAULT_GRID_SIZE = 16

FLIPPED_HORIZONTALLY_FLAG = 0x80000000
FLIPPED_VERTICALLY_FLAG = 0x40000000
FLIPPED_DIAGONALLY_FLAG = 0x20000000
ROTATED_HEXAGONAL_120_FLAG = 0x10000000
GID_MASK = ~(
    FLIPPED_HORIZONTALLY_FLAG
    | FLIPPED_VERTICALLY_FLAG
    | FLIPPED_DIAGONALLY_FLAG
    | ROTATED_HEXAGONAL_120_FLAG
)

DEFAULT_Z_INDEX = {
    "Floor": -20,
    "WallsCollision": -5,
    "Props": 2,
    "Doors": 4,
    "GameplayMarkers": 20,
    "Labels": 20,
}


class TiledConversionError(RuntimeError):
    """Raised when a Tiled map cannot be converted safely."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise TiledConversionError(f"Invalid JSON in {path}: {error}") from error


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def to_res_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return "res://" + resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def normalize_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def properties_to_dict(properties: Any) -> dict[str, Any]:
    if not isinstance(properties, list):
        return {}
    result: dict[str, Any] = {}
    for prop in properties:
        if not isinstance(prop, dict) or "name" not in prop:
            continue
        result[str(prop["name"])] = prop.get("value")
    return result


def path_from_res_or_relative(value: str, base_path: Path) -> Path:
    if value.startswith("res://"):
        return (PROJECT_ROOT / value.removeprefix("res://")).resolve()
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (base_path / path).resolve()


def atlas_from_properties(properties: dict[str, Any]) -> list[int] | None:
    keys = ("atlas_x", "atlas_y", "atlas_w", "atlas_h")
    if any(key not in properties for key in keys):
        return None
    try:
        return [int(properties[key]) for key in keys]
    except (TypeError, ValueError):
        return None


def decode_gid(raw_gid: int) -> tuple[int, dict[str, bool]]:
    return raw_gid & GID_MASK, {
        "horizontal": bool(raw_gid & FLIPPED_HORIZONTALLY_FLAG),
        "vertical": bool(raw_gid & FLIPPED_VERTICALLY_FLAG),
        "diagonal": bool(raw_gid & FLIPPED_DIAGONALLY_FLAG),
        "hex_120": bool(raw_gid & ROTATED_HEXAGONAL_120_FLAG),
    }


def load_tileset_json(first_gid: int, source_path: Path) -> dict[str, Any]:
    data = load_json(source_path)
    return build_tileset_info(first_gid, data, source_path.parent, source_path)


def load_tileset_tsx(first_gid: int, source_path: Path) -> dict[str, Any]:
    root = ET.parse(source_path).getroot()
    image = root.find("image")
    if image is None or image.get("source") is None:
        raise TiledConversionError(f"TSX tileset has no image source: {source_path}")

    data: dict[str, Any] = {
        "name": root.get("name", source_path.stem),
        "tilewidth": int(root.get("tilewidth", "0")),
        "tileheight": int(root.get("tileheight", "0")),
        "spacing": int(root.get("spacing", "0")),
        "margin": int(root.get("margin", "0")),
        "tilecount": int(root.get("tilecount", "0")),
        "columns": int(root.get("columns", "0")),
        "image": image.get("source"),
        "imagewidth": int(image.get("width", "0")),
        "imageheight": int(image.get("height", "0")),
    }
    return build_tileset_info(first_gid, data, source_path.parent, source_path)


def build_tileset_info(
    first_gid: int,
    data: dict[str, Any],
    base_path: Path,
    source_path: Path | None,
) -> dict[str, Any]:
    image_value = data.get("image", "")
    image_path = (base_path / image_value).resolve() if image_value else None
    tiles: dict[int, dict[str, Any]] = {}

    for tile in data.get("tiles", []) if isinstance(data.get("tiles", []), list) else []:
        if not isinstance(tile, dict) or "id" not in tile:
            continue
        tile_id = int(tile["id"])
        tile_properties = properties_to_dict(tile.get("properties"))
        tile_image = tile.get("image")
        tile_image_path = (base_path / tile_image).resolve() if tile_image else image_path
        godot_source = str(tile_properties.get("godot_source", ""))
        godot_source_path = path_from_res_or_relative(godot_source, base_path) if godot_source else None
        tiles[tile_id] = {
            "image_path": tile_image_path,
            "godot_source": godot_source,
            "godot_source_path": godot_source_path,
            "atlas": atlas_from_properties(tile_properties),
            "width": int(tile.get("imagewidth", tile.get("width", data.get("tilewidth", 0)))),
            "height": int(tile.get("imageheight", tile.get("height", data.get("tileheight", 0)))),
            "properties": tile_properties,
        }

    columns = int(data.get("columns", 0))
    if columns <= 0:
        tile_width = int(data.get("tilewidth", 0))
        image_width = int(data.get("imagewidth", 0))
        columns = max(1, image_width // tile_width) if tile_width > 0 else 1

    return {
        "firstgid": first_gid,
        "name": str(data.get("name", source_path.stem if source_path else "embedded_tileset")),
        "source_path": source_path,
        "base_path": base_path,
        "image_path": image_path,
        "tilewidth": int(data.get("tilewidth", 0)),
        "tileheight": int(data.get("tileheight", 0)),
        "spacing": int(data.get("spacing", 0)),
        "margin": int(data.get("margin", 0)),
        "columns": columns,
        "tilecount": int(data.get("tilecount", 0)),
        "tiles": tiles,
        "properties": properties_to_dict(data.get("properties")),
    }


def load_tilesets(map_data: dict[str, Any], map_path: Path) -> list[dict[str, Any]]:
    tilesets: list[dict[str, Any]] = []
    for entry in map_data.get("tilesets", []):
        if not isinstance(entry, dict) or "firstgid" not in entry:
            continue
        first_gid = int(entry["firstgid"])
        if "source" in entry:
            source_path = (map_path.parent / str(entry["source"])).resolve()
            if source_path.suffix.lower() == ".json":
                tilesets.append(load_tileset_json(first_gid, source_path))
            elif source_path.suffix.lower() == ".tsx":
                tilesets.append(load_tileset_tsx(first_gid, source_path))
            else:
                raise TiledConversionError(f"Unsupported external tileset format: {source_path}")
        else:
            tilesets.append(build_tileset_info(first_gid, entry, map_path.parent, None))

    tilesets.sort(key=lambda value: int(value["firstgid"]))
    return tilesets


def resolve_tile(gid: int, tilesets: list[dict[str, Any]]) -> dict[str, Any]:
    if gid <= 0:
        raise TiledConversionError("Cannot resolve empty gid 0")

    selected: dict[str, Any] | None = None
    for tileset in tilesets:
        if int(tileset["firstgid"]) <= gid:
            selected = tileset
        else:
            break

    if selected is None:
        raise TiledConversionError(f"No tileset found for gid {gid}")

    local_id = gid - int(selected["firstgid"])
    tile_width = int(selected["tilewidth"])
    tile_height = int(selected["tileheight"])
    per_tile = selected["tiles"].get(local_id)
    if per_tile is not None and per_tile.get("image_path") is not None:
        source_path = per_tile.get("godot_source_path") or per_tile["image_path"]
        source = per_tile.get("godot_source") or to_res_path(source_path)
        atlas = per_tile.get("atlas") or [0, 0, int(per_tile["width"]), int(per_tile["height"])]
        return {
            "tileset": selected["name"],
            "local_id": local_id,
            "source": source,
            "source_path": normalize_path(source_path),
            "atlas": atlas,
            "size": [int(atlas[2]), int(atlas[3])],
        }

    image_path = selected.get("image_path")
    if image_path is None:
        raise TiledConversionError(f"Tileset has no image for gid {gid}: {selected['name']}")

    columns = max(1, int(selected["columns"]))
    spacing = int(selected["spacing"])
    margin = int(selected["margin"])
    column = local_id % columns
    row = local_id // columns
    atlas_x = margin + column * (tile_width + spacing)
    atlas_y = margin + row * (tile_height + spacing)
    return {
        "tileset": selected["name"],
        "local_id": local_id,
        "source": to_res_path(image_path),
        "source_path": normalize_path(image_path),
        "atlas": [atlas_x, atlas_y, tile_width, tile_height],
        "size": [tile_width, tile_height],
    }


def layer_z_index(layer: dict[str, Any]) -> int:
    properties = properties_to_dict(layer.get("properties"))
    value = properties.get("z_index", DEFAULT_Z_INDEX.get(str(layer.get("name", "")), 0))
    try:
        return int(value)
    except (TypeError, ValueError):
        return DEFAULT_Z_INDEX.get(str(layer.get("name", "")), 0)


def make_layer_output(layer: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(layer.get("name", "")),
        "type": str(layer.get("type", "")),
        "z_index": layer_z_index(layer),
        "opacity": float(layer.get("opacity", 1.0)),
        "visible": bool(layer.get("visible", True)),
        "properties": properties_to_dict(layer.get("properties")),
        "items": [],
    }


def item_from_gid(
    *,
    raw_gid: int,
    item_id: str,
    layer: dict[str, Any],
    tilesets: list[dict[str, Any]],
    position: list[float],
    size_override: list[float] | None = None,
    rotation: float = 0.0,
    opacity: float | None = None,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_gid, flip = decode_gid(raw_gid)
    tile = resolve_tile(clean_gid, tilesets)
    source_size = tile["size"]
    size = size_override if size_override is not None else [float(source_size[0]), float(source_size[1])]

    return {
        "id": item_id,
        "gid": clean_gid,
        "raw_gid": raw_gid,
        "tileset": tile["tileset"],
        "local_id": tile["local_id"],
        "source": tile["source"],
        "source_path": tile["source_path"],
        "atlas": tile["atlas"],
        "position": [round(float(position[0]), 4), round(float(position[1]), 4)],
        "size": [round(float(size[0]), 4), round(float(size[1]), 4)],
        "rotation": round(float(rotation), 4),
        "flip": flip,
        "opacity": float(layer.get("opacity", 1.0)) if opacity is None else float(opacity),
        "properties": properties or {},
    }


def convert_tile_layer(
    layer: dict[str, Any],
    map_data: dict[str, Any],
    tilesets: list[dict[str, Any]],
    output_layer: dict[str, Any],
) -> None:
    layer_width = int(layer.get("width", map_data.get("width", 0)))
    tile_width = float(map_data.get("tilewidth", DEFAULT_GRID_SIZE))
    tile_height = float(map_data.get("tileheight", DEFAULT_GRID_SIZE))
    offset_x = float(layer.get("offsetx", 0.0))
    offset_y = float(layer.get("offsety", 0.0))

    def append_tile(raw_gid: int, x: int, y: int) -> None:
        if raw_gid == 0:
            return
        output_layer["items"].append(
            item_from_gid(
                raw_gid=raw_gid,
                item_id=f"{layer.get('name', 'Layer')}_{x}_{y}",
                layer=layer,
                tilesets=tilesets,
                position=[x * tile_width + offset_x, y * tile_height + offset_y],
            )
        )

    if isinstance(layer.get("chunks"), list):
        for chunk in layer["chunks"]:
            chunk_width = int(chunk.get("width", 0))
            chunk_x = int(chunk.get("x", 0))
            chunk_y = int(chunk.get("y", 0))
            for index, raw_gid in enumerate(chunk.get("data", [])):
                append_tile(int(raw_gid), chunk_x + index % chunk_width, chunk_y + index // chunk_width)
        return

    for index, raw_gid in enumerate(layer.get("data", [])):
        append_tile(int(raw_gid), index % layer_width, index // layer_width)


def object_kind(obj: dict[str, Any], properties: dict[str, Any]) -> str:
    for key in ("kind", "marker", "role"):
        value = properties.get(key)
        if value not in (None, ""):
            return str(value)
    for key in ("class", "type", "name"):
        value = obj.get(key)
        if value not in (None, ""):
            return str(value)
    return "marker"


def is_collision_layer(layer: dict[str, Any]) -> bool:
    name = str(layer.get("name", "")).lower()
    properties = properties_to_dict(layer.get("properties"))
    return "collision" in name or bool(properties.get("collision", False))


def is_marker_layer(layer: dict[str, Any]) -> bool:
    name = str(layer.get("name", "")).lower()
    properties = properties_to_dict(layer.get("properties"))
    return "marker" in name or name == "gameplaymarkers" or bool(properties.get("markers", False))


def is_label_layer(layer: dict[str, Any]) -> bool:
    return str(layer.get("name", "")).lower() == "labels"


def convert_collision(
    obj: dict[str, Any],
    layer: dict[str, Any],
    properties: dict[str, Any],
    offset_x: float,
    offset_y: float,
) -> dict[str, Any]:
    x = float(obj.get("x", 0.0)) + offset_x
    y = float(obj.get("y", 0.0)) + offset_y
    width = float(obj.get("width", 0.0))
    height = float(obj.get("height", 0.0))
    collision = {
        "id": str(obj.get("id", "")),
        "name": str(obj.get("name", "")),
        "kind": object_kind(obj, properties),
        "layer": str(layer.get("name", "")),
        "position": [round(x, 4), round(y, 4)],
        "size": [round(width, 4), round(height, 4)],
        "rotation": round(float(obj.get("rotation", 0.0)), 4),
        "properties": properties,
    }
    if isinstance(obj.get("polygon"), list):
        collision["shape"] = "polygon"
        collision["points"] = [
            [round(float(point.get("x", 0.0)), 4), round(float(point.get("y", 0.0)), 4)]
            for point in obj["polygon"]
        ]
    elif isinstance(obj.get("polyline"), list):
        collision["shape"] = "polyline"
        collision["points"] = [
            [round(float(point.get("x", 0.0)), 4), round(float(point.get("y", 0.0)), 4)]
            for point in obj["polyline"]
        ]
    else:
        collision["shape"] = "rectangle"
    return collision


def convert_marker(
    obj: dict[str, Any],
    layer: dict[str, Any],
    properties: dict[str, Any],
    offset_x: float,
    offset_y: float,
) -> dict[str, Any]:
    x = float(obj.get("x", 0.0)) + offset_x
    y = float(obj.get("y", 0.0)) + offset_y
    text_data = obj.get("text", {}) if isinstance(obj.get("text"), dict) else {}
    kind = "label" if text_data or is_label_layer(layer) else object_kind(obj, properties)
    marker = {
        "id": str(obj.get("id", "")),
        "name": str(obj.get("name", "")),
        "kind": kind,
        "layer": str(layer.get("name", "")),
        "position": [round(x, 4), round(y, 4)],
        "size": [round(float(obj.get("width", 0.0)), 4), round(float(obj.get("height", 0.0)), 4)],
        "rotation": round(float(obj.get("rotation", 0.0)), 4),
        "point": bool(obj.get("point", False)),
        "properties": properties,
    }
    if text_data:
        marker["text"] = str(text_data.get("text", ""))
    return marker


def convert_object_layer(
    layer: dict[str, Any],
    tilesets: list[dict[str, Any]],
    output_layer: dict[str, Any],
    collisions: list[dict[str, Any]],
    markers: list[dict[str, Any]],
) -> None:
    offset_x = float(layer.get("offsetx", 0.0))
    offset_y = float(layer.get("offsety", 0.0))

    for obj in layer.get("objects", []):
        if not isinstance(obj, dict):
            continue
        properties = properties_to_dict(obj.get("properties"))
        if int(obj.get("gid", 0)) > 0:
            raw_gid = int(obj["gid"])
            clean_gid, _flip = decode_gid(raw_gid)
            tile = resolve_tile(clean_gid, tilesets)
            width = float(obj.get("width", tile["size"][0]))
            height = float(obj.get("height", tile["size"][1]))
            x = float(obj.get("x", 0.0)) + offset_x
            y = float(obj.get("y", 0.0)) + offset_y - height
            output_layer["items"].append(
                item_from_gid(
                    raw_gid=raw_gid,
                    item_id=f"{layer.get('name', 'Object')}_{obj.get('id', len(output_layer['items']))}",
                    layer=layer,
                    tilesets=tilesets,
                    position=[x, y],
                    size_override=[width, height],
                    rotation=float(obj.get("rotation", 0.0)),
                    opacity=float(obj.get("opacity", layer.get("opacity", 1.0))),
                    properties=properties,
                )
            )
            if is_marker_layer(layer) and properties.get("marker"):
                markers.append(convert_marker(obj, layer, properties, offset_x, offset_y))
            continue

        if is_label_layer(layer) or isinstance(obj.get("text"), dict) or is_marker_layer(layer):
            markers.append(convert_marker(obj, layer, properties, offset_x, offset_y))
        elif is_collision_layer(layer):
            collisions.append(convert_collision(obj, layer, properties, offset_x, offset_y))
        else:
            markers.append(convert_marker(obj, layer, properties, offset_x, offset_y))


def convert_tiled_map(map_path: Path) -> dict[str, Any]:
    map_path = map_path.resolve()
    map_data = load_json(map_path)
    if map_data.get("type") != "map":
        raise TiledConversionError(f"Expected a Tiled map JSON file: {map_path}")

    tilesets = load_tilesets(map_data, map_path)
    layers: list[dict[str, Any]] = []
    collisions: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []

    for layer in map_data.get("layers", []):
        if not isinstance(layer, dict):
            continue
        output_layer = make_layer_output(layer)
        layer_type = layer.get("type")
        if layer_type == "tilelayer":
            convert_tile_layer(layer, map_data, tilesets, output_layer)
        elif layer_type == "objectgroup":
            convert_object_layer(layer, tilesets, output_layer, collisions, markers)
        else:
            output_layer["unsupported_type"] = layer_type
        layers.append(output_layer)

    tile_width = int(map_data.get("tilewidth", DEFAULT_GRID_SIZE))
    tile_height = int(map_data.get("tileheight", tile_width))
    if tile_width != tile_height:
        raise TiledConversionError(f"GalacticX expects square map grid cells, got {tile_width}x{tile_height}")

    return {
        "format": FORMAT,
        "source_map": normalize_path(map_path),
        "grid_size": tile_width,
        "size": {
            "width": int(map_data.get("width", 0)),
            "height": int(map_data.get("height", 0)),
            "pixel_width": int(map_data.get("width", 0)) * tile_width,
            "pixel_height": int(map_data.get("height", 0)) * tile_height,
        },
        "layers": layers,
        "collisions": collisions,
        "markers": markers,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Tiled JSON map to convert")
    parser.add_argument("output", type=Path, help="Godot-ready JSON output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        converted = convert_tiled_map(args.input)
        write_json(args.output, converted)
    except TiledConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
