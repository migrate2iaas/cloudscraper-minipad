rem if we run from 32-bit cmd on 64-bit windows
if exist C:\Windows\sysnative cd C:\Windows\sysnative

bcdedit /copy {current} /d "Recovery OS"
bcdedit /set {current} device partition=X:
bcdedit /set {current} osdevice partition=X:
bcdedit /set {current} bootlog yes
bcdedit /set {current} bootstatuspolicy ignoreallfailures
bcdedit /set {current} description MigratedOS

