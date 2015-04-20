rem we get IP from this template and add it to the the adjust script
set newAdapterName=VirtualNetworkAdapter

netsh interface set interface name="Local Area Connection" newname="%newAdapterName%"
netsh -c interface dump > X:\CloudscraperBootAdjust\adjust\netsh_dump.txt
wmic NIC where "NetEnabled=true and NetConnectionID like '%newAdapterName%'" get Name /value > X:\CloudscraperBootAdjust\adjust\adapter_name.txt