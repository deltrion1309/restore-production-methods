# Publishing to the Steam Workshop

## Before you upload

1. **Bump the version** in `.metadata/metadata.json`. The launcher shows it, and Workshop
   subscribers get the update when it changes.
2. **Package a clean folder.** During development the game's mod folder holds a junction pointing
   at this repository. Do not upload that: the launcher uploads *everything* in the folder, which
   through the junction means `.git`, `dev/`, `docs/` and `build/` — the entire history, published
   to Steam.

   ```powershell
   cd "D:\Code\Victoria 3 mod"
   .\dev\package.ps1
   ```

   That replaces the junction with a real folder containing only `.metadata/`, `common/`,
   `events/`, `localization/` and `thumbnail.png`.

## Uploading

3. Close Victoria 3, open the **Paradox launcher**.
4. Go to the mods list, find **Restore Production Methods**, and use its upload-to-Workshop
   action. The first upload asks you to accept Steam's Workshop Legal Agreement.
5. The launcher creates the Workshop item and writes a `steamcmd` folder into the mod directory
   holding the published file id. Keep that folder — it is how later uploads find the same item
   instead of creating a second one.

New Workshop items are created **hidden**. Nothing is public until you say so.

## Filling in the listing

6. Open the item on Steam. Paste
   [workshop-description.bbcode.txt](workshop-description.bbcode.txt) into the description field,
   upload `docs/workshop-banner.png` as the listing image, set the tags, and only then set
   visibility to Public.

   The launcher does not show a thumbnail for a local, unpublished mod in every version — the
   Workshop item picks `thumbnail.png` up at upload time regardless, so a blank tile in the
   library before publishing is not a problem to chase.

## Afterwards

7. Put the development junction back:

   ```powershell
   .\dev\deploy.ps1 -Force
   ```

## Updating later

Bump the version, run `package.ps1`, upload again from the launcher, run `deploy.ps1 -Force`. As
long as the `steamcmd` folder survives, it updates the existing item rather than creating a new
one.

## If the upload misbehaves

The exact wording and placement of the launcher's upload button changes between launcher
versions, so hunt around the mod entry rather than trusting a screenshot. If the upload reports
nothing to upload, or uploads a folder that looks wrong, check that `package.ps1` actually
replaced the junction with a real folder — a link is the most likely culprit.
