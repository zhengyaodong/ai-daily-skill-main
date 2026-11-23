@echo off
REM 邮件自动转发程序启动脚本
chcp 65001 >nul
echo ========================================
echo 邮件自动转发程序
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

REM 检查是否有 .env 文件
if not exist .env (
    echo [警告] 未找到 .env 文件
    echo 请先配置环境变量（参考 EMAIL_FORWARDER_README.md）
    echo.
    echo 按任意键继续...
    pause >nul
)

REM 运行邮件转发程序
echo 正在启动邮件转发程序...
echo 按 Ctrl+C 可以停止程序
echo.
python email_forwarder.py

pause
