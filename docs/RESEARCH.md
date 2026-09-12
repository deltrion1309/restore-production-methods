# Engine research notes

Everything below was verified against the **installed 1.13 game files**, not from memory.
Paths are relative to `Victoria 3/game/`. Line numbers refer to the 1.13 files and will drift.

## 1. Civil-war on_actions

`common/on_actions/00_code_on_actions.txt` defines, with these documented root scopes:

| on_action | Root | Extra scope | Notes |
|---|---|---|---|
| `on_revolution_start` | Country (the *loyalist* country) | `scope:target` = uprising country | fires at outbreak |
| `on_secession_start`  | Country (the *loyalist* country) | `scope:target` = uprising country | fires at outbreak |
| `on_revolution_end`   | Country | `scope:target` = uprising country | empty in vanilla |
| `on_secession_end`    | Country | `scope:target` = uprising country | |
| `on_civil_war_won`    | Country | — | fires **after** `on_revolution_end` |
| `on_state_owner_change` | State | — | fires on any ownership change |
| `on_state_created`    | State | — | |
| `on_revolution_checkpoint_reached` / `on_secession_checkpoint_reached` | | | periodic during the war |

**The states have already been transferred to `scope:target` when `on_revolution_start` runs.**
Evidence: vanilla's own Paris Commune branch inside `on_revolution_start` does
`set_state_owner = c:PRC` and `c:PRC = { annex = scope:target }`, i.e. it manipulates the rebel
country's territory from inside that hook. This makes `scope:target.any_scope_state` the correct,
generic way to enumerate the defecting states — no need to guess which states *will* defect.

Useful triggers seen in the same context: `is_secessionist`, `is_civil_war_type = revolution`,
`random_civil_war`, and the vanilla variable `civil_war_type_var`.

## 2. Hooking on_actions without overriding vanilla

`common/on_actions/_on_actions.md` states:

> You can declare data for on-actions in multiple files, however, you cannot have multiple
> triggers or effect blocks for a given named on-action. [...] If a modder wishes to append their
> own effects to an on_action without overriding a file, they may do it as follows:
> `some_vanilla_on_action = { on_actions = { some_modded_on_action } }`

**Caveat:** the same restriction that applies to `effect` applies to `on_actions`. Vanilla's
`on_state_owner_change` *already has* an `on_actions = { ip4_lands_of_anarchy_remove_on_state_lost }`
block, so we must **not** add our own `on_actions` block to it — that is a conflict, not a merge.
Hooks we add must target on_actions that have no `on_actions` block of their own
(`on_revolution_start`, `on_secession_start`, `on_civil_war_won`, `on_war_end`, the pulses).

## 3. Production methods in script

* Defined in `common/production_methods/`, grouped by `common/production_method_groups/`;
  building types declare `production_method_groups = { ... }`.
* Read: `has_active_production_method = pm_x` (building scope) and
  `is_production_method_active = { building_type = ... production_method = ... }`
  (country/state scope). Both seen in vanilla scripted effects.
* Write: `activate_production_method = { building_type = ... production_method = ... }`.
* Iteration: `every_scope_building` / `any_scope_building` / `random_scope_building` exist on
  state scope (used 43× in vanilla scripted effects alone).

**Open engine question — the one that drives the architecture:** there appears to be *no* script
list that iterates a building's production method *groups* or its currently active methods. The
wiki's Building modding page states you must name each production method explicitly. If that is
confirmed, a fully generic "read whatever PM is active" is impossible in pure script, and the
snapshot has to be built from the game's own data at build time (see ARCHITECTURE.md, "PM
identity problem").

To settle it definitively we need the game-generated script reference logs:
`Documents/Paradox Interactive/Victoria 3/logs/event_scopes.log`, `effects.log`, `triggers.log`.
The wiki itself points at these as the authoritative list.

## 4. Mod packaging

* `.metadata/metadata.json` is mandatory (the old `descriptor.mod` is legacy).
  Format confirmed against an installed 1.13 workshop mod: `name`, `id`, `version`, `game_id`,
  `supported_game_version`, `short_description`, `tags`, `relationships`, `game_custom_data`.
* Localization files must be UTF-8 **with BOM** and end in `_l_english.yml`.
* Scripted GUIs live in `common/scripted_guis/` and **cannot be hot-reloaded** — a game restart is
  required for changes to take effect.

