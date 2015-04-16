cd /d "%~dp0"


git fetch origin
git reset --hard origin/642_onapp_release
git clean -f -d
git pull origin 642_onapp_release
git checkout origin/642_onapp_release

WHERE python
IF %ERRORLEVEL% NEQ 0 set PATH=%PATH%;C:\Python27\
python "%~dp0\src\server.py"