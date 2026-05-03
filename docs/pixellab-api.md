# PixelLab API Integration

GalacticX uses PixelLab API v2 for generated pixel art assets.

## Authentication

PixelLab v2 uses Bearer token authentication:

```bash
Authorization: Bearer YOUR_API_TOKEN
```

Store the local token in `.env` as `PIXELLAB_API_TOKEN`. The `.env` file is ignored by git.

```bash
PIXELLAB_API_TOKEN=your-token-here
```

The token is available from the PixelLab account page:

```text
https://pixellab.ai/account
```

## Connection Check

Use `GET /balance` through the helper script. This validates auth without spending generation credits.

```bash
python3 scripts/pixellab_api.py balance
```

## Generate Pixel Art

The project helper wraps `POST /generate-image-v2`, then polls `GET /background-jobs/{job_id}` until the job completes.

```bash
python3 scripts/pixellab_api.py generate-image-v2 \
  --description "small sci-fi data core, transparent background, crisp 16-bit pixel art" \
  --width 64 \
  --height 64 \
  --output-dir assets/sprites/api_generated/data_core \
  --image-prefix data_core
```

Saved artifacts:

- `<artifact-prefix>_request.summary.json`
- `<artifact-prefix>_submit.json`
- `<artifact-prefix>_job_result.json`
- `<image-prefix>_00.png` and later numbered images when PixelLab returns multiple outputs

Use `--image-field quantized_images` when you want PixelLab's quantized pixel-art result instead of the raw `images` field.

## Reference Images

PixelLab supports subject references and a style image for `generate-image-v2`.

```bash
python3 scripts/pixellab_api.py generate-image-v2 \
  --description "front-facing compact armored sci-fi trooper sprite" \
  --width 208 \
  --height 208 \
  --style-image assets/sprites/characters/stormtrooper_gun/rotations/south.png \
  --style-usage "Match palette, outline, detail, and shading" \
  --output-dir assets/sprites/characters/stormtrooper_gun/api_generated/chest_blaster \
  --image-prefix stormtrooper_chest_blaster \
  --artifact-prefix generate_image_v2
```

References:

- PixelLab v2 docs: https://api.pixellab.ai/v2/docs
- AI-assistant docs: https://api.pixellab.ai/v2/llms.txt

## PixelLab Agent

Use `.claude/agents/pixellab-api-asset-agent.md` for PixelLab API work.

Agent responsibilities:

- Validate `PIXELLAB_API_TOKEN` auth with `python3 scripts/pixellab_api.py balance`.
- Generate assets through `scripts/pixellab_api.py generate-image-v2`.
- Keep generated outputs under `assets/sprites/**/api_generated/**`.
- Save request summaries, submit responses, job results, and returned PNGs with stable names.
- Avoid printing, committing, or documenting real API token values.
- Update `docs/repo-wiki.md` and rebuild `python3 scripts/rag.py index` after PixelLab workflow documentation changes.

## GalacticX Asset Ownership

PixelLab is the source pipeline for generated characters, directional animation frames, map props, low top-down tilesets, and map visual reference assets.

Stable output directories:

- Characters: `assets/sprites/characters/<character>/`
- Generated character iterations: `assets/sprites/characters/<character>/api_generated/<task>/`
- Props and interactables: `assets/sprites/props/`
- Effects: `assets/sprites/effects/`
- Tilesets: `assets/tilesets/<tileset_name>/`
- Maps and layout references: `assets/maps/<map_name>/`

Do not overwrite existing PNGs, metadata, request summaries, submit responses, or job results. Use a unique task directory or image prefix for each generation pass.

## Tilesets And Maps

Use the PixelLab MCP/API tileset workflow for low top-down starship tilesets when available. The current plan expects Godot `TileMapLayer` layers named:

- `Floor`
- `WallsCollision`
- `Props`
- `Doors`
- `GameplayMarkers`

Prebuilt tile maps should be placed under `assets/maps/` and imported into the Godot world scene. PixelLab-generated tilesets and map object sprites should be placed under `assets/tilesets/` and `assets/sprites/props/` before wiring them into Godot.

Run a balance check before any paid generation:

```bash
python3 scripts/pixellab_api.py balance
```

## Current Starship Sector Asset Rule

The current long-corridor sector uses the imported local archive at `assets/tilesets/spaceship_tileset/` as the primary tileset. Runtime atlas mappings live in `data/spaceship_tile_catalog.json`, and the generated sector layout lives in `data/starship_sector_layout.json`.

Use PixelLab for supplemental missing pieces only, such as:

- additional bulkhead or blast-door variants
- terminal and console variants
- corridor dressing props
- warning-light and smoke effects
- map reference art under `assets/maps/<map_name>/`

Do not run a paid PixelLab generation just because the map is being edited. First define the prompt, dimensions, output directory, and whether the output should go under `assets/tilesets/`, `assets/sprites/props/`, or `assets/maps/`.
