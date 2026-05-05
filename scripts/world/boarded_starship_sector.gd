class_name BoardedStarshipSector
extends Node2D

signal player_ready(player: PlayerController)
signal guard_ready(guard: GuardAI)
signal status_requested(message: String)

const PlayerScene: PackedScene = preload("res://scenes/actors/Player.tscn")
const GuardScene: PackedScene = preload("res://scenes/actors/Guard.tscn")
const StarshipLayoutBuilderScript: Script = preload("res://scripts/world/starship_layout_builder.gd")
const PaintedTiledMapLoaderScript: Script = preload("res://scripts/world/painted_tiled_map_loader.gd")
const TILESET_ROOT := "res://assets/tilesets/spaceship_tileset/Spaceship Tileset"
const TILE_SIZE := 48.0
const MAP_ORIGIN := Vector2(80, 72)
const MAP_TILE_SIZE := 48.0
const MAIN_CORRIDOR_Y := 5
const MAIN_CORRIDOR_HEIGHT := 2

var player: PlayerController
var guard: GuardAI
var container: ContainerInteractable
var terminal: TerminalInteractable
var door: LockedDoor
var _spawn_position := Vector2(128, 384)
var _objective_area: Area2D
var _painted_map_loader: PaintedTiledMapLoader
var _painted_map_loaded := false


func _ready() -> void:
	_create_tilemap_layer_shells()
	_spawn_position = _main_corridor_center(1)
	_painted_map_loaded = _create_painted_starship_layout()
	_spawn_position = _marker_position_any(["player_spawn", "spawn"], _spawn_position)
	if not _painted_map_loaded and not _create_starship_layout():
		_create_placeholder_starship_map()
	_create_interactables()
	_create_npc_markers()
	_spawn_player()
	_spawn_guard()
	_create_objective_marker()


func reset_player_to_spawn() -> void:
	if player != null:
		player.reset_to(_spawn_position)


func to_save_data() -> Dictionary:
	var data := {
		"player": player.to_save_data() if player != null else {},
		"world": {
			"container": container.to_save_data() if container != null else {},
			"terminal": terminal.to_save_data() if terminal != null else {},
			"door": door.to_save_data() if door != null else {},
			"guard": guard.to_save_data() if guard != null else {}
		}
	}
	return data


func apply_save_data(data: Dictionary) -> void:
	if data.has("player") and data["player"] is Dictionary and player != null:
		player.apply_save_data(data["player"])

	var world_data: Dictionary = data.get("world", {}) as Dictionary
	if container != null and world_data.get("container", {}) is Dictionary:
		container.apply_save_data(world_data["container"])
	if terminal != null and world_data.get("terminal", {}) is Dictionary:
		terminal.apply_save_data(world_data["terminal"])
	if door != null and world_data.get("door", {}) is Dictionary:
		door.apply_save_data(world_data["door"])
	if guard != null and world_data.get("guard", {}) is Dictionary:
		guard.apply_save_data(world_data["guard"])


func _create_tilemap_layer_shells() -> void:
	var shell_root := Node2D.new()
	shell_root.name = "TileMapLayers"
	add_child(shell_root)

	for layer_name in ["Floor", "WallsCollision", "Props", "Doors", "GameplayMarkers", "Labels"]:
		var layer: Node = null
		if ClassDB.class_exists("TileMapLayer"):
			layer = ClassDB.instantiate("TileMapLayer") as Node
		if layer == null:
			layer = Node2D.new()
			layer.set_meta("tilemap_layer_placeholder", true)
		layer.name = layer_name
		shell_root.add_child(layer)


func _create_starship_layout() -> bool:
	var builder := StarshipLayoutBuilderScript.new() as StarshipLayoutBuilder
	if builder == null:
		return false
	return builder.build_into(self)


func _create_painted_starship_layout() -> bool:
	_painted_map_loader = PaintedTiledMapLoaderScript.new() as PaintedTiledMapLoader
	if _painted_map_loader == null:
		return false
	return _painted_map_loader.load_into(self)


