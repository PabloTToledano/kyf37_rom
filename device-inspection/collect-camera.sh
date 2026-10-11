#!/bin/bash
adbpath=/mnt/c/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
"$adbpath" -s 981108631314 shell 'dmesg | grep -iE "camera|msm_sensor|sensor_probe|ov[0-9]|imx[0-9]" | tail -n 100' > /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/v8-camera-kernel.txt
