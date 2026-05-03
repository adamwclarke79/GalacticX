class_name TimeSystem
extends Node

signal time_changed(minutes: int, formatted_time: String)
signal schedule_phase_changed(phase: String)

@export var start_minutes: int = 6 * 60
@export var minutes_per_real_second: float = 6.0
@export var schedule_path: String = "res://data/npc_schedules.json"

var current_minutes: int = 0
var _minute_accumulator: float = 0.0
var _phase: String = "Boarding"


func _ready() -> void:
	current_minutes = start_minutes
	_emit_time()
	emit_signal("schedule_phase_changed", _phase)


func _process(delta: float) -> void:
	_minute_accumulator += delta * minutes_per_real_second
	if _minute_accumulator < 1.0:
		return

	var elapsed_minutes := int(_minute_accumulator)
	_minute_accumulator -= elapsed_minutes
	current_minutes = (current_minutes + elapsed_minutes) % (24 * 60)
	_update_phase()
	_emit_time()


func set_minutes(minutes: int) -> void:
	current_minutes = clampi(minutes, 0, (24 * 60) - 1)
	_update_phase()
	_emit_time()


func format_time() -> String:
	var hours := int(current_minutes / 60)
	var minutes := current_minutes % 60
	return "%02d:%02d" % [hours, minutes]


func get_phase() -> String:
	return _phase


func _update_phase() -> void:
	var next_phase := "Boarding"
	if current_minutes >= 7 * 60:
		next_phase = "Search"
	if current_minutes >= 8 * 60:
		next_phase = "Lockdown"

	if next_phase != _phase:
		_phase = next_phase
		schedule_phase_changed.emit(_phase)


func _emit_time() -> void:
	time_changed.emit(current_minutes, format_time())
