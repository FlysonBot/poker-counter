param (
    [switch]$nozip
)

& .\.venv\Scripts\activate.ps1
pyinstaller -y main.spec
Remove-Item .\build -Recurse -Force
Copy-Item .\src\config.yaml .\dist\main\config.yaml
Copy-Item .\README.md .\dist\main\README.md

if (-not $nozip) {
    $tomlContent = Get-Content .\pyproject.toml -Raw

    if ($tomlContent -match 'version\s*=\s*"([^"]+)"') {
        $version = $Matches[1]
        Compress-Archive -Path .\dist\main\* -DestinationPath .\dist\poker-counter_v$version.zip -Force
    } else {
        Write-Error "Version number not found in pyproject.toml. Archiving as main.zip"
        Compress-Archive -Path .\dist\main\* -DestinationPath .\dist\main.zip -Force
    }
} else {
    Write-Host "Skipping zipping process as -nozip argument was provided."
}
