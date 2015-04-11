cd /d "%~dp0"
git pull
git checkout 642_onapp_release

WHERE python
IF %ERRORLEVEL% NEQ 0 set PATH=%PATH%;C:\Python27\
python "%~dp0\src\server.py"