func _create_placeholder_starship_map() -> void:
	_add_floor(Rect2(Vector2(40, 96), Vector2(1200, 520)), Color(0.24, 0.27, 0.28))
	_add_floor(Rect2(Vector2(80, 140), Vector2(1120, 432)), Color(0.24, 0.27, 0.28))
	_add_floor(Rect2(Vector2(90, 310), Vector2(1080, 96)), Color(0.24, 0.27, 0.28))
	_add_floor(Rect2(Vector2(760, 166), Vector2(210, 130)), Color(0.24, 0.27, 0.28))
	_add_floor(Rect2(Vector2(760, 420), Vector2(210, 120)), Color(0.24, 0.27, 0.28))
	_add_tileset_reference_tiles()

	_add_wall(Rect2(Vector2(40, 96), Vector2(1200, 28)))
	_add_wall(Rect2(Vector2(40, 588), Vector2(1200, 28)))
	_add_wall(Rect2(Vector2(40, 96), Vector2(28, 520)))
	_add_wall(Rect2(Vector2(1212, 96), Vector2(28, 520)))
	_add_wall(Rect2(Vector2(290, 124), Vector2(28, 180)))
	_add_wall(Rect2(Vector2(290, 418), Vector2(28, 170)))
	_add_wall(Rect2(Vector2(690, 124), Vector2(28, 186)))
	_add_wall(Rect2(Vector2(690, 410), Vector2(28, 178)))
	_add_wall(Rect2(Vector2(982, 124), Vector2(28, 190)))
	_add_wall(Rect2(Vector2(982, 410), Vector2(28, 178)))

	_add_floor(Rect2(Vector2(68, 315), Vector2(70, 86)), Color(0.24, 0.27, 0.28))
	_add_label("Breach", Vector2(78, 284), Color(1.0, 0.52, 0.34))
	_add_label("Droid escape bay", Vector2(1010, 528), Color(0.55, 0.90, 1.0))
	_add_label("Leia marker", Vector2(790, 142), Color(0.95, 0.86, 0.55))
	_add_label("Vader marker", Vector2(1035, 144), Color(0.92, 0.24, 0.22))

	for cover_position in [Vector2(435, 318), Vector2(525, 392), Vector2(828, 312), Vector2(900, 392)]:
		_add_prop(cover_position, Vector2(48, 30), Color(0.74, 0.76, 0.75))


func _create_interactables() -> void:
	container = ContainerInteractable.new()
	container.name = "PartsContainer"
	container.position = _marker_position_any(["container", "parts_container"], _grid_to_center(Vector2i(5, 2)))
	add_child(container)

	terminal = TerminalInteractable.new()
	terminal.name = "AccessTerminal"
	terminal.position = _marker_position_any(["terminal", "access_terminal"], _grid_to_center(Vector2i(8, 9)))
	add_child(terminal)

	door = LockedDoor.new()
	door.name = "BlastDoorAlpha"
	door.position = _marker_position_any(["door", "blast_door_alpha"], _main_corridor_center(21))
	add_child(door)


func _create_npc_markers() -> void:
	_add_character_marker("rebelsoldier", _main_corridor_center(3), "west", 1.0)
	_add_character_marker("rebelsoldier", _main_corridor_center(4), "west", 1.0)
	_add_character_marker("imperial_officer", _grid_to_center(Vector2i(22, 3)), "west", 1.0)
	_add_character_marker("cp3o", _grid_to_center(Vector2i(18, 11)), "south", 1.0)
	_add_character_marker("r2d2_replica", _grid_to_center(Vector2i(19, 11)), "south", 1.0)
	_add_character_marker("gnk-droid", _grid_to_center(Vector2i(16, 11)), "east", 1.0)
	_add_placeholder_marker("Princess Leia", _grid_to_center(Vector2i(21, 3)), Color(0.95, 0.85, 0.62))
	_add_placeholder_marker("Darth Vader", _main_corridor_center(23), Color(0.08, 0.08, 0.10))


func _spawn_player() -> void:
	player = PlayerScene.instantiate() as PlayerController
	add_child(player)
	player.reset_to(_spawn_position)
	player_ready.emit(player)


