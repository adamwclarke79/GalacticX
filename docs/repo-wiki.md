# GalacticX Repo Wiki

## Overview

GalacticX is a Godot 4 low top-down starship boarding sandbox using GDScript. The active project is now a systems-first prototype for 8-direction movement, variable-frame character animation, PixelLab-sourced assets, tilemap-ready world structure, interaction, HUD state, NPC patrol/suspicion, inventory/crafting test items, and JSON save/load.

The current slice intentionally does not define a fixed mission core loop. It provides reusable sandbox systems for later mission design.

## Entry Points

- `project.godot`: Godot project configuration. Main scene is `res://scenes/Main.tscn`.
- `scenes/Main.tscn`: Root scene. Owns `GameState`, `SaveSystem`, `BoardedStarshipSector`, and `HUD`.
- `scripts/main.gd`: Coordinates input actions, game-state signals, interaction, save/load, HUD updates, and alert reset behavior.
- `scenes/world/BoardedStarshipSector.tscn`: Sandbox starship scene.
- `scripts/world/boarded_starship_sector.gd`: Builds tilemap layer shells, runs the JSON-driven starship layout builder, places sandbox interactables, NPC markers, player, patrol guard, and objective marker.

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

The directories `assets/maps/` and `assets/tilesets/` are reserved for prebuilt maps and PixelLab-generated/imported tilesets. `assets/tilesets/spaceship_tileset/` now contains the imported spaceship interior sheets from `Spaceship tileset.rar`.

The current starship sector is generated at runtime from:

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
- `scripts/world/starship_layout_builder.gd`: data-driven long-corridor map generator for the current sandbox sector.
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

The imported PNG dimensions are consistent with a 48px tile grid. The runtime layout builder currently uses a procedural corridor style for readable level structure: shiny white floor tiles with black borders, and wall cells with white panels, dark cap lines, and a black lower base matching the current visual reference. Doors and props still use direct `AtlasTexture` regions from the imported spaceship sheets where useful. The next editor step is to build a proper Godot `TileSet` resource and paint real `TileMapLayer` content from the same layout.

## Runtime Starship Layout

Current generated sector:

- Breach/start area at the left side of the main corridor.
- Main corridor: `data/starship_sector_layout.json` room `main_corridor`, rect `[0, 5, 24, 2]`.
- Bulkheads: every five corridor tiles, drawn as open white blast-door panels retracted into the top and bottom wall sections.
- North rooms: storage, reactor, and command.
- South rooms: terminal and droid escape bay.
- Sandbox interactables: parts container at grid `[5, 2]`, access terminal at `[8, 10]`, locked command bulkhead at `[21, 5]`, and objective marker near the droid escape bay.
- Guard patrol: corridor loop between grid cells `[8,6]`, `[18,6]`, `[18,7]`, and `[8,7]`.

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
- RAG index and hash embeddings can be rebuilt.
- `python3 scripts/pixellab_api.py balance` reached PixelLab successfully in the current shell.

Not verified locally yet:

- Godot runtime parsing/playtesting, because `godot` and `godot4` were not available in the current shell.
- Painted Godot `TileSet`/`TileMapLayer` import from the spaceship sheets, because this requires Godot editor or CLI tooling.

## Documentation Maintenance Rules

- Update this wiki when changing scene structure, GDScript behavior, PixelLab workflow, map/tileset conventions, save data, or important asset paths.
- Keep this wiki factual and current.
- Rebuild `.rag/index.jsonl` and `.rag/embeddings.jsonl` after documentation, script, scene, or data changes.
