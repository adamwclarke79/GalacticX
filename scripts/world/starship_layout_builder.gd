class_name StarshipLayoutBuilder
extends RefCounted

const TileCatalogScript: Script = preload("res://scripts/world/tile_catalog.gd")
const DEFAULT_LAYOUT_PATH := "res://data/starship_sector_layout.json"
const DEFAULT_CATALOG_PATH := "res://data/spaceship_tile_catalog.json"
const CARDINAL_DIRECTIONS := [
	Vector2i(1, 0),
	Vector2i(-1, 0),
	Vector2i(0, 1),
	Vector2i(0, -1)
]

var catalog: TileCatalog = TileCatalogScript.new() as TileCatalog
var layout: Dictionary = {}
var grid_size: int = 48
var origin := Vector2.ZERO
var _walkable_cells: Dictionary = {}
var _door_cells: Dictionary = {}
var _wall_cells: Dictionary = {}
var _corridor_rects: Array[Rect2i] = []


func build_into(parent: Node2D, layout_path: String = DEFAULT_LAYOUT_PATH, catalog_path: String = DEFAULT_CATALOG_PATH) -> bool:
	_clear_state()
	_clear_generated_layers(parent)

	if not catalog.load_from(catalog_path):
		return false
	if not _load_layout(layout_path):
		return false

	_populate_walkable_cells()
	if _walkable_cells.is_empty():
		return false

	var floor_layer: Node = _create_generated_layer(parent, "Floor")
	var wall_layer: Node = _create_generated_layer(parent, "WallsCollision")
	var prop_layer: Node = _create_generated_layer(parent, "Props")
	var door_layer: Node = _create_generated_layer(parent, "Doors")
	var marker_layer: Node = _create_generated_layer(parent, "GameplayMarkers")

	_paint_floor(floor_layer)
	_paint_walls(wall_layer)
	_paint_doors(door_layer)
	_paint_bulkheads(door_layer)
	_paint_props(prop_layer)
	_paint_labels(marker_layer)
	return true


func grid_to_world(cell: Vector2i) -> Vector2:
	return origin + Vector2(cell.x * grid_size, cell.y * grid_size)


func grid_to_center(cell: Vector2i) -> Vector2:
	return grid_to_world(cell) + Vector2(grid_size * 0.5, grid_size * 0.5)


func _clear_state() -> void:
	layout.clear()
	_walkable_cells.clear()
	_door_cells.clear()
	_wall_cells.clear()
	_corridor_rects.clear()


func _load_layout(path: String) -> bool:
	if not FileAccess.file_exists(path):
		push_warning("Starship layout missing: %s" % path)
		return false

	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_warning("Unable to open starship layout: %s" % path)
		return false

	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("Starship layout is not a JSON object: %s" % path)
		return false

	layout = parsed as Dictionary
	grid_size = int(layout.get("grid_size", catalog.tile_size))
	origin = _array_to_vector2(layout.get("origin", [0, 0]))
	return grid_size > 0


func _populate_walkable_cells() -> void:
	if not (layout.get("rooms", []) is Array):
		return
	var rooms_value: Array = layout["rooms"] as Array

	for room_value in rooms_value:
		if typeof(room_value) != TYPE_DICTIONARY:
			continue
		var room: Dictionary = room_value as Dictionary
		var room_rect: Rect2i = _array_to_rect2i(room.get("rect", []))
		if String(room.get("type", "")) == "corridor":
			_corridor_rects.append(room_rect)
		for x in range(room_rect.position.x, room_rect.position.x + room_rect.size.x):
			for y in range(room_rect.position.y, room_rect.position.y + room_rect.size.y):
				_mark_walkable(Vector2i(x, y))

		if room.has("door"):
			var door_cell: Vector2i = _array_to_vector2i(room["door"])
			_mark_walkable(door_cell)
			_door_cells[_cell_key(door_cell)] = door_cell


func _paint_floor(layer: Node) -> void:
	for key in _walkable_cells.keys():
		var cell: Vector2i = _walkable_cells[key] as Vector2i
		_add_corridor_floor_tile(layer, cell)


