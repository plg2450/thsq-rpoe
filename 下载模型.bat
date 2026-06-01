@echo off
chcp 65001 >nul
echo ========================================
echo   下载 Wav2Lip 唇形同步模型
echo ========================================
echo.
echo 模型文件: wav2lip_gan.pth (约 400MB)
echo 下载地址: https://drive.google.com/file/d/1dYy1K2d1O5w8e0vl0f59Wf1jYbqt2h7d/view
echo.
echo 请手动下载模型文件，然后放到以下目录:
echo %~dp0models\Wav2Lip\checkpoints\
echo.
echo 下载完成后按任意键继续...
pause >nul

if exist "%~dp0models\Wav2Lip\checkpoints\wav2lip_gan.pth" (
    echo.
    echo ✓ 模型文件已存在！
) else (
    echo.
    echo ✗ 模型文件不存在，请先下载！
)
echo.
pause
