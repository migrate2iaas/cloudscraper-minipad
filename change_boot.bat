

bcdedit /copy {current} /d "Backup of default entry"
bcdedit /set {current} device partition=D:
bcdedit /set {current} osdevice partition=D:
bcdedit /set {current} bootlog yes
bcdedit /set {current} bootstatuspolicy ignoreallfailures


bcdedit /create {edaedaaa-edaa-edaa-edaa-edaedaedaeda}  /d "Chainloaded Bootmgr" /application BOOTSECTOR
bcdedit /set {edaedaaa-edaa-edaa-edaa-edaedaedaeda} device partition=d:
bcdedit /set {edaedaaa-edaa-edaa-edaa-edaedaedaeda}   path \bootmgr
bcdedit /displayorder {edaedaaa-edaa-edaa-edaa-edaedaedaeda}  /addfirst