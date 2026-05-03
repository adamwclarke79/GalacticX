# Platformer Agent Notes

## Source Notes

- Claude Code project skills live under `.claude/skills/<skill-name>/SKILL.md`; project subagents live under `.claude/agents/`.
- `htdt/godogen` uses a multi-stage Godot game-generation workflow with decomposition, architecture, asset planning, task execution, visual capture, and resumable state files.
- `wshobson/agents` includes a `godot-gdscript-patterns` skill focused on Godot 4 GDScript architecture: state machines, signals, autoloads, resources, and typed script patterns.
- `Ev01/PlatformerController2D` highlights platformer affordances worth preserving in agent reviews: coyote time, jump buffering, variable jump height, asymmetric gravity, double jump, acceleration/friction, input mappings, and edge-case fixes.
- Godot documentation emphasizes `CharacterBody2D`, `_physics_process()`, `move_and_slide()`, grounded motion mode for platformers, and typed GDScript consistency.

## Role Review Template

Each specialist should return:

1. Constraints found in the repo.
2. Proposed change or design decision.
3. Risks or tradeoffs.
4. Acceptance checks.

The chair should return:

1. Merged decision.
2. Disagreements resolved.
3. Implementation order.
4. Verification plan.

## Platformer Feel Checklist

- Movement has acceleration and deceleration rather than binary velocity snapping unless intentionally arcade-like.
- Jump includes coyote time and jump buffer unless the design intentionally requires strict precision.
- Jump height supports tap/hold variation when the level design asks for nuanced vertical control.
- Falling is faster than rising for responsiveness unless floaty movement is a deliberate theme.
- Camera preserves forward visibility and avoids hiding landing zones.
- Hazards communicate their active area before punishing the player.
- Checkpoints appear before difficulty spikes and after completed challenges.
- The first level teaches verbs before testing combinations.

## Godot 4 Implementation Checklist

- `project.godot` exists before Godot-specific code changes are made.
- Input actions are registered in project settings and names match scripts.
- Controllable characters use `CharacterBody2D` and `velocity`.
- `move_and_slide()` is called from `_physics_process()`.
- New GDScript uses explicit types, `@export`, `@onready`, and `signal` declarations where appropriate.
- Node paths are stable or exported; brittle deep `$Path/To/Node` references are avoided in reusable scripts.
- Scene ownership is correct for generated `.tscn` files.
- Runtime state is not hidden inside UI nodes.
