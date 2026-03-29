@echo off
echo ========================================
echo   Toothless Solar Buildings Map
echo   Starting All Services...
echo ========================================
echo.

REM Start Database
echo [1/3] Starting Database...
docker-compose up -d
timeout /t 10 /nobreak > nul

REM Start Backend API
echo [2/3] Starting Backend API...
start "Backend API" cmd /k "cd backend && python api.py"
timeout /t 3 /nobreak > nul

REM Start Frontend
echo [3/3] Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo   All Services Started!
echo ========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8001
echo   Database: localhost:5432
echo.
echo   Press any key to exit...
pause > nul
