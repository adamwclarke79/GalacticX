---
name: godot-2d-platformer-team
description: Coordinate a Claude Code team for Godot 4 GDScript 2D game and platformer work. Use when designing or implementing platformer mechanics, 2D gameplay UI, GDScript architecture, scene structure, player feel, level flow, playtest criteria, or multi-agent review for a Godot project.
---

# Godot 2D Platformer Team

Use this skill to run a small specialist team for Godot 4 + GDScript 2D platformer work. The team has four roles:

- `godot-ui-gameplay-designer`: player-facing UI, HUD, menus, input affordances, readability, camera framing, and game-state presentation.
- `godot-backend-coder`: Godot 4 scene/script architecture, typed GDScript, physics, save/progression, enemy systems, and tests.
- `godot-gameplay-experience-advisor`: moment-to-moment feel, difficulty curve, level grammar, onboarding, friction, pacing, and playtest criteria.
- `godot-platformer-chair`: reviews the role outputs, resolves conflicts, and produces the final recommendation or implementation plan.

## Workflow

1. Inspect the repo before assuming engine state. If `project.godot` is absent, state that the repository is not currently a Godot project before proposing Godot-specific implementation.
2. Define the user-facing objective in one sentence and identify the affected surface: UI, mechanics, systems code, level design, assets, or verification.
3. Route the work:
   - UI or presentation-heavy requests: start with `godot-ui-gameplay-designer`.
   - GDScript, node, physics, persistence, or tool requests: start with `godot-backend-coder`.
   - Feel, balance, platform layout, onboarding, or retention requests: start with `godot-gameplay-experience-advisor`.
   - Broad feature requests: consult all three specialist roles, then have `godot-platformer-chair` synthesize.
4. Keep each role output short and concrete: constraints, proposal, risks, acceptance checks.
5. Let the chair decide the final ordering. The chair should explicitly call out any conflict between design intent, technical cost, and gameplay feel.
6. If implementation is requested, code only after the chair has resolved scope. Prefer small vertical slices that can be played and verified.

## Godot 4 Standards

- Prefer typed GDScript with explicit return types for new code.
- Use `CharacterBody2D` for controllable platformer characters unless the project already has a different established pattern.
- Put movement in `_physics_process(delta)` and call `move_and_slide()` after updating `velocity`.
- Do not multiply `CharacterBody2D.velocity` by `delta`; Godot applies frame timing internally during `move_and_slide()`.
- Use scenes for reusable node trees, resources for reusable data, and signals for cross-node events.
- Keep gameplay constants exported when designers need inspector tuning.
- Use autoloads sparingly for true global state such as session, save, audio, or event-bus systems.
- Avoid Godot 3 patterns in Godot 4 work: `KinematicBody2D`, `yield`, old `move_and_slide(velocity)` signatures, and untyped spaghetti controllers.

## Platformer Design Checks

For player movement, evaluate acceleration, deceleration, air control, coyote time, jump buffering, variable jump height, fall multiplier, terminal velocity, slopes, one-way platforms, moving platforms, knockback, ladders/climb zones, and respawn behavior.

For levels, define a small vocabulary before building content: safe ground, gap, vertical challenge, enemy gate, hazard, moving platform, checkpoint, reward, secret, and recovery path. Introduce one idea at a time, combine ideas after the player proves comprehension, and leave room for failure recovery.

For UI and feedback, verify that health, lives, score, objective state, checkpoints, interact prompts, pause, death, restart, and controller/keyboard prompts are visible without competing with platform readability.

For game feel, require feedback loops: animation state, dust/landing effects, hit pause, screen shake only for high-salience events, sound cues, camera dead zone/smoothing, and clear damage/ invulnerability feedback.

## Verification

Use the smallest reliable verification available:

- Static pass: parse scene/script structure and check Godot 4 APIs.
- Runtime pass: run Godot headless tests when a Godot executable and test harness exist.
- Playability pass: launch the scene and verify controls, collisions, camera, UI readability, failure/retry, and at least one intended fun beat.
- Regression pass: confirm no existing input actions, autoloads, exported tunables, or scene paths were broken.

For deeper design details and the GitHub/source notes used to create this skill, read `references/platformer-agent-notes.md`.
