# GalacticX Repo Wiki

## Overview

GalacticX is a Godot 4 low top-down starship boarding sandbox using GDScript. The active project is now a systems-first prototype for 8-direction movement, variable-frame character animation, PixelLab-sourced assets, tilemap-ready world structure, interaction, HUD state, NPC patrol/suspicion, inventory/crafting test items, and JSON save/load.

The current slice intentionally does not define a fixed mission core loop. It provides reusable sandbox systems for later mission design.

## Entry Points

- `project.godot`: Godot project configuration. Main scene is `res://scenes/Main.tscn`.
- `scenes/Main.tscn`: Root scene. Owns `GameState`, `SaveSystem`, `BoardedStarshipSector`, and `HUD`.
- `scripts/main.gd`: Coordinates input actions, game-state signals, interaction, save/load, HUD updates, and alert reset behavior.
- `scenes/world/BoardedStarshipSector.tscn`: Sandbox starship scene.
- `scripts/world/boarded_starship_sector.gd`: Builds tilemap layer shells, tries the converted Tiled painted-map loader, falls back to the JSON-driven procedural layout builder, places sandbox interactables, NPC markers, player, patrol guard, and objective marker.

## Gameplay References

- `docs/references/a_new_hope_boarding_scene_gameplay_reference.md`: high-level design reference for the private Star Wars boarding-scene demo. It covers corridor layout, faction roles, droid escape behavior, Leia/Vader scenario anchors, patrol and suspicion pressure, and 8-direction low top-down animation requirements. It intentionally avoids dialogue, screenplay text, subtitles, and shot-by-shot reproduction.

## Scene Structure

- `scenes/actors/Player.tscn`: `CharacterBody2D` using `scripts/actors/player_controller.gd`.
- `scenes/actors/Guard.tscn`: `CharacterBody2D` using `scripts/actors/guard_ai.gd`.
- `scenes/ui/HUD.tscn`: `CanvasLayer` using `scripts/ui/hud.gd`.
- `scenes/world/BoardedStarshipSector.tscn`: world root using `scripts/world/boarded_starship_sector.gd`.

`BoardedStarshipSector` creates a `TileMapLayers` shell with expected layer names:

- `Floor`
- `WallsCollision`
- `Props`
- `Doors`
- `GameplayMarkers`
- `Labels`

The directories `assets/maps/` and `assets/tilesets/` are reserved for prebuilt maps and PixelLab-generated/imported tilesets. `assets/tilesets/spaceship_tileset/` now contains the imported spaceship interior sheets from `Spaceship tileset.rar`.

The current starship sector first tries to load a converted Tiled map:

- `data/maps/starship_sector_painted.json`: optional active painted-map JSON in `galacticx_tiled_map_v1` format.
- `scripts/world/painted_tiled_map_loader.gd`: loads visual atlas placements, collision shapes, labels, and gameplay markers from the converted Tiled map.

If no painted map is available, the sector is generated at runtime from:

- `data/starship_sector_layout.json`: 48px grid layout for a long main corridor, side rooms, room doors, props, labels, and sandbox markers.
- `data/spaceship_tile_catalog.json`: atlas sheet IDs and region rectangles for floor, wall, door, console, chest, reactor, medbay, navigator, and light art.
- `scripts/world/tile_catalog.gd`: loads atlas regions safely and returns `AtlasTexture` instances.
- `scripts/world/starship_layout_builder.gd`: converts room rectangles into walkable cells, generates surrounding wall cells, places floor/wall/door/prop sprites, and creates `StaticBody2D` collision.

If the catalog or layout fails to load, `BoardedStarshipSector` falls back to the older placeholder rectangle map so the project still opens.

## Systems

