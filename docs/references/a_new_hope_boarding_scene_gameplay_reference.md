# A New Hope Boarding Scene Gameplay Reference

This reference captures high-level gameplay design lessons from the opening boarding sequence of *Star Wars: Episode IV - A New Hope* for the private GalacticX demo. It is not a transcript, subtitle extract, screenplay excerpt, or shot-by-shot recreation. Use it as a design grounding document for layout, pacing, character roles, animation, and systems behavior.

## Design Purpose

- Ground the starship slice in a low top-down boarding action fantasy.
- Help agents build believable corridor pressure, faction behavior, droid escape tension, and command presence.
- Keep implementation systems-first: 8-direction movement, interaction, patrols, alerts, HUD, save/load, and reusable NPC behaviors.
- Avoid defining a final mission loop until the core systems are playable.

## Setting

- Location: a rebel corvette or similar small military/diplomatic starship under forced boarding.
- Camera interpretation: low top-down 16-bit view, with characters readable in eight facings.
- Space grammar: tight white/gray corridors, bulkheads, recessed doorways, alcoves, control panels, smoke, sparking wall damage, and cross-corridor choke points.
- Tactical mood: the ship has already been breached; defenders are reacting under pressure while the boarding force pushes inward.

## Factions And Characters

- Stormtroopers: armored boarding soldiers. They advance through corridors, secure rooms, and create pressure through patrol routes, line-of-sight checks, and alert escalation.
- Rebel soldiers: defensive troops. They hold choke points, retreat between cover, and can be represented by static firing poses or simple patrol/guard behaviors in v1.
- Imperial officers: command figures. They should stay behind or near patrols, mark secured zones, and provide scenario authority without needing complex AI.
- C3PO and R2D2: noncombat escape objectives. They should avoid danger, move slowly or cautiously, and prefer side corridors or escape-pod routes.
- Princess Leia: hero-side objective anchor. For v1, she can be a marker, protected NPC, or locked-room objective rather than a full companion system.
- Darth Vader: villain-side pressure anchor. For v1, use him as a static arrival marker, high-threat zone, or alert-state signifier rather than a boss.
- Random droids: ship-life props and low-risk moving actors. They can wander, panic, block narrow spaces briefly, or provide visual scale.

## Spatial Logic

- Breach entry: one end of the map should communicate that the attackers entered through a damaged docking point or blast door.
- Defensive corridor: place rebels near a choke point with cover objects, wall recesses, and short sightlines.
- Side rooms: use small alcoves for containers, terminals, droid hiding points, or alternate paths.
- Locked bulkheads: doors should make the starship feel segmented and give interaction systems a clear purpose.
- Droid route: create a safer but indirect route toward an escape bay, maintenance hatch, or pod access area.
- Command marker: place Leia and Vader markers in different zones so the map has clear narrative poles without requiring cutscenes.

## Gameplay Translation

- Boarding pressure should come from space control, not from overwhelming the player with combat in the first slice.
- Patrols should be simple and readable: fixed routes, clear facing direction, and visible suspicion feedback.
- Line-of-sight can begin as proximity or cone detection, then later account for walls and cover.
- Locked doors and terminals should gate movement and demonstrate interaction, inventory, crafting, and save/load state.
- Cover objects can be noninteractive collision in v1; later they can support stealth, crouch, or firefight behavior.
- Smoke and sparks should be visual dressing only at first, avoiding physics or particle complexity unless Godot validation is stable.
- Alarm pressure should be represented through HUD state, patrol speed, suspicion growth, or reset conditions.

## NPC Behavior Notes

- Stormtrooper patrols should face their movement direction and pause briefly at checkpoints.
- Rebel soldiers can hold positions, face the breach, and optionally switch to retreat markers during alert states.
- Officers should move less than soldiers; their value is readability and command presence.
- Droids should not fight. They should flee, idle nervously, follow a path, or wait near escape markers.
- Leia should read as an objective anchor; avoid implementing dialogue or scripted rescue logic in v1.
- Vader should read as danger and escalation; avoid combat, boss logic, or complex pursuit in v1.

## 8-Direction Animation Requirements

- All moving actors should support these facings: `north`, `south`, `east`, `west`, `north-east`, `north-west`, `south-east`, `south-west`.
- Movement vectors should select facing through eight angle sectors.
- Diagonal movement must be normalized so diagonal travel is not faster than cardinal travel.
- Animation frame counts may vary by actor, state, or direction. The loader should discover `frame_*.png` files and loop whatever exists, from 2 to 8 frames.
- If animated frames are missing, fall back to `rotations/<direction>.png`.
- If rotations are missing, fall back to root directional files such as `<character>/<direction>.png`.
- If no directional sprite exists, use a colored placeholder and document the missing asset.

## First-Slice Boundaries

- Include: top-down movement, 8-direction facing, simple patrols, suspicion, interaction prompts, inventory/crafting test items, locked bulkheads, HUD, save/load, and droid escape markers.
- Exclude for now: full combat, dialogue trees, cinematic scripting, squad tactics, destructible geometry, boss encounters, procedural ship layouts, and a fully defined mission loop.
- Firefights can be implied through static NPC placement, alert zones, muzzle-flash placeholders, or blocked corridors until combat is deliberately scoped.

## RAG Usage

Use this reference when asking:

- How should the boarded starship level be laid out?
- How should stormtroopers, rebels, droids, Leia, and Vader behave in a systems-first prototype?
- What should the 8-direction animation loader support?
- Which cinematic elements should be translated into gameplay pressure without recreating the scene directly?
