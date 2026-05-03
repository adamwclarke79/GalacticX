class_name InteractionSystem
extends Node

signal prompt_changed(prompt: String)

var player: Node
var game_state: GameState
var _current_prompt: String = ""


func setup(next_player: Node, next_game_state: GameState) -> void:
	player = next_player
	game_state = next_game_state
	if player != null and player.has_signal("interact_pressed"):
		player.interact_pressed.connect(interact)


func _process(_delta: float) -> void:
	var prompt := ""
	var interactable := _get_current_interactable()
	if interactable != null and interactable.has_method("get_interaction_prompt"):
		prompt = String(interactable.call("get_interaction_prompt", game_state))

	if prompt != _current_prompt:
		_current_prompt = prompt
		prompt_changed.emit(prompt)


func interact() -> void:
	var interactable := _get_current_interactable()
	if interactable == null:
		if game_state != null:
			game_state.set_status("Nothing to interact with")
		return

	if interactable.has_method("interact"):
		var result = interactable.call("interact", game_state)
		if game_state != null and result is String and not String(result).is_empty():
			game_state.set_status(String(result))


func _get_current_interactable() -> Node:
	if player == null or not player.has_method("get_current_interactable"):
		return null
	return player.call("get_current_interactable") as Node
