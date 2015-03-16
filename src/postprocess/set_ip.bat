rem we get IP from this template and add it to the the adjust script
netsh interface set interface name="Local Area Network" newname="VirtualNetworkAdapter"
netsh -c interface dump > X:\CloudscraperBootAdjust\adjust\netsh_dump.txt