- `scripts/systems/directional_animation.gd`: reusable 8-facing animation loader. It supports `north`, `south`, `east`, `west`, `north-east`, `north-west`, `south-east`, and `south-west`.
- `scripts/systems/inventory_system.gd`: item counts, add/remove/has, save/load data.
- `scripts/systems/crafting_system.gd`: recipe loading from `data/recipes.json`; default recipe is `battery + wire + scrap_metal = hack_tool`.
- `scripts/systems/time_system.gd`: simple in-game clock and schedule phase placeholder.
- `scripts/systems/game_state.gd`: inventory, crafting, time, suspicion, alert, and status signal hub.
- `scripts/systems/interaction_system.gd`: resolves the player’s nearest interactable and emits HUD prompts.
- `scripts/systems/save_system.gd`: JSON save/load at `user://galacticx_save.json`.
- `scripts/world/painted_tiled_map_loader.gd`: converted Tiled JSON map loader used before the procedural fallback.
- `scripts/world/starship_layout_builder.gd`: data-driven long-corridor map generator for the current sandbox sector fallback.
- `scripts/world/tile_catalog.gd`: imported tileset atlas loader used by the layout builder.

## Character Animation Convention

All moving actors should support eight facings:

- `north`
- `south`
- `east`
- `west`
- `north-east`
- `north-west`
- `south-east`
- `south-west`

The loader supports variable frame counts from 2 to 8 frames per state and direction. It discovers `frame_*.png`, sorts numerically, and loops the available frames.

Load order:

1. `assets/sprites/characters/<character>/animations/<state>/<direction>/frame_*.png`
2. `assets/sprites/characters/<character>/rotations/<direction>.png`
3. `assets/sprites/characters/<character>/<direction>.png`
4. Generated colored placeholder texture

Known current coverage:

- `stormtrooper_gun`: 8-direction walking frames and rotations.
- `r2d2_replica`: 8-direction rolling frames and rotations.
- `cp3o`: 8-direction walking, pushbutton, surprise, and death frames.
- `astromech`: 8-direction sad-walk frames and rotations.
- `imperial_officer`, `gnk-droid`, `golddroid`: 8-direction rotations.
- `rebelsoldier`: root directional files.
- Leia and Vader currently use placeholder markers unless sprites are added.

## PixelLab Asset Pipeline

PixelLab is the source agent for characters, character animations, props, tilesets, and map visual assets.

- Agent instructions: `.claude/agents/pixellab-api-asset-agent.md`
- Helper script: `scripts/pixellab_api.py`
- Workflow docs: `docs/pixellab-api.md`
- Auth check: `python3 scripts/pixellab_api.py balance`

Asset output conventions:

- Characters: `assets/sprites/characters/<character>/...`
- Generated character iterations: `assets/sprites/characters/<character>/api_generated/<task>/`
- Tilesets: `assets/tilesets/<tileset_name>/`
- Maps/layout references: `assets/maps/<map_name>/`
- Props: `assets/sprites/props/`
- Effects: `assets/sprites/effects/`

Do not overwrite existing PixelLab PNGs or metadata; use unique output directories or prefixes for new generations.

For this sector, the imported local spaceship tileset is the primary art source. PixelLab should be used for missing supplemental pieces, such as extra doors, corridor dressing, terminal variants, droid route markers, or map reference images. Run `python3 scripts/pixellab_api.py balance` first, and do not start a paid generation job without an explicit prompt, dimensions, and output directory.

## Imported Spaceship Tileset

Imported path: `assets/tilesets/spaceship_tileset/`.

Important sheets:

- `Spaceship Tileset/tilesets/Spacestation_Inside_A1.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_A2.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_A4.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_A5.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_B.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_C.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_D.png`
- `Spaceship Tileset/tilesets/Spacestation_Inside_E.png`

Object sheets under `Spaceship Tileset/characters/` include consoles, doors, lights, chests, reactors, navigator, medbay, ladder, switches, and decoration. Parallax sheets live under `Spaceship Tileset/parallaxes/`.

