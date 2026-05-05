class_name PaintedTiledMapLoader
extends RefCounted

const SUPPORTED_FORMAT := "galacticx_tiled_map_v1"
const DEFAULT_MAP_PATH := "res://data/maps/starship_sector_painted.json"
const GENERATED_LAYER_NAMES := ["Floor", "WallsCollision", "Props", "Doors", "GameplayMarkers", "Labels"]

var map_data: Dictionary = {}
var _markers: Array[Dictionary] = []
var _texture_cache: Dictionary = {}


func load_into(parent: Node2D, map_path: String = DEFAULT_MAP_PATH) -> bool:
	_clear_state()
	_clear_generated_layers(parent)

	if not _load_map(map_path):
		return false

	for layer_value in map_data.get("layers", []):
		if typeof(layer_value) != TYPE_DICTIONARY:
			continue
		var layer_data: Dictionary = layer_value as Dictionary
		if not bool(layer_data.get("visible", true)):
			continue
		var layer_name := String(layer_data.get("name", "Props"))
		var generated_layer := _create_generated_layer(parent, layer_name)
		for item_value in layer_data.get("items", []):
			if typeof(item_value) != TYPE_DICTIONARY:
				continue
			_add_tile_item(generated_layer, item_value as Dictionary, int(layer_data.get("z_index", 0)))

	_add_collisions(parent)
	_collect_markers()
	_add_labels(parent)
	return true


func marker_position(name_or_kind: String, fallback: Vector2) -> Vector2:
	for marker in _markers:
		if _marker_matches(marker, name_or_kind):
			return _marker_center(marker)
	return fallback


func marker_position_any(names_or_kinds: Array[String], fallback: Vector2) -> Vector2:
	for key in names_or_kinds:
		for marker in _markers:
			if _marker_matches(marker, key):
				return _marker_center(marker)
	return fallback


func marker_positions(name_or_kind: String) -> Array[Vector2]:
	var positions: Array[Vector2] = []
	for marker in _markers:
		if _marker_matches(marker, name_or_kind):
			positions.append(_marker_center(marker))
	return positions


func _clear_state() -> void:
	map_data.clear()
	_markers.clear()
	_texture_cache.clear()


func _load_map(map_path: String) -> bool:
	if not FileAccess.file_exists(map_path):
		return false

	var file := FileAccess.open(map_path, FileAccess.READ)
	if file == null:
		push_warning("Unable to open painted Tiled map: %s" % map_path)
		return false

	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("Painted Tiled map is not a JSON object: %s" % map_path)
		return false

	map_data = parsed as Dictionary
	if String(map_data.get("format", "")) != SUPPORTED_FORMAT:
		push_warning("Unsupported painted Tiled map format: %s" % map_data.get("format", ""))
		return false
	return true


func _add_tile_item(layer: Node, item: Dictionary, default_z_index: int) -> void:
	var texture := _texture_for_item(item)
	if texture == null:
		return

	var sprite := Sprite2D.new()
	sprite.name = String(item.get("id", "TiledTile"))
	sprite.texture = texture
	sprite.centered = false
	sprite.position = _array_to_vector2(item.get("position", [0, 0]))
	sprite.rotation_degrees = float(item.get("rotation", 0.0))
	sprite.z_index = int(item.get("z_index", default_z_index))
	sprite.modulate = Color(1.0, 1.0, 1.0, float(item.get("opacity", 1.0)))

	var atlas := _array_to_rect2(item.get("atlas", []))
	var size := _array_to_vector2(item.get("size", [atlas.size.x, atlas.size.y]))
	if atlas.size.x > 0.0 and atlas.size.y > 0.0:
		sprite.scale = Vector2(size.x / atlas.size.x, size.y / atlas.size.y)

	var flip_data: Dictionary = item.get("flip", {}) as Dictionary
	sprite.flip_h = bool(flip_data.get("horizontal", false))
	sprite.flip_v = bool(flip_data.get("vertical", false))
	if bool(flip_data.get("diagonal", false)):
		sprite.rotation_degrees += 90.0

	layer.add_child(sprite)


func _texture_for_item(item: Dictionary) -> Texture2D:
	var source_path := String(item.get("source", ""))
	if source_path == "":
		return null
	var atlas_rect := _array_to_rect2(item.get("atlas", []))
	if atlas_rect.size.x <= 0.0 or atlas_rect.size.y <= 0.0:
		return null

	var cache_key := "%s:%s,%s,%s,%s" % [
		source_path,
		atlas_rect.position.x,
		atlas_rect.position.y,
		atlas_rect.size.x,
		atlas_rect.size.y
	]
	if _texture_cache.has(cache_key):
		return _texture_cache[cache_key] as Texture2D
	if not ResourceLoader.exists(source_path):
		push_warning("Painted map texture missing: %s" % source_path)
		return null

	var source_texture := load(source_path) as Texture2D
	if source_texture == null:
		return null

	var atlas := AtlasTexture.new()
	atlas.atlas = source_texture
	atlas.region = atlas_rect
	_texture_cache[cache_key] = atlas
	return atlas


