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

`BoardedStarshipSector` creates `TileMapLayers` shells named `Floor`, `WallsCollision`, `Props`, `Doors`, and `GameplayMarkers`, then asks `StarshipLayoutBuilder` to populate generated child nodes under those layers. The generated map uses:

- `data/starship_sector_layout.json`: long corridor, side rooms, doors, props, and labels.
- `data/spaceship_tile_catalog.json`: atlas sheet paths and regions from the imported spaceship tileset.
- `scripts/world/starship_layout_builder.gd`: walkable-grid layout, white tiled floor rendering, black-base/white-panel wall rendering, door/prop sprite placement, and collision generation.
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
- two-tile-wide long corridor across the sector
- shiny white floor tiles with black borders for the playable corridor and rooms
- black-base walls with white wall panels and dark cap lines, matching the current reference image
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
- Convert the JSON-generated layout into real painted `TileMapLayer` content when the editor workflow is ready.
- Use PixelLab only for supplemental missing tiles, props, and map reference art after checking balance and choosing an explicit output directory.
- Add Leia and Vader sprites when available.
- Expand NPC behavior from static/patrol markers into sandbox behaviors.
- Add wall-aware line-of-sight once tile collision is stable.
- Keep the mission loop undefined until movement, animation, tile collision, interaction, and save/load are verified in Godot.
