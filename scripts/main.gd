extends Node2D

@onready var _game_state: GameState = $GameState
@onready var _save_system: SaveSystem = $SaveSystem
@onready var _world: BoardedStarshipSector = $LevelRoot/BoardedStarshipSector
@onready var _hud: HUD = $HUD

var _interaction_system: InteractionSystem


func _ready() -> void:
	_configure_input()
	_wire_game_state()
	_wire_world()
	_setup_interaction()
	_hud.set_status("PixelLab-sourced starship sandbox ready")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("craft_debug"):
		_game_state.craft_debug_item()
	elif event.is_action_pressed("save_debug"):
		_save_game()
	elif event.is_action_pressed("load_debug"):
		_load_game()
	elif event.is_action_pressed("inventory"):
		_game_state.set_status("Inventory toggled in HUD")


func _configure_input() -> void:
	_bind_keys("move_left", [KEY_A, KEY_LEFT])
	_bind_keys("move_right", [KEY_D, KEY_RIGHT])
	_bind_keys("move_up", [KEY_W, KEY_UP])
	_bind_keys("move_down", [KEY_S, KEY_DOWN])
	_bind_keys("interact", [KEY_E])
	_bind_keys("inventory", [KEY_I, KEY_TAB])
	_bind_keys("craft_debug", [KEY_C])
	_bind_keys("save_debug", [KEY_F5])
	_bind_keys("load_debug", [KEY_F9])


func _bind_keys(action: StringName, keys: Array) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)

	for key in keys:
		var physical_key := int(key)
		if _action_has_physical_key(action, physical_key):
			continue

		var event := InputEventKey.new()
		event.physical_keycode = physical_key
		InputMap.action_add_event(action, event)


func _action_has_physical_key(action: StringName, key: int) -> bool:
	for event in InputMap.action_get_events(action):
		var key_event := event as InputEventKey
		if key_event != null and key_event.physical_keycode == key:
			return true
	return false


func _wire_game_state() -> void:
	_game_state.inventory_changed.connect(_hud.set_inventory)
	_game_state.suspicion_changed.connect(_hud.set_suspicion)
	_game_state.time_changed.connect(_hud.set_time)
	_game_state.status_changed.connect(_hud.set_status)
	_game_state.alert_triggered.connect(_on_alert_triggered)


func _wire_world() -> void:
	_world.player_ready.connect(_on_player_ready)
	_world.guard_ready.connect(_on_guard_ready)
	_world.status_requested.connect(_game_state.set_status)

	if _world.player != null:
		_on_player_ready(_world.player)
	if _world.guard != null:
		_on_guard_ready(_world.guard)


func _setup_interaction() -> void:
	_interaction_system = InteractionSystem.new()
	_interaction_system.name = "InteractionSystem"
	add_child(_interaction_system)
	_interaction_system.prompt_changed.connect(_hud.set_prompt)
	if _world.player != null:
		_interaction_system.setup(_world.player, _game_state)


func _on_player_ready(player: PlayerController) -> void:
	if _interaction_system != null:
		_interaction_system.setup(player, _game_state)


func _on_guard_ready(guard: GuardAI) -> void:
	guard.suspicion_requested.connect(_game_state.add_suspicion)


func _on_alert_triggered() -> void:
	_world.reset_player_to_spawn()
	_game_state.set_suspicion(48.0)
	_game_state.set_status("Alert reset: player returned to breach")


func _save_game() -> void:
	var data := {
		"version": 1,
		"game_state": _game_state.to_save_data(),
		"world": _world.to_save_data()
	}
	if _save_system.save_game(data):
		_game_state.set_status("Saved to %s" % _save_system.get_save_path())
	else:
		_game_state.set_status("Save failed")


func _load_game() -> void:
	var data := _save_system.load_game()
	if data.is_empty():
		_game_state.set_status("No save found")
		return

	if data.get("game_state", {}) is Dictionary:
		_game_state.apply_save_data(data["game_state"])
	if data.get("world", {}) is Dictionary:
		_world.apply_save_data(data["world"])
	_game_state.set_status("Loaded from %s" % _save_system.get_save_path())
