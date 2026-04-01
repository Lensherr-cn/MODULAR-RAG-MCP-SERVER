@echo off
REM 启动后端服务脚本 (Windows)

echo ========================================
echo Enterprise Knowledge Hub API
echo ========================================
echo.

REM 获取脚本所在目录
cd /d "%~dp0"

REM 检查虚拟环境
if exist "..\.venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "..\.venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ".venv\Scripts\activate.bat"
)

REM 设置环境变量
set DEBUG=true
set HOST=0.0.0.0
set PORT=8000

echo Starting server...
echo API Docs: http://localhost:8000/docs
echo.

REM 启动服务
python -m uvicorn app.main:app --host %HOST% --port %PORT% --reload --log-level info
