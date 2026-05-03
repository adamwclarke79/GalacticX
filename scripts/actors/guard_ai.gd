class_name GuardAI
extends CharacterBody2D

signal suspicion_requested(amount: float)

@export var character_id: String = "stormtrooper_gun"
@export var patrol_speed: float = 115.0
@export var pause_seconds: float = 0.6
@export var detection_radius: float = 128.0
@export var suspicion_per_second: float = 34.0

@onready var _animator: DirectionalAnimation = $DirectionalAnimation
@onready var _detection_area: Area2D = $DetectionArea

var patrol_points: Array[Vector2] = []
var target_player: Node2D
var facing_direction: String = "south"
var _patrol_index: int = 0
var _pause_left: float = 0.0


func _ready() -> void:
	_animator.set_character(character_id)
	_update_detection_shape()


func _physics_process(delta: float) -> void:
	_patrol(delta)
	_detect_player(delta)


func set_patrol_points(points: Array[Vector2]) -> void:
	patrol_points = points
	_patrol_index = 0


func set_target_player(player: Node2D) -> void:
	target_player = player


func to_save_data() -> Dictionary:
	return {
		"position": [global_position.x, global_position.y],
		"facing": facing_direction,
		"patrol_index": _patrol_index
	}


func apply_save_data(data: Dictionary) -> void:
	if data.get("position", []) is Array:
		var position_data: Array = data["position"] as Array
		if position_data.size() >= 2:
			global_position = Vector2(float(position_data[0]), float(position_data[1]))
	facing_direction = String(data.get("facing", facing_direction))
	_patrol_index = int(data.get("patrol_index", _patrol_index))


func _patrol(delta: float) -> void:
	if patrol_points.is_empty():
		velocity = Vector2.ZERO
		_animator.tick("idle", facing_direction, delta)
		return

	if _pause_left > 0.0:
		_pause_left -= delta
		velocity = Vector2.ZERO
		_animator.tick("idle", facing_direction, delta)
		return

	var target: Vector2 = patrol_points[_patrol_index]
	var to_target: Vector2 = target - global_position
	if to_target.length() <= 6.0:
		global_position = target
		_patrol_index = (_patrol_index + 1) % patrol_points.size()
		_pause_left = pause_seconds
		velocity = Vector2.ZERO
		_animator.tick("idle", facing_direction, delta)
		return

	var direction: Vector2 = to_target.normalized()
	velocity = direction * patrol_speed
	move_and_slide()
	facing_direction = DirectionalAnimation.direction_from_vector(direction, facing_direction)
	_animator.tick("walking", facing_direction, delta)


func _detect_player(delta: float) -> void:
	if target_player == null:
		return

	var distance: float = global_position.distance_to(target_player.global_position)
	if distance > detection_radius:
		return

	var suspicion_scale: float = 1.0 - clampf(distance / detection_radius, 0.0, 1.0)
	suspicion_requested.emit(suspicion_per_second * maxf(suspicion_scale, 0.25) * delta)


func _update_detection_shape() -> void:
	if _detection_area == null:
		return
	var collision: CollisionShape2D = _detection_area.get_node_or_null("CollisionShape2D") as CollisionShape2D
	if collision == null:
		return
	var shape: CircleShape2D = CircleShape2D.new()
	shape.radius = detection_radius
	collision.shape = shape
