# Development notes

## Test loop

1. `.\dev\deploy.ps1` once, to link the working copy into the mod folder.
2. Enable the mod in a launcher playset.
3. Add `-debug_mode` to the game's launch options. This unlocks the console **and** makes the
   game write its script reference logs, which are the authoritative syntax documentation:
   `Documents\Paradox Interactive\Victoria 3\logs\event_scopes.log`, `effects.log`,
   `triggers.log`, `event_targets.log`.
4. After every run, read `Documents\Paradox Interactive\Victoria 3\logs\error.log`.
   Paradox script fails silently in game — the error log is the only feedback there is.
   A clean run means the file parsed, not that the logic is right.

## Useful console commands (debug mode)

| Command | Use |
|---|---|
| `effect <...>` | run an effect on the selected scope, to test a restore by hand |
| `event rpm_events.1` | fire the summary event directly |
| `civil_war` / `revolution` | force a civil war to test Phase 1 without waiting |
| `annex <TAG>` | get the states back quickly to test Phase 2 |

## Reloading

* `common/` script and `events/` reload in-game with the `reload` console command.
* `common/scripted_guis/` does **not** — it needs a full game restart.
* Localization reloads with `reloadloc`.

## Conventions

* Tabs for indentation, matching Paradox's own files.
* Every script object, localization key and event is prefixed `rpm_`.
* Localization `.yml` files must be saved as **UTF-8 with BOM** or the game silently ignores them.
* Never override a vanilla file. Hook on_actions additively instead.
