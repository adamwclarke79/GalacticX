# Starship Custom Tiles

This folder contains custom starship tile references and derived runtime tiles.

## Walls

- `wall_tile_reference.png`: supplied 1254x1254 source image.
- `wall_tile_96.png`: strict 96x96 resize of the full source image.
- `wall_tile_buttons_48x96.png`: sharpened 48x96 bright-white wall-panel resize from `White_wall_tile_Buttons.png`.
- `wall_tile_plain_48x96.png`: sharpened 48x96 bright-white wall-panel resize from `White_wall_tile.png`.
- `wall_tile_v2_white_outline_48x96.png`: sharpened 48x96 wall-panel resize from `White_wall_tile_V2.png` with the edge-connected black exterior changed to white and added shading around the upper white panel.
- `wall_tile_v2_orange_alt_48x96.png`: duplicate of `wall_tile_v2_white_outline_48x96.png` with the lower orange display marks rearranged.

`StarshipLayoutBuilder` uses `wall_tile_96.png` for wall visuals while keeping collision on the existing 48px gameplay grid.
`scripts/build_tiled_map_setup.py` appends the 48x96 Star Wars wall-panel tiles to the generated `02 Wall Tiles` Tiled palette.
