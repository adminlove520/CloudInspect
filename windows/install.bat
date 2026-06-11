@echo off
chcp 65001 > nul
echo ====================================
echo CloudInspect Windows - 安装脚本
echo ====================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] 找到 Python
echo.

:: 安装依赖
echo [INFO] 正在安装 Python 依赖...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] 依赖安装失败
    echo 尝试使用管理员权限重新运行
    pause
    exit /b 1
)

echo.
echo [OK] 依赖安装完成
echo.

:: 检查 PowerShell
echo [INFO] 检查 PowerShell 版本...
powershell -Command "$PSVersionTable.PSVersion" > nul 2>&1
if errorlevel 1 (
    echo [WARN] PowerShell 不可用，部分功能可能受限
)

echo.
echo ====================================
echo 安装完成
echo ====================================
echo.
echo 运行巡检:
echo   python inspect.py
echo.
echo 查看帮助:
echo   python inspect.py --help
echo.
pause