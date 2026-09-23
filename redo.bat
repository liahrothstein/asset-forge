@echo off
del "work\ref\%1.png" "work\raw\%1.obj" "assets\%1.glb" 2>nul
del "work\cut\%1.png" 2>nul
echo [%1] очищен, готов к перегенерации