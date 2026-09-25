@echo off
call C:\Users\Dmitry\miniconda3\Scripts\activate.bat kohya
cd /d D:\Development\third_party\kohya_ss
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set "PATH=D:\Development\third_party\kohya_ss\venv\Scripts;%PATH%"
D:\Development\third_party\kohya_ss\venv\Scripts\python.exe kohya_gui.py