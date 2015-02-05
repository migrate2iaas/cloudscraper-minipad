if "%DISK_N%"=="" set DISK_N=1

echo rescan > rescan.txt
echo select disk %DISK_N% >> rescan.txt
echo select partition 1 >> rescan.txt
echo assign letter=X >> rescan.txt
diskpart /s rescan.txt