func _paint_walls(layer: Node) -> void:
	for key in _walkable_cells.keys():
		var cell: Vector2i = _walkable_cells[key] as Vector2i
		for direction_value in CARDINAL_DIRECTIONS:
			var direction: Vector2i = direction_value
			var wall_cell: Vector2i = cell + direction
			var wall_key: String = _cell_key(wall_cell)
			if _walkable_cells.has(wall_key) or _wall_cells.has(wall_key):
				continue
			_wall_cells[wall_key] = wall_cell
			_add_corridor_wall_panel(layer, wall_cell)
			_add_collision_rect(layer, "WallCollision", grid_to_center(wall_cell), Vector2(grid_size, grid_size))


func _paint_doors(layer: Node) -> void:
	for key in _door_cells.keys():
		var cell: Vector2i = _door_cells[key] as Vector2i
		_add_side_room_blast_door(layer, cell)


func _paint_bulkheads(layer: Node) -> void:
	var style: Dictionary = layout.get("corridor_style", {}) as Dictionary
	var interval: int = max(1, int(style.get("bulkhead_interval", 5)))
	var start_offset: int = int(style.get("bulkhead_start", interval))

	for corridor_rect in _corridor_rects:
		var first_x: int = corridor_rect.position.x + start_offset
		var last_x: int = corridor_rect.position.x + corridor_rect.size.x
		for x in range(first_x, last_x, interval):
			_add_open_bulkhead(layer, Vector2i(x, corridor_rect.position.y), corridor_rect.size.y)


func _paint_props(layer: Node) -> void:
	if not (layout.get("props", []) is Array):
		return
	var props_value: Array = layout["props"] as Array

	for prop_value in props_value:
		if typeof(prop_value) != TYPE_DICTIONARY:
			continue
		var prop: Dictionary = prop_value as Dictionary
		var kind: String = String(prop.get("kind", ""))
		if kind == "placeholder":
			continue

		var cell: Vector2i = _array_to_vector2i(prop.get("grid", [0, 0]))
		var region_id: String = _region_for_prop_kind(kind)
		if region_id == "":
			continue
		_add_region_sprite(layer, region_id, cell, 2)
		if _prop_blocks_movement(kind):
			_add_collision_rect(layer, "PropCollision", grid_to_center(cell), _collision_size_for_prop(kind))


func _paint_labels(layer: Node) -> void:
	if not (layout.get("labels", []) is Array):
		return
	var labels_value: Array = layout["labels"] as Array

	for label_value in labels_value:
		if typeof(label_value) != TYPE_DICTIONARY:
			continue
		var label_data: Dictionary = label_value as Dictionary
		var label: Label = Label.new()
		label.text = String(label_data.get("text", ""))
		label.position = grid_to_world(_array_to_vector2i(label_data.get("grid", [0, 0])))
		label.z_index = 20
		label.add_theme_font_size_override("font_size", 12)
		label.add_theme_color_override("font_color", Color(0.76, 0.86, 0.95))
		layer.add_child(label)


func _add_region_sprite(layer: Node, region_id: String, cell: Vector2i, z_index: int) -> void:
	var texture: Texture2D = catalog.make_texture(region_id)
	if texture == null:
		_add_fallback_rect(layer, cell, z_index, _fallback_color(region_id))
		return

	var sprite: Sprite2D = Sprite2D.new()
	sprite.texture = texture
	sprite.centered = false
	sprite.position = grid_to_world(cell)
	sprite.z_index = z_index
	layer.add_child(sprite)


func _add_corridor_floor_tile(layer: Node, cell: Vector2i) -> void:
	var tile_position: Vector2 = grid_to_world(cell)
	_add_rect_visual(layer, tile_position, Vector2(grid_size, grid_size), Color(0.53, 0.55, 0.55), -12)


func _add_corridor_wall_panel(layer: Node, cell: Vector2i) -> void:
	var tile_position: Vector2 = grid_to_world(cell)
	_add_rect_visual(layer, tile_position, Vector2(grid_size, grid_size), Color(0.88, 0.89, 0.88), -5)
	_add_rect_visual(layer, tile_position + Vector2(2.0, 2.0), Vector2(grid_size - 4.0, grid_size - 4.0), Color(0.96, 0.97, 0.96), -4)
	_add_rect_visual(layer, tile_position + Vector2(6.0, 7.0), Vector2(grid_size - 12.0, 3.0), Color(1.0, 1.0, 1.0, 0.50), -3)
	_add_rect_visual(layer, tile_position + Vector2(6.0, grid_size - 10.0), Vector2(grid_size - 12.0, 2.0), Color(0.62, 0.64, 0.64, 0.35), -3)
	_add_rect_visual(layer, tile_position + Vector2(4.0, 14.0), Vector2(2.0, 20.0), Color(0.58, 0.60, 0.60, 0.25), -2)
	_add_rect_visual(layer, tile_position + Vector2(grid_size - 8.0, 10.0), Vector2(2.0, 24.0), Color(0.38, 0.40, 0.40, 0.35), -2)
	_add_rect_visual(layer, tile_position + Vector2(grid_size - 15.0, 15.0), Vector2(5.0, 3.0), Color(0.12, 0.13, 0.13, 0.50), -1)
	_add_rect_visual(layer, tile_position + Vector2(11.0, 15.0), Vector2(7.0, 2.0), Color(0.74, 0.10, 0.10, 0.45), -1)
	_add_rect_visual(layer, tile_position + Vector2(19.0, 15.0), Vector2(6.0, 2.0), Color(0.12, 0.13, 0.13, 0.45), -1)


