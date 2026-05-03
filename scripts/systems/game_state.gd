class_name GameState
extends Node

signal inventory_changed(items: Dictionary)
signal suspicion_changed(value: float)
signal time_changed(formatted_time: String)
signal status_changed(message: String)
signal alert_triggered

@export var suspicion_decay_per_second: float = 4.0
@export var suspicion_threshold: float = 100.0

var inventory: InventorySystem
var crafting: CraftingSystem
var time_system: TimeSystem
var suspicion: float = 0.0
var _alert_active: bool = false


func _ready() -> void:
	inventory = InventorySystem.new()
	inventory.name = "InventorySystem"
	add_child(inventory)
	inventory.inventory_changed.connect(_on_inventory_changed)

	crafting = CraftingSystem.new()
	crafting.name = "CraftingSystem"
	add_child(crafting)

	time_system = TimeSystem.new()
	time_system.name = "TimeSystem"
	add_child(time_system)
	time_system.time_changed.connect(_on_time_changed)


func _process(delta: float) -> void:
	if suspicion <= 0.0:
		return

	set_suspicion(suspicion - suspicion_decay_per_second * delta)


func add_item(item_id: String, amount: int = 1) -> void:
	inventory.add_item(item_id, amount)
	status_changed.emit("Picked up %s" % item_id)


func craft_debug_item() -> bool:
	if crafting.craft("hack_tool", inventory):
		status_changed.emit("Crafted hack_tool")
		return true

	status_changed.emit("Missing parts for hack_tool")
	return false


func add_suspicion(amount: float) -> void:
	set_suspicion(suspicion + amount)


func set_suspicion(value: float) -> void:
	var next_value := clampf(value, 0.0, suspicion_threshold)
	if is_equal_approx(next_value, suspicion):
		return

	suspicion = next_value
	suspicion_changed.emit(suspicion)

	if suspicion >= suspicion_threshold and not _alert_active:
		_alert_active = true
		status_changed.emit("Alert triggered")
		alert_triggered.emit()
	elif suspicion < suspicion_threshold * 0.6:
		_alert_active = false


func set_status(message: String) -> void:
	status_changed.emit(message)


func to_save_data() -> Dictionary:
	return {
		"inventory": inventory.to_save_data(),
		"suspicion": suspicion,
		"time_minutes": time_system.current_minutes
	}


func apply_save_data(data: Dictionary) -> void:
	if data.has("inventory") and data["inventory"] is Dictionary:
		inventory.apply_save_data(data["inventory"])
	set_suspicion(float(data.get("suspicion", 0.0)))
	time_system.set_minutes(int(data.get("time_minutes", time_system.current_minutes)))
	status_changed.emit("Loaded sandbox state")


func _on_inventory_changed(items: Dictionary) -> void:
	inventory_changed.emit(items)


func _on_time_changed(_minutes: int, formatted_time: String) -> void:
	time_changed.emit(formatted_time)
