class_name HUD
extends CanvasLayer

var _objective_label: Label
var _time_label: Label
var _suspicion_label: Label
var _inventory_label: Label
var _prompt_label: Label
var _status_label: Label


func _ready() -> void:
	_create_labels()
	set_objective("Starship systems sandbox")
	set_time("06:00")
	set_suspicion(0.0)
	set_inventory({})
	set_prompt("")
	set_status("WASD/arrows move   E interact   C craft   F5 save   F9 load")


func set_objective(text: String) -> void:
	_objective_label.text = text


func set_time(text: String) -> void:
	_time_label.text = "Time %s" % text


func set_suspicion(value: float) -> void:
	var label := "LOW"
	if value >= 75.0:
		label = "ALERT"
	elif value >= 45.0:
		label = "SEARCH"
	elif value >= 20.0:
		label = "WATCHED"
	_suspicion_label.text = "Suspicion %03d%%  %s" % [int(round(value)), label]


func set_inventory(items: Dictionary) -> void:
	if items.is_empty():
		_inventory_label.text = "Inventory: empty"
		return

	var parts: Array[String] = []
	for item_id in items.keys():
		parts.append("%s x%d" % [String(item_id), int(items[item_id])])
	parts.sort()
	_inventory_label.text = "Inventory: " + ", ".join(parts)


func set_prompt(text: String) -> void:
	_prompt_label.text = text
	_prompt_label.visible = not text.is_empty()


func set_status(text: String) -> void:
	_status_label.text = text


func _create_labels() -> void:
	var root := Control.new()
	root.name = "Root"
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root)

	_objective_label = _make_label(Vector2(18, 16), 18, Color(0.90, 0.95, 1.0))
	root.add_child(_objective_label)

	_suspicion_label = _make_label(Vector2(470, 16), 18, Color(1.0, 0.76, 0.28))
	root.add_child(_suspicion_label)

	_time_label = _make_label(Vector2(1080, 16), 18, Color(0.70, 0.94, 1.0))
	root.add_child(_time_label)

	_inventory_label = _make_label(Vector2(18, 650), 16, Color(0.88, 0.92, 0.70))
	root.add_child(_inventory_label)

	_prompt_label = _make_label(Vector2(500, 650), 18, Color(1.0, 1.0, 1.0))
	root.add_child(_prompt_label)

	_status_label = _make_label(Vector2(18, 46), 14, Color(0.74, 0.84, 1.0))
	root.add_child(_status_label)


func _make_label(label_position: Vector2, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.position = label_position
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	return label
