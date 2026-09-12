# Development notes

## Installing

The repository root is the mod root. Link it into the game's mod folder rather than copying it:

```powershell
.\dev\deploy.ps1
```

Then in the Paradox launcher: **Mods -> All installed mods**, add *Restore Production Methods*
to a playset, make sure its toggle is on, and launch. Script and event changes need the game
restarted (or the `reload` console command); scripted GUI changes always need a full restart.

Never keep a copied second set of these files under the mod folder, and never leave a second
junction there under a different name. The launcher scans every subfolder of the mod folder, so
two folders carrying the same mod id appear as the same mod twice - and the game loads whichever
one it finds, which may be the stale copy. `deploy.ps1` removes both kinds of duplicate: it
deletes other links pointing at this repository, and moves a real folder at the target out of
the mod folder entirely rather than leaving a `.bak` behind for the launcher to pick up.

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

## Regenerating the building script

`common/scripted_effects/rpm_generated_effects.txt` is generated, never edited by hand:

```powershell
python dev/generate_pm_script.py --source "D:\SteamLibrary\steamapps\common\Victoria 3\game"
```

Add a `--source` for each mod folder whose buildings or production methods should be covered,
in load order - later sources override earlier ones by file name, the same way the game does.
Re-run it after a game patch or a change of mod set.

## Conventions

* Tabs for indentation, matching Paradox's own files.
* Every script object, localization key and event is prefixed `rpm_`.
* Every `.txt` and `.yml` file must be saved as **UTF-8 with BOM**. Localization without it is
  silently ignored; script without it logs a warning for every file.
* Never override a vanilla file. Hook on_actions additively instead.
