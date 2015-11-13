cd /d "%~dp0"


git fetch origin
git reset --hard origin/908_xen
#git clean -f -d
git pull origin 908_xen
git checkout origin/908_xen

WHERE python
IF %ERRORLEVEL% NEQ 0 set PATH=%PATH%;C:\Python27\
python "%~dp0\src\server.py"