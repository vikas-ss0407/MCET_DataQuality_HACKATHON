@echo off
echo.
echo ===== Data Quality Guardian - Quick Start =====
echo.
echo Starting Backend (FastAPI)...
start cmd /k "cd backend && pip install -r requirements.txt && uvicorn main:app --reload"
echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak
echo.
echo Starting Frontend (React + Vite)...
start cmd /k "cd frontend && npm install && npm start"
echo.
echo ===== Services Starting =====
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo.
echo Sample CSV: sample_data.csv
echo Documentation: README.md
echo.
pause