The imported PNG dimensions are consistent with a 48px tile grid. The runtime layout builder currently uses a procedural corridor style for readable level structure: a flat gunmetal floor color (`Color(0.24, 0.27, 0.28)`), a visible main-corridor floor strip scaled to `0.4` of the underlying two-tile width, and 96x96 wall visuals from `assets/tilesets/starwars/wall_tile_96.png`. The wall tile is a strict 96x96 resize of the full supplied reference image at `assets/tilesets/starwars/wall_tile_reference.png`; collision still uses the 48px gameplay grid. Every second north-face corridor wall cell gets a hanging `GX0861` overlay (`Spacestation_Inside_C.png`, atlas `x=480 y=432 48x48`) with small red and blue indicator dots; this does not replace the base wall tile. Doors and props still use direct `AtlasTexture` regions from the imported spaceship sheets where useful. The editor path now uses Tiled on a 16px map grid, with larger 48px/96px-style art placed as objects and converted into Godot-ready JSON.

Door visuals use the selected `!Spaceship_door.png` frame column from the numbered catalog and render through a white-door shader:

- `GX2036`: open frame, atlas `x=288 y=0 48x96`
- `GX2048`: partially open frame 1, atlas `x=288 y=96 48x96`
- `GX2060`: partially open frame 2, atlas `x=288 y=192 48x96`
- `GX2072`: closed frame, atlas `x=288 y=288 48x96`

Generated passable room doors use the open frame. The interactive `LockedDoor` uses `GX2072` while closed, plays through `GX2060` and `GX2048` during the open transition, and settles on `GX2036` when opened.

## Numbered Tileset Selection Catalog

The imported spaceship tileset now has a generated selection catalog at `docs/tileset_catalog/index.html`, with metadata in `docs/tileset_catalog/manifest.json` and sliced PNGs under `docs/tileset_catalog/slices/`.

Regenerate it with:

```bash
python3 scripts/build_tileset_catalog.py
```

The catalog assigns stable-looking IDs such as `GX0001`, `GX0002`, and onward during generation. Tile sheets under `Spaceship Tileset/tilesets/` are cut into 48x48 cells. RPG Maker-style character/object sheets under `Spaceship Tileset/characters/` are preserved as larger selectable frames where possible: `!$*.png` sheets are split into 3 columns by 4 rows, and `!*.png` sheets are split into 12 columns by 8 rows. Fully transparent cells are skipped unless the script is run with `--include-empty`.

Use the HTML page when choosing floor, wall, door, prop, object, character, or item regions for Godot layout work. Click a thumbnail to open a zoomable pixel-preview modal, use the zoom slider or plus/minus buttons for close inspection, and use the Copy button to copy the selected ID. Once IDs are chosen, use `manifest.json` to map the selected ID back to the source sheet, atlas coordinates, cell size, and generated preview PNG.

## Tiled Map Workflow

Tiled setup files live under `assets/maps/tiled/`:

- `galacticx.tiled-project`: Tiled project file.
- `starship_sector_template.json`: 16x16-grid starter map with `Floor`, `WallsCollision`, `Props`, `Doors`, `GameplayMarkers`, and `Labels`.
- `palettes/*.json`: nine generated Tiled palette tabs grouped as floor tiles, wall tiles, doors, consoles, reactors/medbay, storage, lights, and decorations.
- `palettes/*.png`: generated atlas images used by those palette tabs.
- `tilesets/*.json`: compatibility tilesets for every imported spaceship tilesheet and object sheet.

Regenerate the setup with `python3 scripts/build_tiled_map_setup.py`. Convert a painted Tiled JSON map with `python3 scripts/convert_tiled_map.py assets/maps/tiled/<map>.json data/maps/starship_sector_painted.json`. The runtime uses marker names or `kind` properties for `player_spawn`, `container`, `terminal`, `door`, `guard_spawn`, `guard_patrol`, and `objective`.

## Runtime Starship Layout

Current generated sector:

