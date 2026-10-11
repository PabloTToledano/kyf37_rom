#!/bin/bash
# usage: tools/material-preview.sh <outdir> <name> <sel> [night]   (phone lock 'sysui-material')
# Renders the real tile/card/selection views in the debuggable-only preview (hosted in MLandActivity). See Kyf37MaterialPreview.
# The preview runs in its own process (com.android.systemui:sweetsweetdesserts); it is killed first so a freshly installed
# SystemUI APK is loaded.
export MSYS_NO_PATHCONV=1
A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
O=$1; mkdir -p "$O"
P=$($A shell "ps -A | grep sweetsweetdesserts" | tr -d '\r' | awk '{print $2}')
[ -n "$P" ] && $A shell "kill $P"
sleep 1
if [ "$4" = night ]; then $A shell cmd uimode night yes >/dev/null; else $A shell cmd uimode night no >/dev/null; fi
$A shell "input keyevent 224; am start -f 0x10008000 -n com.android.systemui/.egg.MLandActivity --ez kyf37_preview true --ei sel $3 >/dev/null; sleep 2.2; screencap -p /data/local/tmp/p.png"
$A pull /data/local/tmp/p.png "$O/$2.png" >/dev/null
