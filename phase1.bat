@echo off
cd /d D:\Development\asset-forge
D:\Development\third_party\kohya_ss\venv\Scripts\python.exe gen_images_kohya.py %1
start explorer work\ref