- Breach/start area at the left side of the main corridor.
- Main corridor: `data/starship_sector_layout.json` room `main_corridor`, rect `[0, 5, 24, 2]`, with `corridor_style.floor_width_scale` set to `0.4` so the visible floor band is 60% narrower than the old two-tile-wide corridor.
- Bulkheads: every five corridor tiles, drawn as open white blast-door panels retracted into the top and bottom wall sections.
- Door frames: selected from `GX2036`, `GX2048`, `GX2060`, and `GX2072`, rendered white.
- North wall panels: `GX0861` hangs over every second north-face wall tile as a button/control detail.
- North rooms: storage, reactor, and command.
- South rooms: terminal and droid escape bay.
- Sandbox interactables: parts container at grid `[5, 2]`, access terminal at `[8, 10]`, locked command bulkhead at `[21, 5]`, and objective marker near the droid escape bay.
- Guard patrol: centerline movement between the narrowed corridor points at grid x `8` and `18`.

The layout is systems-first. It exists to validate top-down navigation, imported tileset rendering, wall collision, room placement, interaction prompts, NPC patrol/suspicion, HUD state, and save/load before a mission loop is defined.

## Input Actions

`scripts/main.gd` registers these at runtime:

- `move_left`: `A`, left arrow
- `move_right`: `D`, right arrow
- `move_up`: `W`, up arrow
- `move_down`: `S`, down arrow
- `interact`: `E`
- `inventory`: `I`, tab
- `craft_debug`: `C`
- `save_debug`: `F5`
- `load_debug`: `F9`

## Sandbox Interactables

- `ContainerInteractable`: search a storage crate and receive `battery`, `wire`, and `scrap_metal`.
- `TerminalInteractable`: use an access terminal and receive `access_card`.
- `LockedDoor`: sealed blast door opens with `hack_tool` or `access_card`.
- `SandboxObjectiveMarker`: updates status when reached.

## Save Data

Save path: `user://galacticx_save.json`.

Saved fields include:

- player position and facing
- inventory
- suspicion
- current in-game time
- container looted state
- terminal activation state
- blast door unlocked/open state
- guard position, facing, and patrol index

## RAG Usage

Build the lexical index:

```bash
python3 scripts/rag.py index
```

The generated asset inventory includes image paths under `assets/sprites/`, `assets/tilesets/`, and `assets/maps/`, so imported spaceship tileset PNGs are retrievable by name.

Build embeddings:

```bash
python3 scripts/rag.py embed --provider hash --force
```

Search examples:

```bash
python3 scripts/rag.py search "8-direction animation loader" --mode hybrid
python3 scripts/rag.py search "PixelLab tileset asset pipeline" --mode hybrid
python3 scripts/rag.py context "how should the starship boarding scene guide level design" --mode hybrid
```

Generated index files:

- `.rag/index.jsonl`
- `.rag/embeddings.jsonl`

Both are ignored by git.

## Validation Status

Verified locally:

- `python3 -m py_compile scripts/rag.py scripts/pixellab_api.py`
- `python3 -m py_compile scripts/build_tiled_map_setup.py scripts/convert_tiled_map.py`
- `python3 tests/test_convert_tiled_map.py`
- `python3 scripts/convert_tiled_map.py tests/fixtures/tiled/sample_starship.tiled.json data/maps/fixtures/sample_starship_converted.json`
- RAG index and hash embeddings can be rebuilt.
- `python3 scripts/pixellab_api.py balance` reached PixelLab successfully in the current shell.

Not verified locally yet:

- Godot runtime parsing/playtesting, because `godot` and `godot4` were not available in the current shell.
- Native painted Godot `TileSet`/`TileMapLayer` resource import from the spaceship sheets, because this requires Godot editor or CLI tooling. The current painted-map path uses converted Tiled JSON at runtime instead.

## Documentation Maintenance Rules

- Update this wiki when changing scene structure, GDScript behavior, PixelLab workflow, map/tileset conventions, save data, or important asset paths.
- Keep this wiki factual and current.
- Rebuild `.rag/index.jsonl` and `.rag/embeddings.jsonl` after documentation, script, scene, or data changes.
