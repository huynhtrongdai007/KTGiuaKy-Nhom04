@echo off
echo Dang tat Server va Client...
echo.

REM Tat cua so Server
taskkill /F /FI "WINDOWTITLE eq Caro Server*" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Da tat Server
) else (
    echo [--] Khong tim thay Server
)

REM Tat cua so Client
taskkill /F /FI "WINDOWTITLE eq Caro Client*" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Da tat Client
) else (
    echo [--] Khong tim thay Client
)

echo.
echo Hoan tat!
pause
