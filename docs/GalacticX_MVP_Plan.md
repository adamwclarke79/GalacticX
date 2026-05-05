# GalacticX MVP Plan

## Current Build

GalacticX is now structured as a low top-down Godot 4 starship boarding sandbox. The current goal is to prove reusable systems, not a fixed mission loop.

Implemented systems:

- 8-direction `CharacterBody2D` player movement.
- Variable-frame directional animation loading.
- Static and moving NPC support.
- Runtime-generated starship sector using the imported spaceship tileset, JSON layout data, and tilemap-ready layer shells.
- Container, terminal, locked door, and objective marker interactables.
- Inventory, crafting, suspicion, time, HUD, and save/load systems.
- PixelLab asset workflow documented as the source for future characters, animations, tilesets, props, and map visual assets.

## Architecture

`scenes/Main.tscn` is the active entry point. It owns:

- `GameState`: inventory, crafting, time, suspicion, status, and alert signals.
- `SaveSystem`: JSON persistence at `user://galacticx_save.json`.
- `BoardedStarshipSector`: current sandbox level.
- `HUD`: inventory, time, suspicion, prompt, and debug status display.

`BoardedStarshipSector` creates `TileMapLayers` shells named `Floor`, `WallsCollision`, `Props`, `Doors`, `GameplayMarkers`, and `Labels`. It first tries to load converted Tiled JSON from `data/maps/starship_sector_painted.json`; if unavailable, it asks `StarshipLayoutBuilder` to populate generated child nodes under those layers. The generated fallback map uses:

- `data/starship_sector_layout.json`: long corridor, side rooms, doors, props, and labels.
- `data/spaceship_tile_catalog.json`: atlas sheet paths and regions from the imported spaceship tileset.
- `scripts/world/painted_tiled_map_loader.gd`: runtime loader for converted Tiled visual items, collisions, labels, and gameplay markers.
- `scripts/world/starship_layout_builder.gd`: walkable-grid layout, flat gunmetal floor rendering, white wall tile rendering, door/prop sprite placement, and collision generation.
- `scripts/world/tile_catalog.gd`: safe loading for imported atlas regions.

The spaceship tileset archive has been extracted to `assets/tilesets/spaceship_tileset/`. Collision is currently generated from the JSON walkable grid with `StaticBody2D` cells. A painted Godot `TileSet` can replace or refine this later without changing the gameplay systems.

## PixelLab Asset Source

Use `.claude/agents/pixellab-api-asset-agent.md` for PixelLab API work.

Source files:

- `scripts/pixellab_api.py`
- `docs/pixellab-api.md`

Stable output directories:

- `assets/sprites/characters/<character>/`
- `assets/sprites/characters/<character>/api_generated/<task>/`
- `assets/tilesets/<tileset_name>/`
- `assets/maps/<map_name>/`
- `assets/sprites/props/`
- `assets/sprites/effects/`

Run `python3 scripts/pixellab_api.py balance` before paid generation when `PIXELLAB_API_TOKEN` is available.

## Animation Convention

Each actor should support:

- `north`
- `south`
- `east`
- `west`
- `north-east`
- `north-west`
- `south-east`
- `south-west`

Animation frames can vary from 2 to 8 frames. The loader discovers and loops available `frame_*.png` files. Missing animated frames fall back to rotations, then root directional sprites, then a colored placeholder.

## Tilemap Plan

Prebuilt tile maps should become the primary editor-authored layout source. Until a Godot-painted map exists, the current runtime layout is generated from `data/starship_sector_layout.json` so the prototype already has a long corridor with small and large rooms off the main corridor.

Current imported source:

- `assets/tilesets/spaceship_tileset/Spaceship Tileset/tilesets/Spacestation_Inside_A1.png`
- `assets/tilesets/spaceship_tileset/Spaceship Tileset/tilesets/Spacestation_Inside_A2.png`
- `assets/tilesets/spaceship_tileset/Spaceship Tileset/tilesets/Spacestation_Inside_A4.png`
- `assets/tilesets/spaceship_tileset/Spaceship Tileset/tilesets/Spacestation_Inside_A5.png`
- `assets/tilesets/spaceship_tileset/Spaceship Tileset/tilesets/Spacestation_Inside_B.png`
- `assets/tilesets/spaceship_tileset/Spaceship Tileset/tilesets/Spacestation_Inside_C.png`
- `assets/tilesets/spaceship_tileset/Spaceship Tileset/tilesets/Spacestation_Inside_D.png`
- `assets/tilesets/spaceship_tileset/Spaceship Tileset/tilesets/Spacestation_Inside_E.png`

Expected layout:

- breach entry
- corridor choke point
- side rooms
- locked bulkheads
- terminals
- cover props
- droid escape area
- Leia marker
- Vader marker

Current runtime layout:

- breach entry at the left end of the main corridor
- underlying two-cell-high long corridor across the sector, with the visible floor strip scaled to 40% of that width so it reads 60% narrower
- flat single-color gunmetal floor for the narrowed corridor strip and rooms
- 96x96 wall visuals from `assets/tilesets/starwars/wall_tile_96.png`, a strict resize of the full supplied reference image, while gameplay collision remains on the 48px grid
- every second north-face corridor wall cell has a hanging `GX0861` button/control overlay from `Spacestation_Inside_C.png` at atlas region `x=480 y=432 48x48`
- door visuals use the `!Spaceship_door.png` frame set `GX2036` open, `GX2048` partially open, `GX2060` partially open, and `GX2072` closed, rendered through a white-door shader; the locked door plays the partial frames when opening
- repeated open bulkheads every five corridor tiles, with shiny white blast-door panels retracted into the walls
- small north storage room with the parts container
- small south terminal room with the access terminal
- larger north reactor room with medbay/reactor props
- larger south droid escape bay
- command room and locked command bulkhead

Expected Godot world layering:

- `Floor`
- `WallsCollision`
- `Props`
- `Doors`
- `GameplayMarkers`

Collision should come from the Godot `TileSet` when available, with manual `StaticBody2D` collision only for missing collision areas.

## Controls

- Move: `WASD` or arrows
- Interact: `E`
- Inventory debug: `I` or tab
- Craft `hack_tool`: `C`
- Save: `F5`
- Load: `F9`

## Save Schema

Save file: `user://galacticx_save.json`.

Saved state:

- player position and facing
- inventory
- suspicion
- current time
- container state
- terminal state
- door state
- guard position, facing, and patrol index

## Next Build Steps

- Create a Godot `TileSet` resource from `assets/tilesets/spaceship_tileset/`.
- Add wall/bulkhead collision to the Godot `TileSet`.
- Paint the first production starship map in Tiled from `assets/maps/tiled/starship_sector_template.json`, then convert it to `data/maps/starship_sector_painted.json`.
- Use PixelLab only for supplemental missing tiles, props, and map reference art after checking balance and choosing an explicit output directory.
- Add Leia and Vader sprites when available.
- Expand NPC behavior from static/patrol markers into sandbox behaviors.
- Add wall-aware line-of-sight once tile collision is stable.
- Keep the mission loop undefined until movement, animation, tile collision, interaction, and save/load are verified in Godot.
