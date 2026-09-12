<#
.SYNOPSIS
	Links this working copy into the Victoria 3 mod folder.

.DESCRIPTION
	Creates a directory junction at
		%USERPROFILE%\Documents\Paradox Interactive\Victoria 3\mod\<ModFolderName>
	pointing at the repository root, so the game loads the files you are editing with no copy
	step.

	Keeping exactly one entry matters: the Paradox launcher scans every subfolder of the mod
	folder, so a leftover copy or a junction under a second name shows up as a duplicate mod
	with the same id. This script therefore also removes any other link in the mod folder that
	points at this repository, and moves a real folder sitting at the target OUT of the mod
	folder rather than leaving a .bak behind for the launcher to find.

	A junction (not a symlink) is used on purpose: junctions do not need administrator rights
	or developer mode on Windows.

.EXAMPLE
	.\dev\deploy.ps1
	.\dev\deploy.ps1 -Force
#>
[CmdletBinding()]
param(
	# Folder name to create inside the game's mod folder. Must match the name the
	# Paradox launcher knows the mod by, if you created it there.
	[string]$ModFolderName = 'Restore Production Methods',
	[switch]$Force
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$modRoot  = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Victoria 3\mod'
$linkPath = Join-Path $modRoot $ModFolderName

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.metadata\metadata.json'))) {
	throw "Could not find .metadata\metadata.json under '$repoRoot'. Run this from the repository."
}

if (-not (Test-Path -LiteralPath $modRoot)) {
	throw "Victoria 3 mod folder not found at '$modRoot'. Start the game's launcher once to create it."
}

# --- Remove stray links elsewhere in the mod folder that point at this repository ----------
Get-ChildItem -LiteralPath $modRoot -Directory -Force | ForEach-Object {
	if (-not $_.LinkType) { return }
	if ($_.FullName -eq $linkPath) { return }

	$target = @($_.Target)[0]
	if ($target -and ($target.TrimEnd('\') -ieq $repoRoot.TrimEnd('\'))) {
		Write-Host "Removing duplicate link '$($_.FullName)'" -ForegroundColor Yellow
		$_.Delete()
	}
}

# --- Deal with whatever is at the target ---------------------------------------------------
if (Test-Path -LiteralPath $linkPath) {
	$item = Get-Item -LiteralPath $linkPath -Force

	if ($item.LinkType) {
		if (-not $Force -and (@($item.Target)[0].TrimEnd('\') -ieq $repoRoot.TrimEnd('\'))) {
			Write-Host "'$linkPath' already points at this repository. Nothing to do." -ForegroundColor Green
			return
		}
		$item.Delete()
	}
	else {
		if (-not $Force) {
			Write-Host "'$linkPath' is a real folder. Re-run with -Force to move it aside and link in its place." -ForegroundColor Yellow
			return
		}

		# Move it OUT of the mod folder - a .bak left inside would still be scanned by the
		# launcher and show up as a duplicate mod.
		$stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
		$parked = Join-Path (Split-Path -Parent $repoRoot) "$ModFolderName.replaced-$stamp"
		Move-Item -LiteralPath $linkPath -Destination $parked
		Write-Host "Moved the old copy to '$parked'. Delete it once the game loads the mod correctly." -ForegroundColor Yellow
	}
}

New-Item -ItemType Junction -Path $linkPath -Target $repoRoot | Out-Null
Write-Host "Linked '$linkPath' -> '$repoRoot'" -ForegroundColor Green

# --- Warn about any other folder claiming the same mod id ---------------------------------
# The launcher reads .metadata\metadata.json from every subfolder regardless of its name, so a
# leftover copy (even one called *.bak) still shows up as this mod a second time.
$ourId = (Get-Content -LiteralPath (Join-Path $repoRoot '.metadata\metadata.json') -Raw | ConvertFrom-Json).id
Get-ChildItem -LiteralPath $modRoot -Directory -Force | ForEach-Object {
	if ($_.FullName -eq $linkPath) { return }
	$meta = Join-Path $_.FullName '.metadata\metadata.json'
	if (-not (Test-Path -LiteralPath $meta)) { return }
	try { $id = (Get-Content -LiteralPath $meta -Raw | ConvertFrom-Json).id } catch { return }
	if ($id -eq $ourId) {
		Write-Host "WARNING: '$($_.FullName)' also declares mod id '$ourId'." -ForegroundColor Red
		Write-Host "         The launcher will list the mod twice until you delete or move that folder." -ForegroundColor Red
	}
}
Write-Host "Restart the Paradox launcher, then add 'Restore Production Methods' to a playset." -ForegroundColor Green
