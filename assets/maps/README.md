# GalacticX Maps

Place prebuilt starship map files and layout references here.

Expected convention:

- `assets/maps/<map_name>/`
- Include source map data, exported Godot resources, and any reference PNGs needed by the PixelLab asset workflow.
- Active Godot scenes should map these into `TileMapLayer` nodes named `Floor`, `WallsCollision`, `Props`, `Doors`, and `GameplayMarkers`.
