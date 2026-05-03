class_name TerminalInteractable
extends Area2D

@export var save_id: String = "ship_terminal"
@export var display_name: String = "Access terminal"
@export var grants_item: String = "access_card"

var activated: bool = false


func _ready() -> void:
	collision_layer = 4
	collision_mask = 0
	if get_node_or_null("CollisionShape2D") == null:
		var collision := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(40, 48)
		collision.shape = shape
		add_child(collision)
	if get_node_or_null("Visual") == null:
		var visual := Polygon2D.new()
		visual.name = "Visual"
		visual.color = Color(0.12, 0.78, 0.86, 1.0)
		visual.polygon = PackedVector2Array([
			Vector2(-20, -24),
			Vector2(20, -24),
			Vector2(20, 24),
			Vector2(-20, 24)
		])
		add_child(visual)


func get_interaction_prompt(_game_state: GameState) -> String:
	return "%s linked" % display_name if activated else "[E] Use %s" % display_name


func interact(game_state: GameState) -> String:
	if activated:
		return "%s already linked" % display_name

	activated = true
	game_state.add_item(grants_item)
	return "%s granted %s" % [display_name, grants_item]


func to_save_data() -> Dictionary:
	return {"activated": activated}


func apply_save_data(data: Dictionary) -> void:
	activated = bool(data.get("activated", activated))
