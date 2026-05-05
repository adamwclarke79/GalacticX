# Converted Godot Maps

`BoardedStarshipSector` looks for `data/maps/starship_sector_painted.json` first. If that file is missing or invalid, it falls back to the procedural `data/starship_sector_layout.json` builder.

Convert a Tiled JSON map with:

```bash
python3 scripts/convert_tiled_map.py assets/maps/tiled/<map>.json data/maps/starship_sector_painted.json
```

The converted format is `galacticx_tiled_map_v1` with:

- `grid_size`: the Tiled map grid, expected to be `16`
- `layers`: visual atlas placements
- `collisions`: rectangle or polygon collision objects
- `markers`: gameplay points and labels

The `fixtures/` folder is converter test output and is not loaded by the game.
