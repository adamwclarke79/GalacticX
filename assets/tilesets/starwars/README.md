# Starship Custom Tiles

This folder contains custom starship tile references and derived runtime tiles.

## Walls

- `wall_tile_reference.png`: supplied 1254x1254 source image.
- `wall_tile_96.png`: strict 96x96 resize of the full source image.
- `wall_tile_buttons_48x96.png`: sharpened 48x96 bright-white wall-panel resize from `White_wall_tile_Buttons.png`.
- `wall_tile_plain_48x96.png`: sharpened 48x96 bright-white wall-panel resize from `White_wall_tile.png`.
- `wall_tile_v2_white_outline_48x96.png`: sharpened 48x96 wall-panel resize from `White_wall_tile_V2.png` with the edge-connected black exterior changed to white and added shading around the upper white panel.
- `wall_tile_v2_orange_alt_48x96.png`: duplicate of `wall_tile_v2_white_outline_48x96.png` with the lower orange display marks rearranged.
- `wall_panels_bright_96.png`: brightened 4x4 sheet derived from `883f7f35-5200-4f7b-a518-21d18bf528a5.png`, with each cell resized to 96x96.
- `wall_panels_bright_96/`: individual 96x96 slices from `wall_panels_bright_96.png`. The closed door at `r00_c03` and open dark doorway at `r01_c00` are routed to the generated `04 Doors` Tiled palette; the other slices are routed to `02 Walls`.
- `wall_panels_48.png`: 4x4 preview sheet of the supplied May 6 panel tiles, cut to 48x48 with transparent backgrounds.
- `wall_panels_48/`: individual 48x48 slices from `wall_panels_48.png`. The closed door at `r01_c00` and open dark doorway at `r01_c01` are routed to the generated `04 Star Wars Doors 48` Tiled palette; the other slices are routed to `02 Star Wars Walls 48`.

`StarshipLayoutBuilder` uses `wall_tile_96.png` for wall visuals while keeping collision on the existing 48px gameplay grid.
`scripts/build_tiled_map_setup.py` appends the custom Star Wars wall-panel and door-panel tiles to the generated Tiled palettes.
