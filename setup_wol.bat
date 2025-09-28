@echo off
echo 🔧 Wake-on-LAN Setup Guide for Windows
echo =======================================
echo.

echo Step 1: Find your network adapter MAC address
echo ----------------------------------------------
getmac /format:table
echo.

echo Step 2: Enable WOL in Network Adapter Settings
echo ---------------------------------------------
echo 1. Open Device Manager (devmgmt.msc)
echo 2. Expand "Network adapters"
echo 3. Right-click your main network adapter
echo 4. Choose Properties ^> Power Management tab
echo 5. Check these boxes:
echo    ✅ "Allow this device to wake the computer"
echo    ✅ "Only allow a magic packet to wake the computer"
echo.

echo Step 3: Enable WOL in BIOS/UEFI (if available)
echo ---------------------------------------------
echo 1. Restart PC and enter BIOS (F2/F12/Del during boot)
echo 2. Look for "Wake on LAN" / "WOL" / "PME Event Wake Up"
echo 3. Set to "Enabled"
echo 4. Save and exit
echo.

echo Step 4: Configure Power Settings
echo -------------------------------
powercfg /lastwake
echo.
echo Current wake sources shown above.
echo To enable network wake:
echo powercfg /deviceenablewake "Your Network Adapter Name"
echo.

echo Step 5: Test WOL
echo ---------------
echo 1. Put PC to sleep: shutdown /s /t 0
echo 2. From another device, run: python wake_pc.py
echo 3. PC should wake up!
echo.

pause