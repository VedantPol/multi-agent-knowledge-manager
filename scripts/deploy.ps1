param(
  [Parameter(Mandatory = $true)]
  [string]$HostName,

  [Parameter(Mandatory = $true)]
  [string]$User,

  [string]$RemotePath = "/opt/mak",
  [string]$Port = "8000"
)

$ErrorActionPreference = "Stop"

$target = "$User@$HostName"
$archive = "mak-deploy.tar.gz"

tar --exclude ".git" --exclude ".venv" --exclude "data" --exclude ".env" -czf $archive .
ssh $target "mkdir -p $RemotePath"
scp $archive "${target}:${RemotePath}/$archive"
ssh $target "cd $RemotePath && tar -xzf $archive && rm $archive && if [ ! -f .env ]; then cp .env.example .env; fi && docker compose up -d --build"
Remove-Item -LiteralPath $archive

Write-Host "Deployed to http://${HostName}:${Port}"
