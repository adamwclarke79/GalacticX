class_name ContainerInteractable
extends Area2D

@export var save_id: String = "container_parts"
@export var display_name: String = "Storage crate"
@export var loot_items: Array[String] = ["battery", "wire", "scrap_metal"]

var looted: bool = false


func _ready() -> void:
	collision_layer = 4
	collision_mask = 0
	if get_node_or_null("CollisionShape2D") == null:
		var collision := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(54, 38)
		collision.shape = shape
		add_child(collision)
	if get_node_or_null("Visual") == null:
		var visual := Polygon2D.new()
		visual.name = "Visual"
		visual.color = Color(0.58, 0.46, 0.22, 1.0)
		visual.polygon = PackedVector2Array([
			Vector2(-27, -19),
			Vector2(27, -19),
			Vector2(27, 19),
			Vector2(-27, 19)
		])
		add_child(visual)


func get_interaction_prompt(_game_state: GameState) -> String:
	return "[E] Search %s" % display_name if not looted else "%s empty" % display_name


func interact(game_state: GameState) -> String:
	if looted:
		return "%s is empty" % display_name

	looted = true
	for item_id in loot_items:
		game_state.add_item(item_id)
	return "Recovered parts from %s" % display_name


func to_save_data() -> Dictionary:
	return {"looted": looted}


func apply_save_data(data: Dictionary) -> void:
	looted = bool(data.get("looted", looted))
