rem if we run from 32-bit cmd on 64-bit windows
if exist X:\boot.ini goto WIN2003

if exist C:\Windows\sysnative\bcdedit.exe cd C:\Windows\sysnative
bcdedit /copy {current} /d "Recovery OS"
bcdedit /set {current} device partition=X:
bcdedit /set {current} osdevice partition=X:
bcdedit /set {current} bootlog yes
bcdedit /set {current} bootstatuspolicy ignoreallfailures
bcdedit /set {current} description MigratedOS
goto END

:WIN2003

bcdedit /create {NTLDR} /d "Migrated legacy OS"
bcdedit /set {NTLDR} device partition=X:
bcdedit /set {NTLDR} path \NTLDR
bcdedit /displayorder {NTLDR} /addlast
bcdedit /default {NTLDR}

:END