func _spawn_guard() -> void:
	guard = GuardScene.instantiate() as GuardAI
	add_child(guard)
	guard.global_position = _marker_position_any(["guard_spawn", "guard"], _main_corridor_center(9))
	var patrol_points: Array[Vector2] = _marker_positions("guard_patrol")
	if patrol_points.size() < 2:
		patrol_points = []
		patrol_points.append(_main_corridor_center(8))
		patrol_points.append(_main_corridor_center(18))
	guard.set_patrol_points(patrol_points)
	guard.set_target_player(player)
	guard_ready.emit(guard)


func _create_objective_marker() -> void:
	_objective_area = Area2D.new()
	_objective_area.name = "SandboxObjectiveMarker"
	_objective_area.position = _marker_position_any(["objective", "sandbox_objective"], _grid_to_center(Vector2i(20, 11)))
	_objective_area.collision_mask = 2
	_objective_area.body_entered.connect(_on_objective_entered)
	add_child(_objective_area)

	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(62, 96)
	collision.shape = shape
	_objective_area.add_child(collision)

	var visual := Polygon2D.new()
	visual.color = Color(0.12, 0.76, 0.90, 0.45)
	visual.polygon = PackedVector2Array([
		Vector2(-31, -48),
		Vector2(31, -48),
		Vector2(31, 48),
		Vector2(-31, 48)
	])
	_objective_area.add_child(visual)


func _add_floor(rect: Rect2, color: Color) -> void:
	var visual := Polygon2D.new()
	visual.color = color
	visual.position = rect.position
	visual.z_index = -20
	visual.polygon = PackedVector2Array([
		Vector2.ZERO,
		Vector2(rect.size.x, 0),
		rect.size,
		Vector2(0, rect.size.y)
	])
	add_child(visual)


func _add_tileset_reference_tiles() -> void:
	var floor_sheet := "%s/tilesets/Spacestation_Inside_A5.png" % TILESET_ROOT
	var wall_sheet := "%s/tilesets/Spacestation_Inside_A4.png" % TILESET_ROOT
	var console_sheet := "%s/characters/!Consoles.png" % TILESET_ROOT
	var door_sheet := "%s/characters/!Spaceship_door.png" % TILESET_ROOT

	for x in range(5):
		for y in range(2):
			_add_atlas_tile(floor_sheet, Rect2(Vector2(0, 0), Vector2(TILE_SIZE, TILE_SIZE)), Vector2(412 + x * 48, 330 + y * 48), -12)

	for x in range(4):
		_add_atlas_tile(wall_sheet, Rect2(Vector2(576, 384), Vector2(TILE_SIZE, TILE_SIZE)), Vector2(760 + x * 48, 172), -8)

	_add_atlas_tile(console_sheet, Rect2(Vector2(0, 0), Vector2(96, 96)), Vector2(842, 232), -2)
	_add_atlas_tile(door_sheet, Rect2(Vector2(0, 0), Vector2(96, 96)), Vector2(1000, 328), -2)


func _add_atlas_tile(path: String, region: Rect2, tile_position: Vector2, tile_z_index: int) -> void:
	if not ResourceLoader.exists(path):
		return

	var source_texture: Texture2D = load(path) as Texture2D
	if source_texture == null:
		return

	var atlas: AtlasTexture = AtlasTexture.new()
	atlas.atlas = source_texture
	atlas.region = region

	var sprite: Sprite2D = Sprite2D.new()
	sprite.texture = atlas
	sprite.position = tile_position
	sprite.z_index = tile_z_index
	add_child(sprite)


func _add_wall(rect: Rect2) -> void:
	var body := StaticBody2D.new()
	body.name = "Wall"
	body.position = rect.position + rect.size * 0.5
	body.collision_layer = 1
	body.collision_mask = 2
	add_child(body)

	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = rect.size
	collision.shape = shape
	body.add_child(collision)

	var visual := Polygon2D.new()
	visual.color = Color(1.0, 1.0, 1.0)
	visual.z_index = 8
	visual.polygon = PackedVector2Array([
		Vector2(-rect.size.x * 0.5, -rect.size.y * 0.5),
		Vector2(rect.size.x * 0.5, -rect.size.y * 0.5),
		Vector2(rect.size.x * 0.5, rect.size.y * 0.5),
		Vector2(-rect.size.x * 0.5, rect.size.y * 0.5)
	])
	body.add_child(visual)


