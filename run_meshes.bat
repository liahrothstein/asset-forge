@echo off
cd /d D:\Development\third_party\Hunyuan3D-2
set "HY3DGEN_MODELS=E:\hf_cache\hy3dgen"
set "MAX_FACES=8000"
call C:\Users\Dmitry\miniconda3\Scripts\activate.bat assethy
python gen_meshes_hy.py > D:\Development\asset-forge\work\logs\meshes.log 2>&1