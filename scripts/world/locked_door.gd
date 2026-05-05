class_name LockedDoor
extends Area2D

const DOOR_SHEET := "res://assets/tilesets/spaceship_tileset/Spaceship Tileset/characters/!Spaceship_door.png"
const DOOR_FRAME_OPEN := [288.0, 0.0, 48.0, 96.0]
const DOOR_FRAME_PARTIAL_1 := [288.0, 96.0, 48.0, 96.0]
const DOOR_FRAME_PARTIAL_2 := [288.0, 192.0, 48.0, 96.0]
const DOOR_FRAME_CLOSED := [288.0, 288.0, 48.0, 96.0]

@export var save_id: String = "blast_door_alpha"
@export var display_name: String = "Blast door"
@export var required_items: Array[String] = ["hack_tool", "access_card"]

var unlocked: bool = false
var open: bool = false
var _blocker: StaticBody2D
var _border: Polygon2D
var _visual: Polygon2D
var _right_visual: Polygon2D
var _door_sprite: Sprite2D
var _white_door_material: ShaderMaterial
var _door_textures: Dictionary = {}


func _ready() -> void:
	collision_layer = 4
	collision_mask = 0
	_ensure_nodes()
	_update_state()


func get_interaction_prompt(_game_state: GameState) -> String:
	return "%s open" % display_name if open else "[E] Open %s" % display_name


func interact(game_state: GameState) -> String:
	if open:
		return "%s already open" % display_name

	for item_id in required_items:
		if game_state.inventory.has_item(item_id):
				unlocked = true
				open = true
				_update_state()
				_play_open_animation()
				return "%s opened with %s" % [display_name, item_id]

	return "%s requires hack_tool or access_card" % display_name


func to_save_data() -> Dictionary:
	return {
		"unlocked": unlocked,
		"open": open
	}


func apply_save_data(data: Dictionary) -> void:
	unlocked = bool(data.get("unlocked", unlocked))
	open = bool(data.get("open", open))
	_update_state()


func _ensure_nodes() -> void:
	if get_node_or_null("CollisionShape2D") == null:
		var area_collision := CollisionShape2D.new()
		var area_shape := RectangleShape2D.new()
		area_shape.size = Vector2(72, 44)
		area_collision.shape = area_shape
		add_child(area_collision)

	_blocker = get_node_or_null("Blocker") as StaticBody2D
	if _blocker == null:
		_blocker = StaticBody2D.new()
		_blocker.name = "Blocker"
		_blocker.collision_layer = 1
		_blocker.collision_mask = 2
		add_child(_blocker)

	if _blocker.get_node_or_null("CollisionShape2D") == null:
		var block_collision := CollisionShape2D.new()
		var block_shape := RectangleShape2D.new()
		block_shape.size = Vector2(72, 26)
		block_collision.shape = block_shape
		_blocker.add_child(block_collision)

	_visual = get_node_or_null("Visual") as Polygon2D
	if _visual == null:
		_visual = Polygon2D.new()
		_visual.name = "Visual"
		add_child(_visual)
	_visual.z_index = 1

	_border = get_node_or_null("Border") as Polygon2D
	if _border == null:
		_border = Polygon2D.new()
		_border.name = "Border"
		add_child(_border)
	_border.z_index = 0

	_right_visual = get_node_or_null("RightVisual") as Polygon2D
	if _right_visual == null:
		_right_visual = Polygon2D.new()
		_right_visual.name = "RightVisual"
		add_child(_right_visual)
	_right_visual.z_index = 1

	_door_sprite = get_node_or_null("DoorSprite") as Sprite2D
	if _door_sprite == null:
		_door_sprite = Sprite2D.new()
		_door_sprite.name = "DoorSprite"
		add_child(_door_sprite)
	_door_sprite.centered = false
	_door_sprite.position = Vector2(-24.0, -48.0)
	_door_sprite.z_index = 4
	_door_sprite.material = _get_white_door_material()


