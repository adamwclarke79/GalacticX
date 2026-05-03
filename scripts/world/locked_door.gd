class_name LockedDoor
extends Area2D

@export var save_id: String = "blast_door_alpha"
@export var display_name: String = "Blast door"
@export var required_items: Array[String] = ["hack_tool", "access_card"]

var unlocked: bool = false
var open: bool = false
var _blocker: StaticBody2D
var _border: Polygon2D
var _visual: Polygon2D
var _right_visual: Polygon2D


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


func _update_state() -> void:
	if _blocker != null:
		_blocker.process_mode = Node.PROCESS_MODE_DISABLED if open else Node.PROCESS_MODE_INHERIT
		var collision: CollisionShape2D = _blocker.get_node_or_null("CollisionShape2D") as CollisionShape2D
		if collision != null:
			collision.disabled = open
	if _visual != null:
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


func _set_rect_polygon(polygon: Polygon2D, rect: Rect2) -> void:
	if polygon == null:
		return
	polygon.polygon = PackedVector2Array([
		rect.position,
		rect.position + Vector2(rect.size.x, 0.0),
		rect.position + rect.size,
		rect.position + Vector2(0.0, rect.size.y)
	])
