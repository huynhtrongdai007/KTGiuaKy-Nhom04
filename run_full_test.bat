@echo off
echo Starting Server and 2 Clients...

start "Caro Server" cmd /c "python server.py & pause"
timeout /t 1 >nul
start "Caro Client 1" cmd /c "python client.py & pause"
start "Caro Client 2" cmd /c "python client.py & pause"

echo Done.
