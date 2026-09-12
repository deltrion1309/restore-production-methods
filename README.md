# Restore Production Methods

A Victoria 3 mod for the aftermath of civil wars.

When a **revolution** or **secession** breaks out, the states that defect are handed to a rebel
AI country. While that AI holds them it happily flips production methods, expands buildings and
raises battalions to suit *its* economy — not yours. When you win the war back, you inherit the
mess, and vanilla gives you no record of what changed.

This mod:

1. **Snapshots** every affected state the moment it defects — building levels and the active
   production method of every building.
2. **Reports** what the AI changed once you regain the states, as a summary event
   (e.g. *"20 production methods changed in 11 buildings across 3 states"*).
3. **Restores** — from that same event you can put production methods, barracks, conscription
   centres and building levels back to their pre-war state.

## Status

Early development. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design and
[docs/RESEARCH.md](docs/RESEARCH.md) for the verified engine facts the design rests on.

| Phase | Feature | Status |
|-------|---------------------------------|--------------------------|
| 1     | Pre-war snapshot                | implemented, hooks verified in-game |
| 2     | Post-war summary event          | implemented, untested    |
| 3     | Restore actions                 | generated, not wired to the UI yet |

Production methods **and** building levels are both snapshotted. The per-building script is
generated from the game's own data by `dev/generate_pm_script.py` — see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for why, and re-run it after a game patch or when
you change your mod set:

```powershell
python dev/generate_pm_script.py --source "D:\SteamLibrary\steamapps\common\Victoria 3\game"
```

## Compatibility

* Target game version: **1.13.\*** (Matcha)
* Overrides no vanilla files. All engine `on_action` hooks are attached using the additive
  `on_actions = { ... }` chaining pattern that Paradox documents in
  `game/common/on_actions/_on_actions.md`, so it should coexist with other mods.
* All script objects are namespaced with the `rpm_` prefix.

## Development

The repository root *is* the mod root, so it can be linked straight into the game's mod folder.

```powershell
# From the repo root, with Victoria 3 and the Paradox launcher closed:
.\dev\deploy.ps1
```

That creates a directory junction at
`%USERPROFILE%\Documents\Paradox Interactive\Victoria 3\mod\Restore Production Methods`
pointing at your working copy, so edits are live without copying anything. If a real folder is
already there it is moved aside to `...bak` rather than deleted. Pass `-ModFolderName` if the
launcher knows the mod by a different name.

Then open the launcher, add **Restore Production Methods** to a playset, enable it, and play.
Do not keep a second copy of these files under the mod folder — two copies drift apart, and the
game will happily load the stale one.

See [dev/README.md](dev/README.md) for the test loop.

## Licence

Not yet decided.
