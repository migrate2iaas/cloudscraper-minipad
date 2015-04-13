cd /d "%~dp0"
git pull
git checkout origin/642_onapp_release
python "%~dp0\src\server.py"