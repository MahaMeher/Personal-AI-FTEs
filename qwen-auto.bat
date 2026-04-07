@echo off
REM Qwen Code Wrapper with YOLO Mode
REM Personal AI FTEs Project - Gold Tier

REM Usage: qwen-auto.bat "your prompt here"

if "%~1"=="" (
    echo Usage: qwen-auto.bat "your prompt here"
    echo Example: qwen-auto.bat "Post to Facebook: Hello World!"
    exit /b 1
)

REM Run Qwen Code with -y flag for automatic tool execution
echo Running Qwen Code in automatic mode...
echo.

qwen -p "%~1" -y

echo.
echo Done!