func _update_state() -> void:
	if _blocker != null:
		_blocker.process_mode = Node.PROCESS_MODE_DISABLED if open else Node.PROCESS_MODE_INHERIT
		var collision: CollisionShape2D = _blocker.get_node_or_null("CollisionShape2D") as CollisionShape2D
		if collision != null:
			collision.disabled = open
	if _apply_sprite_visual():
		return

	if _visual != null:
		_border.visible = true
		_visual.visible = true
		if open:
			_set_rect_polygon(_border, Rect2(Vector2(-42, -18), Vector2(84, 36)))
			_border.color = Color(0.02, 0.025, 0.03, 1.0)
			_set_rect_polygon(_visual, Rect2(Vector2(-40, -15), Vector2(20, 30)))
			_visual.color = Color(0.94, 0.99, 1.0, 1.0)
			_set_rect_polygon(_right_visual, Rect2(Vector2(20, -15), Vector2(20, 30)))
			_right_visual.color = Color(0.94, 0.99, 1.0, 1.0)
			_right_visual.visible = true
		else:
			_set_rect_polygon(_border, Rect2(Vector2(-42, -18), Vector2(84, 36)))
			_border.color = Color(0.02, 0.025, 0.03, 1.0)
			_set_rect_polygon(_visual, Rect2(Vector2(-36, -14), Vector2(72, 28)))
			_visual.color = Color(0.94, 0.99, 1.0, 1.0)
			_set_rect_polygon(_right_visual, Rect2(Vector2.ZERO, Vector2.ZERO))
			_right_visual.visible = false


func _apply_sprite_visual() -> bool:
	if _door_sprite == null:
		return false

	var texture: Texture2D = _make_door_frame_texture(DOOR_FRAME_OPEN if open else DOOR_FRAME_CLOSED)
	if texture == null:
		_door_sprite.visible = false
		return false

	_door_sprite.texture = texture
	_door_sprite.visible = true
	if _border != null:
		_border.visible = false
	if _visual != null:
		_visual.visible = false
	if _right_visual != null:
		_right_visual.visible = false
	return true


func _play_open_animation() -> void:
	if _door_sprite == null:
		return

	for frame in [DOOR_FRAME_PARTIAL_2, DOOR_FRAME_PARTIAL_1, DOOR_FRAME_OPEN]:
		var texture: Texture2D = _make_door_frame_texture(frame)
		if texture != null:
			_door_sprite.texture = texture
		await get_tree().create_timer(0.07).timeout
	_apply_sprite_visual()


func _make_door_frame_texture(region_values: Array) -> Texture2D:
	var key := "%s,%s" % [region_values[0], region_values[1]]
	if _door_textures.has(key):
		return _door_textures[key] as Texture2D
	if not ResourceLoader.exists(DOOR_SHEET):
		return null

	var source_texture := load(DOOR_SHEET) as Texture2D
	if source_texture == null:
		return null

	var atlas := AtlasTexture.new()
	atlas.atlas = source_texture
	atlas.region = Rect2(
		Vector2(float(region_values[0]), float(region_values[1])),
		Vector2(float(region_values[2]), float(region_values[3]))
	)
	_door_textures[key] = atlas
	return atlas


func _get_white_door_material() -> ShaderMaterial:
	if _white_door_material != null:
		return _white_door_material

	var shader := Shader.new()
	shader.code = "shader_type canvas_item;\nvoid fragment() {\n\tvec4 base = texture(TEXTURE, UV);\n\tfloat shade = dot(base.rgb, vec3(0.299, 0.587, 0.114));\n\tfloat panel = smoothstep(0.08, 0.92, shade);\n\tvec3 color = mix(vec3(0.04, 0.045, 0.05), vec3(1.0), panel);\n\tCOLOR = vec4(color, base.a);\n}\n"

	_white_door_material = ShaderMaterial.new()
	_white_door_material.shader = shader
	return _white_door_material


func _set_rect_polygon(polygon: Polygon2D, rect: Rect2) -> void:
	if polygon == null:
		return
	polygon.polygon = PackedVector2Array([
		rect.position,
		rect.position + Vector2(rect.size.x, 0.0),
		rect.position + rect.size,
		rect.position + Vector2(0.0, rect.size.y)
	])