func _add_open_bulkhead(layer: Node, top_cell: Vector2i, corridor_height: int) -> void:
	var portal_top_left: Vector2 = grid_to_world(top_cell)
	var portal_height: float = float(corridor_height) * grid_size
	var top_wall_position: Vector2 = grid_to_world(Vector2i(top_cell.x, top_cell.y - 1))
	var bottom_wall_position: Vector2 = grid_to_world(Vector2i(top_cell.x, top_cell.y + corridor_height))

	_add_rect_visual(layer, portal_top_left + Vector2(-5.0, 0.0), Vector2(10.0, portal_height), Color(0.77, 0.78, 0.77), 3)
	_add_rect_visual(layer, portal_top_left + Vector2(-2.0, 5.0), Vector2(4.0, portal_height - 10.0), Color(0.95, 0.96, 0.95), 4)
	_add_rect_visual(layer, portal_top_left + Vector2(4.0, 0.0), Vector2(2.0, portal_height), Color(0.56, 0.58, 0.58, 0.55), 4)
	_add_rect_visual(layer, portal_top_left + Vector2(-8.0, -3.0), Vector2(grid_size + 16.0, 6.0), Color(0.80, 0.81, 0.80), 4)
	_add_rect_visual(layer, portal_top_left + Vector2(-8.0, portal_height - 3.0), Vector2(grid_size + 16.0, 6.0), Color(0.72, 0.74, 0.73), 4)

	_add_retracted_blast_panel(layer, top_wall_position + Vector2(4.0, 18.0), false)
	_add_retracted_blast_panel(layer, bottom_wall_position + Vector2(4.0, 6.0), true)


func _add_side_room_blast_door(layer: Node, cell: Vector2i) -> void:
	var tile_position: Vector2 = grid_to_world(cell)
	_add_rect_visual(layer, tile_position + Vector2(4.0, 4.0), Vector2(grid_size - 8.0, grid_size - 8.0), Color(0.73, 0.75, 0.74), 1)
	_add_rect_visual(layer, tile_position + Vector2(8.0, 8.0), Vector2(grid_size - 16.0, grid_size - 16.0), Color(0.91, 0.92, 0.91), 2)
	_add_rect_visual(layer, tile_position + Vector2(11.0, 11.0), Vector2(grid_size - 22.0, 6.0), Color(1.0, 1.0, 1.0, 0.45), 3)
	_add_rect_visual(layer, tile_position + Vector2(12.0, grid_size * 0.5 - 1.0), Vector2(grid_size - 24.0, 2.0), Color(0.50, 0.52, 0.52), 3)


func _add_retracted_blast_panel(layer: Node, top_left: Vector2, flipped: bool) -> void:
	_add_rect_visual(layer, top_left, Vector2(grid_size - 8.0, 22.0), Color(0.71, 0.73, 0.72), 5)
	_add_rect_visual(layer, top_left + Vector2(3.0, 3.0), Vector2(grid_size - 14.0, 16.0), Color(0.93, 0.94, 0.93), 6)
	var shine_y: float = 5.0 if not flipped else 13.0
	_add_rect_visual(layer, top_left + Vector2(7.0, shine_y), Vector2(grid_size - 22.0, 3.0), Color(1.0, 1.0, 1.0, 0.52), 7)


func _add_rect_visual(layer: Node, top_left: Vector2, size: Vector2, color: Color, z_index: int) -> Polygon2D:
	var visual: Polygon2D = Polygon2D.new()
	visual.color = color
	visual.position = top_left
	visual.z_index = z_index
	visual.polygon = PackedVector2Array([
		Vector2.ZERO,
		Vector2(size.x, 0.0),
		size,
		Vector2(0.0, size.y)
	])
	layer.add_child(visual)
	return visual


