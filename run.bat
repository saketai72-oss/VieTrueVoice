@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

set "PORT=%~1"
if "%PORT%"=="" set "PORT=8000"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "DEVICE=cuda"
set "CUDA_VISIBLE_DEVICES=0"

if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

echo ====================================================================
echo   VieTrueVoice v0.9.4 // Local CUDA Forensics Server
echo ====================================================================

"%PY_EXE%" -c "import torch; cuda = torch.cuda.is_available(); name = torch.cuda.get_device_name(0) if cuda else 'CPU (CUDA unavailable)'; print(f'[GPU] PyTorch {torch.__version__} | CUDA={cuda} | Device={name}')"
if errorlevel 1 (
    echo [ERROR] Khong tim thay Python/PyTorch hop le ^(%PY_EXE%^).
    pause
    exit /b 1
)

if not exist "out\v0.9.4\best_model.pt" (
    echo [WARN] Khong tim thay out\v0.9.4\best_model.pt - he thong se thu checkpoint du phong.
)

REM Check if requested port is already in use (e.g. Docker container on 8000)
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [ERROR] Cong %PORT% dang duoc su dung ^(vi du: container Docker vietruevoice-api^).
    echo         Dung Docker:  docker compose stop api
    echo         Hoac chay cong khac:  run.bat 8010
    pause
    exit /b 1
)

echo [URL] Web UI:      http://localhost:%PORT%/
echo [URL] Swagger API: http://localhost:%PORT%/docs
echo [CMD] %PY_EXE% -m uvicorn src.app.server:app --host 0.0.0.0 --port %PORT%
echo --------------------------------------------------------------------

"%PY_EXE%" -m uvicorn src.app.server:app --host 0.0.0.0 --port %PORT%
if errorlevel 1 (
    echo.
    echo [ERROR] Server dung dot ngot voi ma loi %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)
endlocal
