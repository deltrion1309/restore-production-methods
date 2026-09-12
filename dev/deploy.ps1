<#
.SYNOPSIS
	Links this working copy into the Victoria 3 mod folder.

.DESCRIPTION
	Creates a directory junction at
		%USERPROFILE%\Documents\Paradox Interactive\Victoria 3\mod\restore-production-methods
	pointing at the repository root, so the game loads the files you are editing with no copy
	step. Run it once. Re-run with -Force to replace an existing link.

	A junction (not a symlink) is used on purpose: junctions do not need administrator rights
	or developer mode on Windows.

.EXAMPLE
	.\dev\deploy.ps1
	.\dev\deploy.ps1 -Force
#>
[CmdletBinding()]
param(
	[switch]$Force
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$modName  = 'restore-production-methods'
$modRoot  = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Victoria 3\mod'
$linkPath = Join-Path $modRoot $modName

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.metadata\metadata.json'))) {
	throw "Could not find .metadata\metadata.json under '$repoRoot'. Run this from the repository."
}

if (-not (Test-Path -LiteralPath $modRoot)) {
	throw "Victoria 3 mod folder not found at '$modRoot'. Start the game's launcher once to create it."
}

if (Test-Path -LiteralPath $linkPath) {
	if (-not $Force) {
		Write-Host "'$linkPath' already exists. Re-run with -Force to replace it." -ForegroundColor Yellow
		return
	}
	$item = Get-Item -LiteralPath $linkPath -Force
	if ($item.LinkType) {
		$item.Delete()
	} else {
		throw "'$linkPath' exists and is a real folder, not a link. Move it aside yourself first."
	}
}

New-Item -ItemType Junction -Path $linkPath -Target $repoRoot | Out-Null
Write-Host "Linked '$linkPath' -> '$repoRoot'" -ForegroundColor Green
Write-Host "Enable 'Restore Production Methods' in the Victoria 3 launcher playset." -ForegroundColor Green