func _add_prop(position: Vector2, size: Vector2, color: Color) -> void:
	var body := StaticBody2D.new()
	body.name = "CoverProp"
	body.position = position
	body.collision_layer = 1
	body.collision_mask = 2
	add_child(body)

	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = size
	collision.shape = shape
	body.add_child(collision)

	var visual := Polygon2D.new()
	visual.color = color
	visual.z_index = 4
	visual.polygon = PackedVector2Array([
		Vector2(-size.x * 0.5, -size.y * 0.5),
		Vector2(size.x * 0.5, -size.y * 0.5),
		Vector2(size.x * 0.5, size.y * 0.5),
		Vector2(-size.x * 0.5, size.y * 0.5)
	])
	body.add_child(visual)


func _add_character_marker(character_id: String, marker_position: Vector2, direction: String, scale_amount: float) -> void:
	var sprite := Sprite2D.new()
	sprite.name = "%sMarker" % character_id
	sprite.position = marker_position
	sprite.scale = Vector2.ONE * scale_amount
	sprite.texture = _load_marker_texture(character_id, direction)
	add_child(sprite)

	if sprite.texture == null:
		_add_placeholder_marker(character_id, marker_position, Color(0.55, 0.55, 0.70))


func _load_marker_texture(character_id: String, direction: String) -> Texture2D:
	var paths: Array[String] = [
		"res://assets/sprites/characters/%s/rotations/%s.png" % [character_id, direction],
		"res://assets/sprites/characters/%s/%s.png" % [character_id, direction],
		"res://assets/sprites/characters/%s/animations/walking/%s/frame_000.png" % [character_id, direction],
		"res://assets/sprites/characters/%s/animations/rolling/%s/frame_000.png" % [character_id, direction]
	]

	for path in paths:
		if ResourceLoader.exists(path):
			var texture: Texture2D = load(path) as Texture2D
			if texture != null:
				return texture
	return null


func _add_placeholder_marker(label_text: String, marker_position: Vector2, color: Color) -> void:
	var visual := Polygon2D.new()
	visual.name = label_text.replace(" ", "") + "Placeholder"
	visual.position = marker_position
	visual.color = color
	visual.polygon = PackedVector2Array([
		Vector2(0, -24),
		Vector2(18, -8),
		Vector2(14, 20),
		Vector2(-14, 20),
		Vector2(-18, -8)
	])
	add_child(visual)
	_add_label(label_text, marker_position + Vector2(-34, 28), Color(0.85, 0.88, 1.0))


func _add_label(text: String, label_position: Vector2, color: Color) -> void:
	var label := Label.new()
	label.text = text
	label.position = label_position
	label.z_index = 20
	label.add_theme_font_size_override("font_size", 12)
	label.add_theme_color_override("font_color", color)
	add_child(label)


func _grid_to_center(grid: Vector2i) -> Vector2:
	return MAP_ORIGIN + Vector2(
		float(grid.x) * MAP_TILE_SIZE + MAP_TILE_SIZE * 0.5,
		float(grid.y) * MAP_TILE_SIZE + MAP_TILE_SIZE * 0.5
	)


func _main_corridor_center(grid_x: int) -> Vector2:
	return MAP_ORIGIN + Vector2(
		float(grid_x) * MAP_TILE_SIZE + MAP_TILE_SIZE * 0.5,
		(float(MAIN_CORRIDOR_Y) + float(MAIN_CORRIDOR_HEIGHT) * 0.5) * MAP_TILE_SIZE
	)


func _marker_position_any(names_or_kinds: Array[String], fallback: Vector2) -> Vector2:
	if _painted_map_loader == null:
		return fallback
	return _painted_map_loader.marker_position_any(names_or_kinds, fallback)


func _marker_positions(name_or_kind: String) -> Array[Vector2]:
	if _painted_map_loader == null:
		var empty: Array[Vector2] = []
		return empty
	return _painted_map_loader.marker_positions(name_or_kind)


func _on_objective_entered(body: Node2D) -> void:
	if body == player:
		status_requested.emit("Sandbox objective marker reached")
