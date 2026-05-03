class_name PlayerController
extends CharacterBody2D

signal interact_pressed

@export var character_id: String = "stormtrooper_gun"
@export var move_speed: float = 210.0
@export var acceleration: float = 1600.0
@export var deceleration: float = 1800.0
@export var interaction_offset: float = 34.0

@onready var _animator: DirectionalAnimation = $DirectionalAnimation
@onready var _interaction_area: Area2D = $InteractionArea

var facing_direction: String = "south"
var _nearby_interactables: Array[Node] = []


func _ready() -> void:
	_animator.set_character(character_id)
	_interaction_area.area_entered.connect(_on_interaction_area_entered)
	_interaction_area.area_exited.connect(_on_interaction_area_exited)
	_update_interaction_area()


func _physics_process(delta: float) -> void:
	var input_vector := Vector2(
		Input.get_axis("move_left", "move_right"),
		Input.get_axis("move_up", "move_down")
	)

	if input_vector.length_squared() > 1.0:
		input_vector = input_vector.normalized()

	var target_velocity := input_vector * move_speed
	var rate := acceleration if input_vector.length_squared() > 0.0001 else deceleration
	velocity = velocity.move_toward(target_velocity, rate * delta)
	move_and_slide()

	if input_vector.length_squared() > 0.0001:
		facing_direction = DirectionalAnimation.direction_from_vector(input_vector, facing_direction)
	_update_interaction_area()

	var state := "walking" if velocity.length_squared() > 4.0 else "idle"
	_animator.tick(state, facing_direction, delta)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact"):
		interact_pressed.emit()


func reset_to(spawn_position: Vector2) -> void:
	global_position = spawn_position
	velocity = Vector2.ZERO
	facing_direction = "south"
	_update_interaction_area()


func apply_save_data(data: Dictionary) -> void:
	if data.get("position", []) is Array:
		var position_data: Array = data["position"] as Array
		if position_data.size() >= 2:
			global_position = Vector2(float(position_data[0]), float(position_data[1]))
	facing_direction = String(data.get("facing", facing_direction))
	_update_interaction_area()


func to_save_data() -> Dictionary:
	return {
		"position": [global_position.x, global_position.y],
		"facing": facing_direction
	}


func get_current_interactable() -> Node:
	var best: Node = null
	var best_distance := INF

	for candidate in _nearby_interactables:
		if not is_instance_valid(candidate) or not candidate.has_method("interact"):
			continue
		var candidate_2d := candidate as Node2D
		if candidate_2d == null:
			continue
		var distance := global_position.distance_squared_to(candidate_2d.global_position)
		if distance < best_distance:
			best = candidate
			best_distance = distance

	return best


func _update_interaction_area() -> void:
	if _interaction_area == null:
		return

	var direction_vector := _direction_to_vector(facing_direction)
	_interaction_area.position = direction_vector * interaction_offset


func _direction_to_vector(direction: String) -> Vector2:
	match direction:
		"north":
			return Vector2.UP
		"south":
			return Vector2.DOWN
		"east":
			return Vector2.RIGHT
		"west":
			return Vector2.LEFT
		"north-east":
			return Vector2(1, -1).normalized()
		"north-west":
			return Vector2(-1, -1).normalized()
		"south-east":
			return Vector2(1, 1).normalized()
		"south-west":
			return Vector2(-1, 1).normalized()
	return Vector2.DOWN


func _on_interaction_area_entered(area: Area2D) -> void:
	if area.has_method("interact") and not _nearby_interactables.has(area):
		_nearby_interactables.append(area)


func _on_interaction_area_exited(area: Area2D) -> void:
	_nearby_interactables.erase(area)
