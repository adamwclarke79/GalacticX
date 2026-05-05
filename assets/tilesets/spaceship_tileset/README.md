# Spaceship Tileset

Imported from `/Users/adamwclarke/Downloads/Spaceship tileset.rar`.

## Contents

- `Spaceship Tileset/tilesets/Spacestation_Inside_A1.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_A2.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_A4.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_A5.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_B.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_C.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_D.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_E.png`
- `Spaceship Tileset/characters/*.png`: object/event sheets for consoles, lights, doors, chests, reactors, medbay, navigator, ladder, switches, and decoration.
- `Spaceship Tileset/parallaxes/Universe.png`
- `Spaceship Tileset/parallaxes/Universe2.png`

## Integration Notes

- The sheets appear compatible with a 48px grid based on their dimensions.
- `scripts/world/boarded_starship_sector.gd` currently loads a few atlas regions from these PNGs as runtime visual samples.
- `scripts/build_tiled_map_setup.py` generates grouped Tiled palette tabs and atlas PNGs under `assets/maps/tiled/palettes/`, with source-sheet compatibility tilesets under `assets/maps/tiled/tilesets/`.
- Painted Tiled maps are converted with `scripts/convert_tiled_map.py` into `data/maps/starship_sector_painted.json` for Godot runtime loading.
- Keep future generated/imported Godot `TileSet` resources in this directory if the project later moves from JSON loading to native Godot resources.