func _add_collisions(parent: Node2D) -> void:
	var collision_layer := _create_generated_layer(parent, "WallsCollision")
	for collision_value in map_data.get("collisions", []):
		if typeof(collision_value) != TYPE_DICTIONARY:
			continue
		var collision_data: Dictionary = collision_value as Dictionary
		var shape := String(collision_data.get("shape", "rectangle"))
		if shape == "polygon" or shape == "polyline":
			_add_collision_polygon(collision_layer, collision_data)
		else:
			_add_collision_rect(collision_layer, collision_data)


func _add_collision_rect(layer: Node, collision_data: Dictionary) -> void:
	var position := _array_to_vector2(collision_data.get("position", [0, 0]))
	var size := _array_to_vector2(collision_data.get("size", [0, 0]))
	if size.x <= 0.0 or size.y <= 0.0:
		return

	var body := StaticBody2D.new()
	body.name = _collision_name(collision_data)
	body.position = position + size * 0.5
	body.rotation_degrees = float(collision_data.get("rotation", 0.0))
	body.collision_layer = 1
	body.collision_mask = 2
	layer.add_child(body)

	var collision := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = size
	collision.shape = rect
	body.add_child(collision)


func _add_collision_polygon(layer: Node, collision_data: Dictionary) -> void:
	var points := PackedVector2Array()
	for point_value in collision_data.get("points", []):
		points.append(_array_to_vector2(point_value))
	if points.size() < 3:
		return

	var body := StaticBody2D.new()
	body.name = _collision_name(collision_data)
	body.position = _array_to_vector2(collision_data.get("position", [0, 0]))
	body.rotation_degrees = float(collision_data.get("rotation", 0.0))
	body.collision_layer = 1
	body.collision_mask = 2
	layer.add_child(body)

	var collision := CollisionPolygon2D.new()
	collision.polygon = points
	body.add_child(collision)


func _collision_name(collision_data: Dictionary) -> String:
	var collision_name := String(collision_data.get("name", ""))
	if collision_name != "":
		return collision_name
	return "%sCollision" % String(collision_data.get("kind", "Tiled"))


func _collect_markers() -> void:
	for marker_value in map_data.get("markers", []):
		if typeof(marker_value) != TYPE_DICTIONARY:
			continue
		_markers.append(marker_value as Dictionary)


func _add_labels(parent: Node2D) -> void:
	var label_layer := _create_generated_layer(parent, "Labels")
	for marker in _markers:
		if String(marker.get("kind", "")) != "label":
			continue
		var text := String(marker.get("text", ""))
		if text == "":
			var properties: Dictionary = marker.get("properties", {}) as Dictionary
			text = String(properties.get("text", marker.get("name", "")))
		if text == "":
			continue

		var label := Label.new()
		label.text = text
		label.position = _array_to_vector2(marker.get("position", [0, 0]))
		label.rotation_degrees = float(marker.get("rotation", 0.0))
		label.z_index = 20
		label.add_theme_font_size_override("font_size", 12)
		label.add_theme_color_override("font_color", Color(0.76, 0.86, 0.95))
		label_layer.add_child(label)


func _marker_matches(marker: Dictionary, name_or_kind: String) -> bool:
	return String(marker.get("name", "")) == name_or_kind or String(marker.get("kind", "")) == name_or_kind


func _marker_center(marker: Dictionary) -> Vector2:
	var position := _array_to_vector2(marker.get("position", [0, 0]))
	var size := _array_to_vector2(marker.get("size", [0, 0]))
	if bool(marker.get("point", false)) or size == Vector2.ZERO:
		return position
	return position + size * 0.5


func _create_generated_layer(parent: Node2D, layer_name: String) -> Node:
	var base_layer := _find_layer(parent, layer_name)
	var generated := base_layer.get_node_or_null("Generated%s" % layer_name)
	if generated != null:
		return generated

	generated = Node2D.new()
	generated.name = "Generated%s" % layer_name
	base_layer.add_child(generated)
	return generated


func _find_layer(parent: Node2D, layer_name: String) -> Node:
	var shell_root := parent.get_node_or_null("TileMapLayers")
	if shell_root == null:
		return parent

	var layer := shell_root.get_node_or_null(layer_name)
	if layer == null:
		layer = Node2D.new()
		layer.name = layer_name
		shell_root.add_child(layer)
	return layer


func _clear_generated_layers(parent: Node2D) -> void:
	var shell_root := parent.get_node_or_null("TileMapLayers")
	if shell_root == null:
		return

	for layer_name in GENERATED_LAYER_NAMES:
		var layer := shell_root.get_node_or_null(layer_name)
		if layer == null:
			continue
		var generated := layer.get_node_or_null("Generated%s" % layer_name)
		if generated == null:
			continue
		layer.remove_child(generated)
		generated.queue_free()


func _array_to_vector2(value: Variant) -> Vector2:
	if typeof(value) != TYPE_ARRAY:
		return Vector2.ZERO
	var data: Array = value as Array
	if data.size() < 2:
		return Vector2.ZERO
	return Vector2(float(data[0]), float(data[1]))


func _array_to_rect2(value: Variant) -> Rect2:
	if typeof(value) != TYPE_ARRAY:
		return Rect2()
	var data: Array = value as Array
	if data.size() < 4:
		return Rect2()
	return Rect2(
		Vector2(float(data[0]), float(data[1])),
		Vector2(float(data[2]), float(data[3]))
	)
