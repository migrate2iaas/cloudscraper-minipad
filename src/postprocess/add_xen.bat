copy /Y C:\Xen\amd64 X:\Xen
copy /Y C:\Xen X:\Xen

"C:\Deployment Tools\amd64\DISM\dism.exe" /Image:X: /Add-Driver:X:\CloudscraperBootAdjust\Xen\xeniface.inf /ForceUnsigned
"C:\Deployment Tools\amd64\DISM\dism.exe" /Image:X: /Add-Driver:X:\CloudscraperBootAdjust\Xen\xenvbd.inf /ForceUnsigned