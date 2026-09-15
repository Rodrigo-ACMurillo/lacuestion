# Instala las fuentes .ttf de esta carpeta solo para el usuario actual (no requiere administrador).
# Uso: clic derecho > «Ejecutar con PowerShell». Después, cierra y vuelve a abrir Word.
$destino = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
New-Item -ItemType Directory -Force -Path $destino | Out-Null
$registro = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts"
if (-not (Test-Path $registro)) { New-Item -Path $registro -Force | Out-Null }

Get-ChildItem -Path $PSScriptRoot -Filter *.ttf | ForEach-Object {
    $archivo = Join-Path $destino $_.Name
    Copy-Item -Path $_.FullName -Destination $archivo -Force
    $nombre = [IO.Path]::GetFileNameWithoutExtension($_.Name) + " (TrueType)"
    New-ItemProperty -Path $registro -Name $nombre -Value $archivo -PropertyType String -Force | Out-Null
    Write-Output ("Instalada: " + $_.Name)
}
Write-Output "Listo. Cierra y vuelve a abrir Word para ver las fuentes."
