class_name InventorySystem
extends Node

signal inventory_changed(items: Dictionary)

var _items: Dictionary = {}


func add_item(item_id: String, amount: int = 1) -> void:
	if item_id.is_empty() or amount <= 0:
		return

	_items[item_id] = get_item_count(item_id) + amount
	inventory_changed.emit(get_items())


func remove_item(item_id: String, amount: int = 1) -> bool:
	if not has_item(item_id, amount):
		return false

	var next_count := get_item_count(item_id) - amount
	if next_count <= 0:
		_items.erase(item_id)
	else:
		_items[item_id] = next_count
	inventory_changed.emit(get_items())
	return true


func remove_items(requirements: Dictionary) -> bool:
	for item_id in requirements.keys():
		if not has_item(String(item_id), int(requirements[item_id])):
			return false

	for item_id in requirements.keys():
		remove_item(String(item_id), int(requirements[item_id]))
	return true


func has_item(item_id: String, amount: int = 1) -> bool:
	return get_item_count(item_id) >= amount


func get_item_count(item_id: String) -> int:
	return int(_items.get(item_id, 0))


func get_items() -> Dictionary:
	return _items.duplicate(true)


func clear() -> void:
	_items.clear()
	inventory_changed.emit(get_items())


func to_save_data() -> Dictionary:
	return get_items()


func apply_save_data(data: Dictionary) -> void:
	_items.clear()
	for item_id in data.keys():
		var count := int(data[item_id])
		if count > 0:
			_items[String(item_id)] = count
	inventory_changed.emit(get_items())
