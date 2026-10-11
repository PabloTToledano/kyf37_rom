#!/bin/bash
# Press a physical-keypad key through the real input path (scan code on matrix_keypad.67): tools/press-key.sh 59   (59 Contacts, 60 Camera, 28 OK ...)
export MSYS_NO_PATHCONV=1; A=C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe
for c in "$@"; do $A shell "sendevent /dev/input/event1 1 $c 1; sendevent /dev/input/event1 0 0 0; sleep 0.08; sendevent /dev/input/event1 1 $c 0; sendevent /dev/input/event1 0 0 0"; sleep 0.6; done
