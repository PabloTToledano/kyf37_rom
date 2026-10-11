#!/bin/bash
# usage: tools/material-shots.sh <outdir> [night]   (hold the phone lock as 'sysui-material')
# Screenshot walk for the Keitai Material You SystemUI: shade (notifications), QS, selection moves, detail, edit, lock, power menu, volume.
export MSYS_NO_PATHCONV=1
A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
O=${1:-kyf37-rom/systemui-material/walk}; mkdir -p "$O"
k(){ $A shell "input keyevent $*" >/dev/null; sleep 0.5; }
shot(){ $A shell screencap -p /data/local/tmp/m.png; $A pull /data/local/tmp/m.png "$O/$1.png" >/dev/null 2>&1; }
F0=$($A shell "logcat -d | grep -c 'FATAL EXCEPTION'" | tr -d '\r')
$A shell svc power stayon true; $A shell input keyevent 224 >/dev/null
[ "$2" = night ] && $A shell cmd uimode night yes || $A shell cmd uimode night no
sleep 2
$A push tools/notify-poster/Post.jar /data/local/tmp/ >/dev/null
$A shell "CLASSPATH=/data/local/tmp/Post.jar app_process /system/bin Post 3 Walk" >/dev/null
k 3; sleep 1
$A shell cmd statusbar expand-notifications; sleep 1.5; shot n0
k 20; shot n1
k 20; k 20; shot n2
k 20; k 20; k 20; shot n3
$A shell cmd statusbar collapse; sleep 1
$A shell cmd statusbar expand-settings; sleep 1.5; shot q0
k 20; shot q1
k 22; shot q2
k 20; k 20; k 20; shot q3
k 20; k 20; k 20; k 20; shot q4
$A shell cmd statusbar collapse; sleep 1
$A shell input keyevent 24; sleep 0.8; shot v0
k 3
$A shell input keyevent --longpress 26; sleep 1.8; shot p0
k 4
$A shell cmd uimode night no
F1=$($A shell "logcat -d | grep -c 'FATAL EXCEPTION'" | tr -d '\r')
echo "fatal exceptions before=$F0 after=$F1"
