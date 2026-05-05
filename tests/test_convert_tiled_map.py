#!/usr/bin/env python3
"""Assertions for the Tiled-to-Godot map converter."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from convert_tiled_map import FORMAT, convert_tiled_map  # noqa: E402


FIXTURE = PROJECT_ROOT / "tests/fixtures/tiled/sample_starship.tiled.json"


def layer_by_name(converted: dict, name: str) -> dict:
    for layer in converted["layers"]:
        if layer["name"] == name:
            return layer
    raise AssertionError(f"Layer missing: {name}")


def test_fixture_conversion() -> None:
    converted = convert_tiled_map(FIXTURE)

    assert converted["format"] == FORMAT
    assert converted["grid_size"] == 16
    assert converted["size"] == {"width": 4, "height": 4, "pixel_width": 64, "pixel_height": 64}

    floor = layer_by_name(converted, "Floor")
    assert floor["z_index"] == -20
    assert len(floor["items"]) == 2
    assert floor["items"][0]["position"] == [0.0, 0.0]
    assert floor["items"][0]["atlas"] == [0, 0, 48, 48]
    assert floor["items"][1]["position"] == [16.0, 0.0]
    assert floor["items"][1]["gid"] == 2
    assert floor["items"][1]["flip"]["horizontal"] is True
    assert floor["items"][1]["flip"]["vertical"] is False
    assert floor["items"][1]["atlas"] == [48, 0, 48, 48]

    props = layer_by_name(converted, "Props")
    assert len(props["items"]) == 3
    assert props["items"][0]["position"] == [80.0, 64.0]
    assert props["items"][0]["size"] == [48.0, 48.0]
    assert props["items"][1]["position"] == [160.0, 64.0]
    assert props["items"][1]["atlas"] == [0, 0, 96, 96]
    assert props["items"][1]["size"] == [96.0, 96.0]
    assert props["items"][2]["position"] == [37.0, 45.0]

    assert len(converted["collisions"]) == 1
    collision = converted["collisions"][0]
    assert collision["shape"] == "rectangle"
    assert collision["position"] == [16.0, 16.0]
    assert collision["size"] == [64.0, 16.0]
    assert collision["kind"] == "wall"

    markers = converted["markers"]
    assert any(marker["kind"] == "player_spawn" and marker["position"] == [24.0, 40.0] for marker in markers)
    assert sum(1 for marker in markers if marker["kind"] == "guard_patrol") == 2
    assert any(marker["kind"] == "label" and marker["text"] == "Fixture" for marker in markers)


if __name__ == "__main__":
    test_fixture_conversion()
    print("Tiled converter fixture assertions passed")
