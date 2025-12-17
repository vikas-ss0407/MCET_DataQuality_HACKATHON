#!/bin/bash

echo ""
echo "===== Data Quality Guardian - Quick Start ====="
echo ""

echo "Starting Backend (FastAPI)..."
cd backend
pip install -r requirements.txt
uvicorn main:app --reload &
BACKEND_PID=$!

echo ""
echo "Waiting 3 seconds..."
sleep 3

echo ""
echo "Starting Frontend (React + Vite)..."
cd ../frontend
npm install
npm start &
FRONTEND_PID=$!

echo ""
echo "===== Services Starting ====="
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:5173"
echo ""
echo "Sample CSV: sample_data.csv"
echo "Documentation: README.md"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

wait
