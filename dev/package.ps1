<#
.SYNOPSIS
	Replaces the development junction with a clean folder ready for Workshop upload.

.DESCRIPTION
	During development the game's mod folder holds a junction pointing at this
	repository, so the game loads what you are editing. That is the wrong thing to
	upload: the Paradox launcher uploads the whole folder, which would include
	.git, dev/, docs/ and build/ - your entire history, published to Steam.

	This script removes the junction and writes a real folder in its place
	containing only the files the mod needs. Upload that, then run
	.\dev\deploy.ps1 -Force to put the junction back and carry on developing.

	Nothing is deleted from the repository, and the junction is only ever removed
	as a link - never followed.

.EXAMPLE
	.\dev\package.ps1
	# ... upload in the launcher ...
	.\dev\deploy.ps1 -Force
#>
[CmdletBinding()]
param(
	[string]$ModFolderName = 'Restore Production Methods'
)

$ErrorActionPreference = 'Stop'

# Everything the game actually reads, plus the Workshop thumbnail.
$SHIP = @('.metadata', 'common', 'events', 'localization', 'thumbnail.png')

$repoRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
$modRoot  = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Victoria 3\mod'
$target   = Join-Path $modRoot $ModFolderName

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.metadata\metadata.json'))) {
	throw "Could not find .metadata\metadata.json under '$repoRoot'. Run this from the repository."
}
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'thumbnail.png'))) {
	throw "thumbnail.png is missing from '$repoRoot'. The Workshop item needs it."
}

if (Test-Path -LiteralPath $target) {
	$item = Get-Item -LiteralPath $target -Force
	if ($item.LinkType) {
		$item.Delete()                       # removes the link, not the repository
		Write-Host "Removed the development junction." -ForegroundColor Yellow
	} else {
		Remove-Item -LiteralPath $target -Recurse -Force
		Write-Host "Removed the previous packaged folder." -ForegroundColor Yellow
	}
}

New-Item -ItemType Directory -Path $target | Out-Null
foreach ($name in $SHIP) {
	$source = Join-Path $repoRoot $name
	if (-not (Test-Path -LiteralPath $source)) {
		Write-Host "skipping '$name' (not present)" -ForegroundColor DarkGray
		continue
	}
	Copy-Item -LiteralPath $source -Destination $target -Recurse
}

$version = (Get-Content -LiteralPath (Join-Path $repoRoot '.metadata\metadata.json') -Raw | ConvertFrom-Json).version
$bytes = (Get-ChildItem -LiteralPath $target -Recurse -File | Measure-Object -Property Length -Sum).Sum

Write-Host ""
Write-Host "Packaged version $version into '$target' ($([math]::Round($bytes / 1MB, 2)) MB)" -ForegroundColor Green
Write-Host "Upload it from the Paradox launcher, then run .\dev\deploy.ps1 -Force to restore the junction." -ForegroundColor Green
