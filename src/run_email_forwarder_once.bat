@echo off
REM 邮件自动转发程序单次运行脚本（用于测试）
chcp 65001 >nul
echo ========================================
echo 邮件自动转发程序 - 单次运行（测试模式）
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 切换到脚本所在目录
cd /d %~dp0

REM 运行邮件转发程序（单次）
python email_forwarder.py --once

pause