func _add_fallback_rect(layer: Node, cell: Vector2i, z_index: int, color: Color) -> void:
	_add_rect_visual(layer, grid_to_world(cell), Vector2(grid_size, grid_size), color, z_index)


func _add_collision_rect(layer: Node, name: String, center: Vector2, size: Vector2) -> void:
	var body: StaticBody2D = StaticBody2D.new()
	body.name = name
	body.position = center
	body.collision_layer = 1
	body.collision_mask = 2
	layer.add_child(body)

	var collision: CollisionShape2D = CollisionShape2D.new()
	var shape: RectangleShape2D = RectangleShape2D.new()
	shape.size = size
	collision.shape = shape
	body.add_child(collision)


func _create_generated_layer(parent: Node2D, layer_name: String) -> Node:
	var base_layer: Node = _find_layer(parent, layer_name)
	var generated: Node2D = Node2D.new()
	generated.name = "Generated%s" % layer_name
	base_layer.add_child(generated)
	return generated


func _find_layer(parent: Node2D, layer_name: String) -> Node:
	var shell_root: Node = parent.get_node_or_null("TileMapLayers")
	if shell_root == null:
		return parent

	var layer: Node = shell_root.get_node_or_null(layer_name)
	if layer == null:
		layer = Node2D.new()
		layer.name = layer_name
		shell_root.add_child(layer)
	return layer


func _clear_generated_layers(parent: Node2D) -> void:
	var shell_root: Node = parent.get_node_or_null("TileMapLayers")
	if shell_root == null:
		return

	for layer_name in ["Floor", "WallsCollision", "Props", "Doors", "GameplayMarkers"]:
		var layer: Node = shell_root.get_node_or_null(layer_name)
		if layer == null:
			continue
		var generated: Node = layer.get_node_or_null("Generated%s" % layer_name)
		if generated == null:
			continue
		layer.remove_child(generated)
		generated.queue_free()


func _mark_walkable(cell: Vector2i) -> void:
	_walkable_cells[_cell_key(cell)] = cell


func _cell_key(cell: Vector2i) -> String:
	return "%d,%d" % [cell.x, cell.y]


func _array_to_vector2(value: Variant) -> Vector2:
	if typeof(value) != TYPE_ARRAY:
		return Vector2.ZERO
	var data: Array = value as Array
	if data.size() < 2:
		return Vector2.ZERO
	return Vector2(float(data[0]), float(data[1]))


func _array_to_vector2i(value: Variant) -> Vector2i:
	if typeof(value) != TYPE_ARRAY:
		return Vector2i.ZERO
	var data: Array = value as Array
	if data.size() < 2:
		return Vector2i.ZERO
	return Vector2i(int(data[0]), int(data[1]))


func _array_to_rect2i(value: Variant) -> Rect2i:
	if typeof(value) != TYPE_ARRAY:
		return Rect2i()
	var data: Array = value as Array
	if data.size() < 4:
		return Rect2i()
	return Rect2i(int(data[0]), int(data[1]), int(data[2]), int(data[3]))


func _region_for_prop_kind(kind: String) -> String:
	match kind:
		"chest":
			return "chest_basic"
		"console":
			return "console_basic"
		"reactor":
			return "reactor_basic"
		"medbay":
			return "medbay_basic"
		"navigator":
			return "navigator_basic"
		"light":
			return "light_basic"
	return ""


func _prop_blocks_movement(kind: String) -> bool:
	return kind in ["chest", "console", "reactor", "medbay", "navigator"]


func _collision_size_for_prop(kind: String) -> Vector2:
	match kind:
		"reactor", "medbay", "navigator":
			return Vector2(grid_size * 0.9, grid_size * 0.9)
		"console":
			return Vector2(grid_size * 0.8, grid_size * 0.8)
		"chest":
			return Vector2(grid_size * 0.9, grid_size * 0.55)
	return Vector2(grid_size * 0.8, grid_size * 0.8)


func _fallback_color(region_id: String) -> Color:
	if region_id.begins_with("wall"):
		return Color(0.92, 0.93, 0.92)
	if region_id.begins_with("door"):
		return Color(0.72, 0.74, 0.73)
	if region_id.begins_with("floor"):
		return Color(0.52, 0.54, 0.54)
	return Color(0.20, 0.45, 0.52)
