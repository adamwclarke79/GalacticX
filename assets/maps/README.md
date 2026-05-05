# GalacticX Maps

Place prebuilt starship map files and layout references here.

Expected convention:

- `assets/maps/<map_name>/`
- Include source map data, exported Godot resources, and any reference PNGs needed by the PixelLab asset workflow.
- Active Godot scenes should map these into layer nodes named `Floor`, `WallsCollision`, `Props`, `Doors`, `GameplayMarkers`, and optional `Labels`.

## Tiled workflow

- `assets/maps/tiled/galacticx.tiled-project`: Tiled project file.
- `assets/maps/tiled/starship_sector_template.json`: 16x16-grid starter map.
- `assets/maps/tiled/palettes/*.json`: nine generated category palette tabs for the Tiled UI.
- `assets/maps/tiled/palettes/*.png`: generated atlas images used by the palette tabs.
- `assets/maps/tiled/tilesets/*.json`: compatibility tilesets for the original imported spaceship PNG sheets.

Regenerate the Tiled setup after adding or replacing spaceship tilesheets:

```bash
python3 scripts/build_tiled_map_setup.py
```

Save painted Tiled maps as JSON under `assets/maps/tiled/`, then convert them for Godot:

```bash
python3 scripts/convert_tiled_map.py assets/maps/tiled/<map>.json data/maps/starship_sector_painted.json
```
