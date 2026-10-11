#!/bin/bash
# Semi-automated keypad walk of the notification shade and quick settings (KYF37).
# Needs the phone lock (tools/phone-lock.ps1). Usage: tools/test-systemui-keypad.sh <outdir> [theme-id]
# Reads the "Kyf37Shade" log tag that Kyf37KeitaiKeys emits (select/activate/longclick) -> no screenshots needed to decide.
export MSYS_NO_PATHCONV=1
ADB=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
OUT=${1:-kyf37-rom/systemui-loop/walk}; THEME=$2
mkdir -p "$OUT"; REPORT="$OUT/walk.txt"; : > "$REPORT"
PASS=0; FAIL=0
say(){ echo "$*" | tee -a "$REPORT"; }
chk(){ if [ "$2" = "1" ]; then PASS=$((PASS+1)); say "PASS  $1"; else FAIL=$((FAIL+1)); say "FAIL  $1"; fi; }
k(){ $ADB shell "input keyevent $*" >/dev/null; sleep 0.45; }
shot(){ $ADB shell screencap -p /data/local/tmp/w.png; $ADB pull /data/local/tmp/w.png "$OUT/$1.png" >/dev/null 2>&1; }
logsel(){ $ADB logcat -d -s Kyf37Shade:I | tr -cd '[:print:]
' | grep -E "select|activate|longclick" ; }
lastsel(){ logsel | tail -1 | sed 's/.*Kyf37Shade: //'; }
clearlog(){ $ADB logcat -c; }
fatal(){ $ADB logcat -d | grep -c "FATAL EXCEPTION"; }
distinct(){ logsel | grep select | sed 's/.*select //' | sort -u; }

PREV_STAY=$($ADB shell settings get global stay_on_while_plugged_in | tr -d '\r')
$ADB shell svc power stayon true
$ADB shell input keyevent 224 >/dev/null
[ -n "$THEME" ] && $ADB shell settings put global kyf37_focus_theme $THEME
F0=$(fatal); say "fatal exceptions before: $F0"
$ADB shell input keyevent 3; sleep 1

# post three notifications
$ADB push tools/notify-poster/Post.jar /data/local/tmp/ >/dev/null
$ADB shell "CLASSPATH=/data/local/tmp/Post.jar app_process /system/bin Post 4 Walk" >/dev/null
sleep 2

say "== A. notification mode =="
clearlog
$ADB shell cmd statusbar expand-notifications; sleep 1.2
shot a0-open
k 20; shot a1-first
for i in 1 2 3 4 5 6 7 8 9 10; do k 20; done
shot a2-bottom
A_LIST=$(distinct); say "$A_LIST"
echo "$A_LIST" | grep -qi "ExpandableNotificationRow" && chk "A rows selectable" 1 || chk "A rows selectable" 0
echo "$A_LIST" | grep -qi "clear" && chk "A Clear all reachable" 1 || chk "A Clear all reachable" 0
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do k 19; done
shot a3-top
echo "$(lastsel)" | grep -qi "QSTile" && chk "A header tile reachable by Up" 1 || chk "A header tile reachable by Up" 0
for i in 1 2 3 4 5 6; do k 22; done; shot a4-header-right
say "header tiles: $(distinct | grep -ci 'tile')"

say "== B. quick settings mode =="
clearlog; k 82; sleep 1.2; shot b0-qs
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18; do k 20; k 22; done
shot b1-after-walk
B_LIST=$(distinct); say "$B_LIST"
say "distinct QS items: $(echo "$B_LIST" | grep -c .)"
echo "$B_LIST" | grep -qi "seek\|slider\|brightness" && chk "B brightness slider reachable" 1 || chk "B brightness slider reachable" 0
echo "$B_LIST" | grep -qi "settings" && chk "B settings button reachable" 1 || chk "B settings button reachable" 0
echo "$B_LIST" | grep -qi "edit" && chk "B edit button reachable" 1 || chk "B edit button reachable" 0
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do k 19; done; for i in 1 2 3 4 5 6; do k 21; done
shot b2-top-left
# digits
clearlog; k 9; sleep 0.6; echo "$(logsel | tail -2)" | grep -q activate && chk "B digit 2 activates tile" 1 || chk "B digit 2 activates tile" 0
k 9; sleep 0.6   # toggle back
shot b3-digit
# hold OK on a tile -> detail page (use tile 3 = usually bluetooth/wifi)
clearlog; k 8; k 8 ; $ADB shell "input keyevent --longpress 23" ; sleep 1.2; shot b4-hold
$ADB shell dumpsys activity service SystemUIService 2>/dev/null | head -0
logsel | tail -3 | tee -a "$REPORT"
k 4; sleep 1; shot b5-back-from-detail
k 4; sleep 1; shot b6-back-from-qs
$ADB shell cmd statusbar collapse; sleep 1

say "== C. Back/home =="
$ADB shell cmd statusbar expand-settings; sleep 1.2; k 4; sleep 1
OPEN=$($ADB shell dumpsys window | grep -c "mStatusBarExpanded=true\|panelExpanded=true")
shot c1-back-once
$ADB shell cmd statusbar collapse; $ADB shell input keyevent 3; sleep 1
FOC=$($ADB shell dumpsys window | grep mCurrentFocus | tr -d '\r'); say "$FOC"
echo "$FOC" | grep -qi "launcher\|Kyf37Home\|home" && chk "C home works" 1 || chk "C home works (check manually: $FOC)" 0

F1=$(fatal); say "fatal exceptions after: $F1"
[ "$F1" = "$F0" ] && chk "no SystemUI FATAL EXCEPTION during walk" 1 || chk "no SystemUI FATAL EXCEPTION during walk" 0
$ADB shell "dumpsys activity processes | grep -c com.android.systemui" >/dev/null
$ADB shell svc power stayon false; [ "$PREV_STAY" != "null" ] && $ADB shell settings put global stay_on_while_plugged_in $PREV_STAY
say "SUMMARY pass=$PASS fail=$FAIL"
