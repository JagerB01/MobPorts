# Monster Plus → Bedrock

An all-18-mob port candidate targeting **Bedrock 1.26.50**, the current stable version listed by Mojang's `bedrock-samples/version.json` when inspected on 15 October 2026. Uses stable `@minecraft/server` 2.0.0; no preview API dependency.

**Egg spawning is now tested in the actual Bedrock 1.26.52.3 engine:** all 18 registered items were dispensed, consumed, and created their corresponding mobs without native content errors. Full client visuals and combat fidelity still need sign-off. See [VALIDATION.md](VALIDATION.md).

## Try the candidate

Build with `npm ci --ignore-scripts && npm run verify`. Import `dist/MonsterPlus-Bedrock-0.1.2.mcaddon` into Bedrock, then activate **both** Monster Plus packs in a disposable Creative test world. The behavior pack declares its resource-pack dependency. Use `/function monsterplus/eggs` to receive all 18 explicit spawn eggs, or find them in the Creative Nature tab. Individual egg IDs are `monsterplus:<id>_spawn_egg`.

Run `/scriptevent monsterplus:smoke` to check native registration, health and properties for all 18 mobs. It removes the temporary test entities. Run `/function monsterplus/gallery` in a spacious test area to spawn the full roster for visual inspection. This gallery keeps its spawned mobs, so use a disposable world.

| Source name | Bedrock identifier |
| --- | --- |
| Hermit Abysswalker | `monsterplus:abyssologer` |
| Glow Skeleton | `monsterplus:glow_skeleton` |
| Swamp Monster | `monsterplus:swamp_zombie` |
| Opalescent Eye | `monsterplus:opalescent_eye` |
| Spectral Minion | `monsterplus:spectral_skeleton` |
| Lava Squid | `monsterplus:lava_squid` |
| Mother Lava Squid | `monsterplus:mother_lava_squid` |
| Crystalian | `monsterplus:crystal_zombie` |
| Overgrown Skeleton | `monsterplus:overgrown_skeleton` |
| Demon Eye | `monsterplus:demon_eye` |
| Ender Watcher | `monsterplus:ender_eye` |
| Corrupted Ancient Hero | `monsterplus:ancient_hero` |
| Ancient Hero Skull | `monsterplus:ancient_hero_skull` |
| Wisp | `monsterplus:wisp` |
| Soul | `monsterplus:soul` |
| Desert Sorceress | `monsterplus:desert_sorceress` |
| Desert Acolyte | `monsterplus:desert_acolyte` |
| Spectral Skull | `monsterplus:spectral_skull` |

## Development

Node 24 and Python 3 are available in the prepared cloud machine. No credentials, database or running web service are required to build this add-on. Each cloud task is already isolated: use `/workspace/MobPorts`; do not create a worktree unless explicitly requested.

```sh
cd /workspace/MobPorts
npm --cache /workspace/.npm-cache ci --ignore-scripts --no-audit --no-fund
npm run verify
```

Edit `packs/MonsterPlus_BP/scripts/` for behavior and `source/` / `tools/build.py` for model and pack generation. Pack JSON, textures, loot and spawn files are **generated and ignored**; the build recreates their directories. It preserves hand-written runtime scripts. `dist/` contains the `.mcaddon` and separate `.mcpack` files.

`npm run check` checks the real stable Bedrock API declarations. `npm test` runs combat-rule tests, a simulated API smoke test, and asset/reference/archive validation. These checks do not load the Bedrock engine.

Optional: `python3 tools/render_software.py` generates `dist/model-inspection.png` using NumPy and Pillow (available in this cloud instance). It is an offline inspection render, not an in-game screenshot; portraits are independently framed and do not show relative mob sizes.

The original Java model boxes, hierarchy, UVs and attributes were recovered using checksum-verified CFR 0.152. Rebuilding does not require the JAR or decompiler: recovered data and original assets are retained in `source/`. To repeat recovery from a matching JAR and its decompiled package directory, use `tools/recover.py --jar PATH --java-dir PATH`. Generated metadata records the JAR SHA-256.

## Source credits

Monster Plus is by **Nitespring**. Original textures, sound recordings and recovered model definitions retain their original rights. The uploaded JAR declares **All rights reserved**; this repository does not grant a redistribution license for those materials. No public upload or publication was performed.

The file is named `MonsterPlus-Neoforge1.21.1-v1.2.0.0.jar`, but its embedded mod metadata declares `1.1.9.0`. This implementation follows the supplied bytecode and assets, not an assumed source release. The vanilla blaze-powder texture comes from Mojang's `bedrock-samples` resource pack.

## 0.1.1 egg compatibility update

All 18 eggs are explicit item definitions in the Nature category with entity-placer components. The build no longer relies on generated spawn-egg registration. `/function monsterplus/eggs` gives every egg; `/function monsterplus/status` reports the installed build. Pack versions are increased to 0.1.1. The stable script dependency is 2.0.0 and the newer pre-damage hook is optional, so it cannot prevent script startup on the older API. The source armor formula and pre-damage friendly-fire cancellation run only when that hook is exposed. Actual Bedrock validation remains pending.

## 0.1.2: actual entity-loading fix

Bedrock rejected all 18 mob definitions because float properties had integer `default: 1` values. They now serialize as `default: 1.0`, with float range bounds. Legacy ranged-attack fields were also corrected for the declared entity format. A real Bedrock 1.26.52.3 integration test powers a dispenser containing each of the 18 egg items, observes the corresponding native entity-spawn event, and checks item consumption. All 18 passed; see `validation/bedrock-eggs-0.1.2.json`. The regression validator now rejects integer defaults for float properties.

Run the native regression with the official dedicated-server installation: `python3 tools/bedrock_engine_test.py --server-dir /workspace/bedrock-validation --archive dist/MonsterPlus-Bedrock-0.1.2.mcaddon`. It creates a runner-owned disposable world and separate test harness; it does not modify the tested archive.
