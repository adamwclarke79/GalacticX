# Tiled Map Workflow

GalacticX uses Tiled as the external map builder and converts Tiled JSON into a Godot-ready map JSON.

## Setup

Regenerate Tiled project files whenever spaceship tilesheet PNGs change:

```bash
python3 scripts/build_tiled_map_setup.py
```

Open `assets/maps/tiled/starship_sector_template.json` in Tiled. The template uses a 16x16 map grid and shows nine generated palette tabs under `assets/maps/tiled/palettes/`:

- `01 Floor`
- `02 Walls`
- `03 Wall Detail`
- `04 Doors`
- `05 Consoles`
- `06 Reactor`
- `07 Chests`
- `08 Lights`
- `09 Decor`

Each palette tab is a JSON tileset plus a matching generated atlas PNG in the same `assets/maps/tiled/palettes/` folder for a cleaner Tiled UI. Compatibility tilesets for the original source sheets remain under `assets/maps/tiled/tilesets/`.

## Authoring Rules

- Use `Floor` for grid-aligned painting.
- Use object layers for larger or freeform 32/48/96+ pixel assets.
- Use `WallsCollision` for rectangle or polygon collision objects.
- Use `Props` and `Doors` for visual object placements.
- Use `GameplayMarkers` for point or rectangle markers.
- Use `Labels` for text labels.

Marker names or `kind` properties used by the runtime:

- `player_spawn`
- `container` or `parts_container`
- `terminal` or `access_terminal`
- `door` or `blast_door_alpha`
- `guard_spawn`
- `guard_patrol`
- `objective` or `sandbox_objective`

For ordinary snapped placement, enable Tiled snap-to-grid. For freeform mode, disable snap-to-grid and place objects freely.

## Export

Save the painted map as JSON under `assets/maps/tiled/`, then convert it:

```bash
python3 scripts/convert_tiled_map.py assets/maps/tiled/<painted-map>.json data/maps/starship_sector_painted.json
```

At runtime, `scripts/world/painted_tiled_map_loader.gd` loads `data/maps/starship_sector_painted.json` first. If it is missing or invalid, the scene falls back to the procedural layout builder.

## Verification

Converter fixture test:

```bash
python3 tests/test_convert_tiled_map.py
```

Syntax check:

```bash
python3 -m py_compile scripts/build_tiled_map_setup.py scripts/convert_tiled_map.py
```
