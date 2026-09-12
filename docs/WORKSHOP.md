# Workshop listing

Draft copy for the Steam Workshop page. Keep it in step with the README.

## Title

Restore Production Methods

## Short description

Snapshots your states when a revolution or secession takes them, reports what the rebel AI
changed, and lets you put it back when you win them again.

## Description

When a revolution or secession breaks out, the states that defect are handed to a rebel AI. While
it holds them it rearranges your industry to suit its own economy — flipping production methods,
expanding buildings, raising troops. Win the war and you inherit the mess, with no record of what
was touched.

This mod keeps the record.

**It snapshots** every state the moment it defects: the level of every building and the active
production method of every production method group.

**It reports** what changed once the states are yours again, in a single summary — how many
production methods were changed, in how many buildings, across how many states; what was expanded
and by how many levels; what the rebels built from nothing.

**It puts things back**, from buttons in that same summary:

* restore every production method to what it was before the war
* undo the rebels' building expansions
* shrink barracks back to their pre-war size
* shrink conscription centres back to their pre-war size

Nothing is ever demolished and nothing is ever built up. Buildings the rebels raised from nothing
are left standing, and a building the rebels shrank stays shrunk — the mod only undoes what it can
undo, and says so.

It is also honest about what it cannot do. A production method that a law or technology no longer
permits is reported separately rather than silently skipped. Buildings that grow on their own —
urban centres, manor houses, subsistence farms — are listed as such rather than blamed on the
rebels, because nothing in the game can resize them.

### Compatibility

* Built and tested against **1.13**.
* Overrides no vanilla files. Every hook uses Paradox's own additive `on_actions` pattern, so it
  should sit happily beside other mods.
* Works with modded buildings and modded production methods: the per-building script is generated
  from the game's own data files, and the generator can be pointed at your whole mod set.
* Single player. Not tested in multiplayer.
* Snapshots are only taken for human players, so it costs nothing in AI civil wars.

### Notes

* Shrinking a building rebuilds it, which resets its production methods — so the mod puts those
  back at the same time. For barracks this means the battalions are raised fresh.
* Source, and a long account of what the engine will and will not allow, at
  https://github.com/deltrion1309/restore-production-methods

## Tags

Utilities, Gameplay, 1.13

## Thumbnail

`thumbnail.png` in the repository root — the "states" design: a grid of states, the ones the
rebels disturbed in red, the ones set right in green. Regenerate with
`python dev/make_thumbnail.py --only states` and copy it to the root.

## Listing image

`docs/workshop-banner.png` — 1280×720, the same design as the thumbnail with room for the pitch.
Regenerate with `python dev/make_thumbnail.py --only banner`.

## Screenshots, if you ever want them

Not required — the banner carries the listing on its own. If in-game captures are wanted later,
the ones worth having are the summary event with its counters filled in, and a building panel
before and after a production method restore.
