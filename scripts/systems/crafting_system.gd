class_name CraftingSystem
extends Node

const DEFAULT_RECIPES: Dictionary = {
	"hack_tool": {
		"ingredients": {
			"battery": 1,
			"wire": 1,
			"scrap_metal": 1
		},
		"output": "hack_tool",
		"amount": 1
	}
}

@export var recipes_path: String = "res://data/recipes.json"

var _recipes: Dictionary = {}


func _ready() -> void:
	load_recipes()


func load_recipes() -> void:
	_recipes = DEFAULT_RECIPES.duplicate(true)

	if not FileAccess.file_exists(recipes_path):
		return

	var file: FileAccess = FileAccess.open(recipes_path, FileAccess.READ)
	if file == null:
		return

	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		_recipes = parsed


func can_craft(recipe_id: String, inventory: InventorySystem) -> bool:
	if inventory == null or not _recipes.has(recipe_id):
		return false

	var recipe: Dictionary = _recipes[recipe_id] as Dictionary
	var ingredients: Dictionary = recipe.get("ingredients", {}) as Dictionary
	for item_id in ingredients.keys():
		if not inventory.has_item(String(item_id), int(ingredients[item_id])):
			return false
	return true


func craft(recipe_id: String, inventory: InventorySystem) -> bool:
	if not can_craft(recipe_id, inventory):
		return false

	var recipe: Dictionary = _recipes[recipe_id] as Dictionary
	var ingredients: Dictionary = recipe.get("ingredients", {}) as Dictionary
	var output: String = String(recipe.get("output", recipe_id))
	var amount: int = int(recipe.get("amount", 1))

	if not inventory.remove_items(ingredients):
		return false

	inventory.add_item(output, amount)
	return true


func get_recipes() -> Dictionary:
	return _recipes.duplicate(true)
