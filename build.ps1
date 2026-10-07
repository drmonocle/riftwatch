Set-ExecutionPolicy -Scope Process Bypass -Force
$xwinBin = "C:\Users\TV\.xwin\bin"
$cargoPath = "C:\Users\TV\.cargo\bin"
$nodePath = "C:\Users\TV\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.19.0-win-x64"
$llvmPath = "C:\Users\TV\AppData\Local\Microsoft\WinGet\Packages\MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\llvm-mingw-20260616-ucrt-x86_64\bin"
$env:Path = "$xwinBin;$cargoPath;$nodePath;$llvmPath;$env:Path"

Write-Host "Building Vite frontend..."
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Vite build failed!"
    exit 1
}

Write-Host "Vite build succeeded!"
