if "%DISK_N%"=="" set DISK_N=%1
if "%DISK_N%"=="" set DISK_N=1

echo rescan > rescan.txt
diskpart /s rescan.txt
rem wait till volume is recognized after the rescan (that is async in Windows)
ping 1.1.1.1 -n 1 -w 60000 > nul

echo select disk %DISK_N% >> rescan.txt
echo select partition 1 >> rescan.txt
echo assign letter=X >> rescan.txt
diskpart /s rescan.txt