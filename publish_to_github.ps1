param(
  [string]$RepoUrl = "https://github.com/meng0614/paper-to-group-meeting-ppt.git"
)

$ErrorActionPreference = "Stop"
$SkillDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Git = "C:\Users\30430\Documents\research\research_tools\portable_git\cmd\git.exe"

if (-not (Test-Path -LiteralPath $Git)) {
  throw "Portable git not found: $Git"
}

Set-Location -LiteralPath $SkillDir

& $Git config --global --add safe.directory $SkillDir.Replace("\", "/")

if (-not (Test-Path -LiteralPath ".git")) {
  & $Git init
  & $Git branch -m main
}

$remote = (& $Git remote) -join "`n"
if ($remote -notmatch "(?m)^origin$") {
  & $Git remote add origin $RepoUrl
} else {
  & $Git remote set-url origin $RepoUrl
}

& $Git add .

$status = (& $Git status --porcelain) -join "`n"
if ($status.Trim().Length -gt 0) {
  & $Git -c user.name="Codex Research Assistant" -c user.email="codex@example.com" commit -m "Initial paper-to-group-meeting-ppt skill"
}

& $Git push -u origin main
