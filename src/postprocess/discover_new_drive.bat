echo rescan > rescan.txt
echo select disk 1 >> rescan.txt
echo select partition 1 >> rescan.txt
echo assign letter=X >> rescan.txt
diskpart /s rescan.txt