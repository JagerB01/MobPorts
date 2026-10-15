# Validation and remaining work

This is an **all-mob implementation candidate** with native egg spawning now tested in Bedrock 1.26.52.3. Full visual/combat fidelity is not yet signed off.

## Verified in this cloud instance

- Source inventory: 18 mob types, all corresponding behavior/client definitions and source-derived health values.
- Original custom Java cube geometry recovered, including pivots, hierarchy, UVs, inflation, and mirrored cubes. Models inherited from vanilla are explicitly reconstructed. Runtime jaw offsets replace the source's inactive export offsets.
- Original JAR PNGs and OGGs are preserved byte-for-byte. The offline inspection sheet renders all 18 model definitions with their textures; no Bedrock renderer was involved.
- Stable `@minecraft/server` 2.0.0 API type check passes.
- Fourteen automated tests pass: crystal patterns, cooldown priority, hero phase thresholds and armor formula, projectile math, status-effect durations, and a simulated API execution of all 18 controllers. The simulation exercises attacks, summons, the mother's birth timer, ownership, hero phase transitions, poison and conditional Demon Eye loot. It does not emulate native AI, physics, Molang, pack loading or rendering.
- Generated JSON parses; geometry, animation, texture, sound, custom-drop and archive references resolve. Native component schemas are **not** validated by this structural check.
- Package creation, ZIP integrity and archive-vs-filesystem parity pass. Frozen dependency installation and rebuilding are exercised in `/workspace/MobPorts`.

## Source-specific mechanics implemented

- Abysswalker: eye and unarmed spectral-minion summons, owned minion targets and expiry, darkness, the source crystal ring/line patterns and a purple fireball.
- Crystalian: slow movement, high knockback resistance, three delayed crystal spikes at the target every 60 ticks.
- Ancient Hero: health phases at 75%, 50%, 25%; armor loss, visual armor/head removal, phase-two detached skull, accelerating skull-fire intervals, homing skull projectiles and friendly-fire protection.
- Eyes and flying skulls: orbit/dive controller; Ender Watcher retaliation/endermite targets and teleporting; source Demon Eye color/size probabilities, size-dependent health/speed, iris scales, layered iris rendering and timed teeth textures.
- Lava squids, Wisps and Souls: floating combat, retreat and distinct projectile types; mother births a lava squid every 400 ticks and has a fireball barrage.
- Skeletons: source bow/melee/unarmed spawn choices; distinct poison and glow-hit effects. Java Glowing is replaced by a visible particle marker because Bedrock has no equivalent status effect.
- Sorceress and Acolyte: separate flame breath/fireball systems; Sorceress also has source-pattern fire placement (respecting mob griefing) and a barrage. Breath flames use source damage, acceleration and short lifetimes.
- All 15 natural-spawning species have spawn rules translated from the Java biome modifiers, preserving source weights and herd sizes. Three summoned types remain summon/egg-only. Custom loot drops are represented as items.

## Fidelity work still requiring attention

These are limitations, not claimed feature parity:

- Java movement controllers are recreated with Bedrock-native navigation plus scripted steering. Flight paths, liquid motion, animation timing and attack feel need side-by-side tuning in-game. The Ancient Hero's native melee movement and scripted ranged state do not yet reproduce every Java strafe/jump animation.
- Eye/Wisp visual scales use continuous source ranges; collision sizes are quantized to the nearest 0.05 scale step because native collision boxes are configured through component groups. Iris material brightness and animated teeth need an in-game visual pass.
- Ender Watcher has water damage and teleport-on-damage, including projectile damage. Its daylight idle-teleport/light-level behavior is not exactly reproduced; teleport landing and liquid checks require engine validation.
- Mob breath uses the source's default zero-ricochet setting. Spell-scroll ricochets are outside this mob scope. Sorceress walls place real fire after the source warmup and use Bedrock fire behavior. Custom Java particle shapes and some projectile special effects use Bedrock substitutions.
- Java biome tags and mob-cap categories have no exact Bedrock equivalent. Natural spawn frequency and lava spawning require engine testing. Darkness, sunlight, liquid behavior, damage attribution and native equipment rendering need actual Minecraft validation.
- Looting bonuses are translated to Bedrock's linear bonus rather than Java's exact first-level formula. The drop items preserve identity/texture; full armor, weapon and spell-scroll item gameplay is outside this mob-port implementation.

## Remaining client and combat checks

1. Load the `.mcaddon` in the target stable client and inspect the content log. Confirm script version availability, native component acceptance, Molang expressions, materials, and dependencies.
2. Run `/scriptevent monsterplus:smoke` and require all 18 registrations/health/property checks to pass. Run `/function monsterplus/gallery` in Creative and compare each source model, size, texture layer, item grip and animation.
3. In Survival, check every attack listed above, projectile ownership, neutral retaliation, line of sight, minion lifetime and hero phases. Observe the mother's 20-second birth interval. Test multiplayer and unload/reload behavior.
4. Observe natural spawning in the relevant underground, swamp, jungle/lush-cave, desert, Nether and End settings. Check summon-only types do not spawn naturally.
5. Fix content-log failures and complete remaining fidelity work before labeling the add-on complete.

## Actual Bedrock engine validation: 0.1.2

Network access was granted for the official server download. The official stable download-link service returned Bedrock **1.26.52.3**. The Linux archive was downloaded over verified HTTPS from `www.minecraft.net`, checked for ZIP corruption, and run in an isolated, disposable local world.

The exact previously published 0.1.1 archive reproduced the failure: all 18 actor definitions were rejected because float properties used integer default values. The content log also rejected newer ranged-attack field shapes under the pack's older declared entity format. Version 0.1.2 corrects these definitions.

`tools/bedrock_engine_test.py` loaded the exact 0.1.2 release archive, along with an independent test harness. For each of 18 items it verified native item registration, placed the egg in a real dispenser, powered the dispenser, checked consumption, and observed the correct native `entitySpawn` event. **18/18 passed, with zero native Actor/JSON/Item/Scripting content errors.** The result contains the tested archive SHA-256 in `validation/bedrock-eggs-0.1.2.json`; the full engine log is retained locally.

This verifies native egg/entity registration and dispenser spawning. It does not claim a client-side Creative menu screenshot, manual player interactions, or full visual/combat parity. Those broader checks remain distinct.

## 0.1.1 egg update

Added 18 explicit Nature-category inventory items, each with an entity-placer component targeting its corresponding mob, and `/function monsterplus/eggs`. Native generated eggs are disabled to avoid duplicate identifiers. Validated every egg item ID, Creative category and target reference. Stable API 2.0.0 compilation and simulated execution both with and without the newer pre-damage hook pass. The pre-damage armor/friendly-fire hook is optional; it is unavailable when the runtime only exposes API 2.0. This update has not been tested inside the Bedrock client.

## Spawn failure regression

The structural validator now checks the JSON numeric representation of every float property default and bound. This catches the specific engine-rejected `default: 1` bug rather than treating numeric equality to `1.0` as sufficient.
