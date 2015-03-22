bcdedit /copy {current} /d "Recovery OS"
bcdedit /set {current} device partition=X:
bcdedit /set {current} osdevice partition=X:
bcdedit /set {current} bootlog yes
bcdedit /set {current} bootstatuspolicy ignoreallfailures
bcdedit /set {current} description MigratedOS

