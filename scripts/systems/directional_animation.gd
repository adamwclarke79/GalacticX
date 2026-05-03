class_name DirectionalAnimation
extends Node

const DIRECTIONS: Array[String] = [
	"east",
	"south-east",
	"south",
	"south-west",
	"west",
	"north-west",
	"north",
	"north-east"
]

@export var character_id: String = "stormtrooper_gun"
@export var default_state: String = "walking"
@export var frame_duration: float = 0.10
@export var sprite_path: NodePath = NodePath("../Sprite2D")

var _sprite: Sprite2D
var _cache: Dictionary = {}
var _current_state: String = ""
var _current_direction: String = "south"
var _frame_index: int = 0
var _frame_timer: float = 0.0
var _placeholder_texture: Texture2D


static func direction_from_vector(vector: Vector2, fallback: String = "south") -> String:
	if vector.length_squared() <= 0.0001:
		return fallback

	var angle := rad_to_deg(vector.angle())
	if angle < 0.0:
		angle += 360.0

	var index := int(floor((angle + 22.5) / 45.0)) % DIRECTIONS.size()
	return DIRECTIONS[index]


func _ready() -> void:
	_sprite = get_node_or_null(sprite_path) as Sprite2D
	_placeholder_texture = _create_placeholder_texture()
	set_facing(_current_direction)


func set_character(next_character_id: String) -> void:
	if character_id == next_character_id:
		return

	character_id = next_character_id
	_cache.clear()
	_frame_index = 0
	_frame_timer = 0.0
	set_facing(_current_direction)


func tick(state: String, direction: String, delta: float) -> void:
	if _sprite == null:
		return

	var normalized_direction: String = _normalize_direction(direction)
	var normalized_state: String = state if not state.is_empty() else default_state
	var frames: Array[Texture2D] = _get_frames(normalized_state, normalized_direction)

	if normalized_state != _current_state or normalized_direction != _current_direction:
		_current_state = normalized_state
		_current_direction = normalized_direction
		_frame_index = 0
		_frame_timer = 0.0

	if frames.is_empty():
		_sprite.texture = _placeholder_texture
		return

	if frames.size() > 1:
		_frame_timer += delta
		while _frame_timer >= frame_duration:
			_frame_timer -= frame_duration
			_frame_index = (_frame_index + 1) % frames.size()
	else:
		_frame_index = 0

	var texture: Texture2D = frames[_frame_index] as Texture2D
	if texture != null:
		_sprite.texture = texture


func set_facing(direction: String) -> void:
	tick(default_state, direction, 0.0)


func _get_frames(state: String, direction: String) -> Array[Texture2D]:
	var cache_key: String = "%s/%s/%s" % [character_id, state, direction]
	if _cache.has(cache_key):
		return _cache[cache_key]

	var frames: Array[Texture2D] = _load_animation_frames(state, direction)
	if frames.is_empty() and state != default_state:
		frames = _load_animation_frames(default_state, direction)
	if frames.is_empty():
		var facing_texture: Texture2D = _load_direction_texture(direction)
		if facing_texture != null:
			frames.append(facing_texture)
	if frames.is_empty() and _placeholder_texture != null:
		frames.append(_placeholder_texture)

	_cache[cache_key] = frames
	return frames


func _load_animation_frames(state: String, direction: String) -> Array[Texture2D]:
	var folder: String = "res://assets/sprites/characters/%s/animations/%s/%s" % [character_id, state, direction]
	var dir: DirAccess = DirAccess.open(folder)
	var frames: Array[Texture2D] = []
	if dir == null:
		return frames

	var file_names: Array[String] = []
	dir.list_dir_begin()
	var file_name: String = dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.begins_with("frame_") and file_name.ends_with(".png"):
			file_names.append(file_name)
		file_name = dir.get_next()
	dir.list_dir_end()

	file_names.sort()
	for sorted_file_name in file_names:
		var path: String = "%s/%s" % [folder, sorted_file_name]
		var texture: Texture2D = load(path) as Texture2D
		if texture != null:
			frames.append(texture)

	return frames


func _load_direction_texture(direction: String) -> Texture2D:
	var paths: Array[String] = [
		"res://assets/sprites/characters/%s/rotations/%s.png" % [character_id, direction],
		"res://assets/sprites/characters/%s/%s.png" % [character_id, direction]
	]

	for path in paths:
		if ResourceLoader.exists(path):
			var texture: Texture2D = load(path) as Texture2D
			if texture != null:
				return texture
	return null


func _normalize_direction(direction: String) -> String:
	if DIRECTIONS.has(direction):
		return direction
	return "south"


func _create_placeholder_texture() -> Texture2D:
	var image: Image = Image.create(32, 32, false, Image.FORMAT_RGBA8)
	image.fill(Color(0.95, 0.25, 0.85, 1.0))
	for x in range(0, 32):
		image.set_pixel(x, 0, Color.BLACK)
		image.set_pixel(x, 31, Color.BLACK)
	for y in range(0, 32):
		image.set_pixel(0, y, Color.BLACK)
		image.set_pixel(31, y, Color.BLACK)
	return ImageTexture.create_from_image(image)