## 5. Effects confirmed for the restore step (from effects_l_english.yml)

The game's own effect localization file is a de-facto index of every effect name, because each
effect has a tooltip key. Relevant entries:

| Loc key | What it proves |
|---|---|
| `ADD_BUILDING_LEVEL:0 "Change [BuildingType.GetName] level by $LEVEL|v$ in [State.GetName]"` | `add_building_level` exists and takes a **signed** level delta — the clean way to downsize without demolishing |
| `ACTIVATE_PRODUCTION_METHOD:0 "Activate [PRODUCTION_METHOD.GetName] for [BUILDING_TYPE.GetName] buildings in $TARGET|v$"` | confirms `activate_production_method` |
| `CREATE_BUILDING`, `REMOVE_BUILDING` | the brute-force resize idiom |

`activate_production_method` is documented as country/state scope with
`building_type = <key>` and `production_method = <key>`.

Vanilla's own "resize a building" idiom (`00_chris_scripted_effects.txt`, `destroy_barracks`) is
`remove_building = X` followed by `create_building = { building = "X" level = N reserves = 1 }`.
That destroys and rebuilds, which resets the building's production methods — so if we ever fall
back to it, **building levels must be restored before production methods**, never after.

Exact parameter spellings for `add_building_level` are still unconfirmed; the wiki's
auto-generated effect module is truncated before the entry.

## 6. Printing script variables in localization

Confirmed from vanilla text (`content_1_l_english.yml`, `JE_lobby_text_l_english.yml`):

```
[ROOT.GetCountry.MakeScope.Var('my_var').GetValue]
[GetPlayer.MakeScope.ScriptValue('my_script_value')]
[ROOT.Var('emperor_var').GetCharacter.GetFirstName]
```

Append a format specifier for integers: `.GetValue|0]`.

## 7. Variable lists hold scopes, not values

`add_to_variable_list = { name = <name> target = <event target> }`. The payload is an **event
target**, i.e. a scope. This matters for the production-method snapshot: storing methods in a
list is only possible if a production method is reachable as a scope from a building.

## 8. Verified in-game (first test run, 1.13, mod-only playset)

The mod loaded (`NAMESPACE > 'rpm_events' is set to #1970000` in `game.log`) and every file
parsed. What the run proved:

* The hooks work. `rpm_take_snapshot` ran from `on_revolution_start` and
  `every_scope_building` iterated the real buildings of the defecting states - the errors below
  name them individually (Iron Mines, Barracks, Conscription Center, ...).
* **Building scopes cannot store variables**, despite `event_scopes.log` listing
  `building: Stores Variables: yes`:
  `Error: set_variable effect [ This scope doesn't support variables. Scope: Building Iron Mines ]`
  The same for `has_variable`. The generated log describes the scope *type*; the running game
  disagrees about the instances.
* Paradox wants **UTF-8 with BOM for script files**, not only localization:
  `File 'common/scripted_effects/rpm_snapshot_effects.txt' should be in utf8-bom encoding`.
* Nothing else in the mod produced an error - the on_action chaining, `save_temporary_scope_value_as`
  with a nested value block, and comparing `level` against a variable all parsed and ran.

## 9. There is no production_method scope

`event_scopes.log` lists every scope type the game has. The building-related ones are `building`,
`building_type` and `building_group`. There is **no** `production_method` or
`production_method_group` scope, which rules out storing active methods as scopes in a variable
list. Combined with §8 this forces the generated-script approach described in ARCHITECTURE.md.

Triggers confirmed available from `triggers_l_english.yml`: `has_building` (state, takes a
building type), `is_building_type` (building), `has_active_production_method` (building),
`is_production_method_active` (country/state, takes building type + method).

## Sources

* Installed game files, Victoria 3 1.13 (`D:\SteamLibrary\steamapps\common\Victoria 3\game`)
* [Modding - Victoria 3 Wiki](https://vic3.paradoxwikis.com/Modding)
* [Scripted gui - Victoria 3 Wiki](https://vic3.paradoxwikis.com/Scripted_gui)
* [Building modding - Victoria 3 Wiki](https://vic3.paradoxwikis.com/Building_modding)
* [Scope - Victoria 3 Wiki](https://vic3.paradoxwikis.com/Scope)
* [Patch 1.13 - Victoria 3 Wiki](https://vic3.paradoxwikis.com/Patch_1.13)
