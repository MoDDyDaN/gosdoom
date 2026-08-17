@echo off
chcp 65001 >nul
cd /d "%~dp0"
set CLOUDFLARED=C:\cloudflared\cloudflared.exe
set CFDIR=%USERPROFILE%\.cloudflared

echo ============================================================
echo  Настройка постоянного туннеля Cloudflare для gosdoom
echo ============================================================
echo.
echo  ПРЕДВАРИТЕЛЬНО (вручную в браузере):
echo   1. Домен eu.org одобрен и виден в https://nic.eu.org
echo   2. Домен добавлен в Cloudflare: https://dash.cloudflare.com/?to=/:account/add-site
echo   3. В панели eu.org (Advanced / DNS) прописаны NS-серверы Cloudflare:
echo      %DNS1% %DNS2%
echo   DNS-статус в Cloudflare должен стать "Active", не "Pending".
echo.
set /p GO="Готово? Нажмите Enter чтобы продолжить (или Ctrl+C для отмены)..."
if errorlevel 1 exit

echo.
echo [1/5] Авторизация в Cloudflare (выберите свой домен в браузере)...
"%CLOUDFLARED%" tunnel login
if not exist "%CFDIR%\cert.pem" (
  echo ОШИБКА: сертификат не создан. Повторите авторизацию.
  pause
  exit /b 1
)

echo.
echo [2/5] Создание туннеля "gosdoom"...
"%CLOUDFLARED%" tunnel create gosdoom

echo.
echo [3/5] Подключение доменного адреса. Введите ваш домен (например, site.eu.org):
set /p DOMAIN="Домен: "
"%CLOUDFLARED%" tunnel route dns gosdoom %DOMAIN%

echo.
echo [4/5] Создание конфига...
(
  echo tunnel: gosdoom
  echo credentials-file: %CFDIR%\gosdoom.json
  echo.
  echo ingress:
  echo   - hostname: %DOMAIN%
  echo     service: http://localhost:8000
  echo   - service: http_status:404
) > "%CFDIR%\config.yml"
echo Готово. Конфиг: %CFDIR%\config.yml

echo.
echo [5/5] Установка автозапуска при загрузке Windows...
"%CLOUDFLARED%" service install

echo.
echo ============================================================
echo  ГОТОВО. Сайт будет доступен на постоянном адресе:
echo    https://%DOMAIN%
echo  Туннель запустится автоматически при загрузке Windows.
echo ============================================================
pause