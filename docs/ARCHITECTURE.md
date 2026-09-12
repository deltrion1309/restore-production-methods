# Architecture

## Scope of the mod

| Phase | What it does | Trigger |
|---|---|---|
| 1 | Snapshot building levels + active production methods of every state that defects | outbreak of a revolution or secession |
| 2 | Summarise what the rebel AI changed | the player regains one or more snapshotted states |
| 3 | Restore production methods / barracks / conscription centres / building levels | player clicks a button in the summary |

### Decisions taken (2026-09-12)

* **UI form: a native event popup**, not a custom `.gui` window. Custom GUI is the most
  patch-fragile part of Victoria 3 modding and cannot be hot-reloaded; an event popup is fully
  supported, needs no vanilla file overrides, and gets the mechanic working end to end first.
  A custom panel remains a possible later iteration.
* **Military restoration is building restoration.** In Victoria 3 regulars come from Barracks,
  conscripts from Conscription Centres and flotillas from Naval Bases. The four buttons stay
  separate as specified, but all four act on building levels — no attempt is made to create,
  disband or resize actual army/fleet *formations*, which are not the same objects after the
  states change hands.
* **AI-built buildings are never demolished.** Buildings that did not exist in the snapshot are
  listed in the summary and otherwise left alone.
* **Restore actions are global per category** — they act on all regained states at once.
* **Human players only.** Snapshots are taken only when the country losing the states is a
  player. Snapshotting every building of every AI country in every civil war would bloat saves
  and cost monthly script time for no benefit.
* **The player as rebel is out of scope.** Nothing is snapshotted when the player is the
  seceding side; the mod exists to help the loyalist put things back.
* **English only for now, translation-ready.** No player-facing string is ever written into
  script — everything goes through localization keys in a single `rpm_` namespace, so adding a
  language later is dropping in one more `.yml` file.

## The PM identity problem - settled

This was the question the whole design hung on. The game's own generated
`event_scopes.log` settles it: the complete list of scope types contains `building`,
`building_type` and `building_group`, and **no `production_method` scope at all**. There is
therefore no way to capture "whichever method is active" as a value - every read
(`has_active_production_method`, `is_production_method_active`) must name the method.

An in-game test settled a second question at the same time, and less pleasantly.
`event_scopes.log` lists `building` as `Stores Variables: yes`, but the running game disagrees:

```
Error: set_variable effect [ This scope doesn't support variables. Scope: Building Iron Mines ]
```

So nothing can be stored on a building either. Anything per-building has to be keyed by building
*type*, and variable names in Paradox script are literals - they cannot be composed at runtime.

### What follows: generated script

`dev/generate_pm_script.py` reads `common/buildings` and `common/production_method_groups` from
any number of source folders - the game folder first, then each mod folder, later ones winning by
file name exactly as the game resolves load order - and emits
`common/scripted_effects/rpm_generated_effects.txt`: roughly 650 KiB covering 115 building types
and 424 production methods.

This is not hardcoding in the sense the requirements warn about. Nothing is typed by hand and
nothing is frozen to vanilla: point the generator at your mod set and modded buildings and modded
production methods are covered exactly like vanilla ones. The cost is that the file must be
regenerated after a game patch or a change of mod set, which is one command.

### Data model

A state holds at most one building of each type, so `(state, building type)` is a unique key and
the whole snapshot fits in state variables:

| Variable | Scope | Meaning |
|---|---|---|
| `rpm_original_owner` | state | the country it defected from |
| `rpm_pending` | state | snapshot taken, not yet reported |
| `rpm_reported` | state | reported, snapshot kept for the restores |
| `rpm_lvl_<building_type>` | state | that building's level at the snapshot |
| `rpm_pm<N>_<building_type>` | state | index of the active method in the type's Nth group |
| `rpm_sum_*` | country | the summary counters the event text prints |

Four generated effects operate on it: `rpm_generated_snapshot_state`,
`rpm_generated_diff_state`, `rpm_generated_restore_pms_state` and `rpm_generated_clear_state`.

## Hooks

```
on_revolution_start ─┐
on_secession_start  ─┴─► rpm_civil_war_start      (Phase 1: snapshot scope:target's states)

on_civil_war_won    ───► rpm_check_returned_states (Phase 2: immediate check)
on_monthly_pulse_country ► rpm_check_returned_states (Phase 2: safety net — catches states
                                                      reconquered long after the war, or in a
                                                      separate later war)
```

All hooks are attached with the additive pattern
`vanilla_on_action = { on_actions = { rpm_... } }`, so no vanilla file is overridden.
`on_state_owner_change` is deliberately **not** hooked: vanilla already declares an `on_actions`
block on it, and a second one is a conflict rather than a merge (see RESEARCH.md §2).

The monthly-pulse safety net is what actually makes Phase 2 robust. The neat cases
(`on_civil_war_won`) are the minority; players often retake states piecemeal, or much later.

## Data model

Stored as script variables so everything lives in the save game.

On each defecting **state**:

See the data model table above. Clean-up: when a restore is applied, or when the player explicitly dismisses the summary, the
snapshot variables for those states are cleared so repeated revolts do not accumulate stale data
in the save.

## Phase 3 and the one-option problem

A Victoria 3 event closes when the player picks an option, but the spec calls for four
independent restore buttons. The pattern used here is the standard Paradox one: each restore
option applies its effect and then immediately re-fires the same event, so the summary reopens
with the remaining choices; a final "Done" option closes it for good. The summary text updates
each time, so the player sees the counters drop as they restore.

## File layout

```
.metadata/metadata.json          mod manifest
common/on_actions/               hooks into vanilla on_actions
common/scripted_effects/         snapshot, diff and restore effects
common/scripted_triggers/        shared conditions (is this a civil-war loss? has it returned?)
events/                          the summary event
localization/english/            all player-facing text
dev/                             deploy script, generator (if Plan B), test notes
docs/                            this file and the research notes
```

Naming: every script object is prefixed `rpm_`, every localization key `rpm_`, every event is in
the `rpm_events` namespace.

## Open questions

1. The exact parameter spelling of `add_building_level`. The effect exists and takes a signed
   level delta, but the wiki's generated effect list is truncated before the entry and no vanilla
   file uses it. The generated restore currently assumes `type` / `level`; the error log will say
   if that is wrong.
2. Whether state variables survive the state changing owner twice. The snapshot is written while
   the rebel holds the state and read after it comes back, so this is load-bearing. The first
   in-game run confirmed the hooks fire and the effects run; it did not confirm the round trip,
   because the storage was on buildings and failed.
