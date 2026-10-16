param (
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("up", "down", "build", "logs", "ps", "test", "audit", "whoami")]
    [string]$Action
)



# Agregar directorio de Docker a PATH del proceso para docker-credential-desktop
$dockerDir = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin"
if (Test-Path $dockerDir) {
    $env:PATH = "$dockerDir;$env:PATH"
}

$cmd = Get-Command docker -ErrorAction SilentlyContinue
if ($cmd) {
    $dockerBin = $cmd.Source
} else {
    $candidate = "$dockerDir\docker.exe"
    if (Test-Path $candidate) {
        $dockerBin = $candidate
    } else {
        Write-Error "No se encontró el ejecutable de Docker. Verifique la instalación de Docker Desktop."
        exit 1
    }
}

switch ($Action) {
    "up" {
        if (-not (Test-Path ".env")) {
            Copy-Item ".env.example" ".env"
            Write-Host "Se generó .env a partir de .env.example" -ForegroundColor Yellow
        }
        & $dockerBin compose up -d --build
    }
    "down" {
        & $dockerBin compose down
    }
    "build" {
        & $dockerBin compose build
    }
    "logs" {
        & $dockerBin compose logs -f
    }
    "ps" {
        & $dockerBin compose ps
    }
    "test" {
        & $dockerBin compose exec backend pytest
    }
    "audit" {
        & $dockerBin compose exec backend pip-audit
    }
    "whoami" {
        & $dockerBin compose exec backend id
    }
}


