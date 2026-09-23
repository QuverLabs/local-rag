param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$NotesDir,
    [string]$ConfigPath
)

$ErrorActionPreference = "Stop"
$Image = "local-rag:dev"
$NotesPath = (Resolve-Path -LiteralPath $NotesDir).Path
if (-not (Get-ChildItem -LiteralPath $NotesPath -Filter "*.md" -File -Recurse | Select-Object -First 1)) {
    throw "No Markdown files found below $NotesPath"
}

$DockerCommand = (Get-Command docker -ErrorAction Stop).Source
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker is not running. Start Docker Desktop." }

$RepoDir = Split-Path -Parent $PSScriptRoot
docker build --platform linux/amd64 -t $Image $RepoDir
if ($LASTEXITCODE -ne 0) { throw "docker build failed" }

if (-not $ConfigPath) {
    $ConfigPath = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
}
$ConfigPath = [IO.Path]::GetFullPath($ConfigPath)
$ConfigDir = Split-Path -Parent $ConfigPath
$ConfigName = Split-Path -Leaf $ConfigPath
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

docker run --rm `
    --platform linux/amd64 `
    --user 0:0 `
    --entrypoint python `
    --mount "type=bind,source=$ConfigDir,target=/claude" `
    $Image -m setup.install_claude_desktop `
    --docker `
    --config-path "/claude/$ConfigName" `
    --docker-command $DockerCommand `
    --notes-dir $NotesPath
if ($LASTEXITCODE -ne 0) { throw "Claude Desktop configuration failed" }
