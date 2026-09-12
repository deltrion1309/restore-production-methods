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

## The PM identity problem

This is the one thing the whole design hinges on.

Restoring a production method is easy: `activate_production_method = { building_type = X
production_method = Y }`. *Reading* which method is currently active is the problem — the only
read primitives found so far (`has_active_production_method`, `is_production_method_active`)
require you to **name** the method you are asking about. If there is no way to enumerate a
building's production method groups, a snapshot cannot be taken generically.

Two candidate plans:

### Plan A — fully generic (preferred)

The wiki's Scope page indicates `production_method` is a real **scope type**. If a building scope
exposes its active production methods as a list (or each group as a link), then the snapshot is
simply a variable list of production-method scopes stored on the building, and restoration feeds
those scopes straight back into `activate_production_method`. No hardcoded names anywhere, and
modded production methods work for free. This satisfies the "avoid hardcoded arrays" directive
literally.

### Plan B — generated script (fallback)

If Plan A is not supported, a small build-time generator (Python, in `dev/`) reads
`common/production_method_groups/` and `common/buildings/` from the installed game and emits
`common/scripted_effects/rpm_generated_*.txt`: per building type, an if/else chain that maps the
active method of each group to a numeric index, plus the inverse chain for restoration.

This is still not *hardcoded* in the maintenance sense — the generator is re-run against each new
patch (and can be pointed at a modded game folder) — but the emitted files are large and must be
regenerated when Paradox adds production methods. It is strictly the second choice.

**Next step:** settle this from the game-generated script reference logs
(`Documents/Paradox Interactive/Victoria 3/logs/event_scopes.log`, `effects.log`, `triggers.log`),
which the wiki names as the authoritative list of scopes, links and lists. These only exist after
the game has been run with the `-debug_mode` launch option.

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

| Variable | Meaning |
|---|---|
| `rpm_original_owner` | country scope — who the state belonged to before the revolt |
| `rpm_lost_date` | when it defected, for the summary text |
| `rpm_pending` | flag: snapshot taken, state not yet returned |

On each **building** in those states:

| Variable | Meaning |
|---|---|
| `rpm_snap_level` | building level at the moment of defection |
| `rpm_snap_pms` | variable list of the active production methods (Plan A) |

Buildings are not destroyed when a state changes owner, so per-building variables are the natural
home for the snapshot — **pending verification that building scope supports variables.**

Clean-up: when a restore is applied, or when the player explicitly dismisses the summary, the
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

1. Does building scope expose its active production methods as scopes (Plan A vs Plan B)?
2. Does building scope support `set_variable` / variable lists?
3. Should a *player-led* revolution (the player is the rebel and keeps the states) also snapshot?
   Currently assumed no — the snapshot only runs for the loyalist side.
4. Should the mod act for AI countries too, or only for the human player? Currently assumed
   player only, to keep save-game size and performance sane.
