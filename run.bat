@echo off
cd /d "%~dp0"
echo Запуск ГосДума Маркет на http://0.0.0.0:8000 (доступен в локальной сети)
"C:\Program Files\Python313\python.exe" -m uvicorn app:app --host 0.0.0.0 --port 8000
