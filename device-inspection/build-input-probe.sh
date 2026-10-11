#!/bin/bash
set -eo pipefail
work=/home/pablo/kyf37-rom/input-probe
sdk=/home/pablo/kyf37-twrp/prebuilts/sdk
java=/home/pablo/kyf37-host-tools/jdk8/bin
mkdir -p "$work/classes"
cat > "$work/Probe.java" <<'JAVA'
package org.kyf37.inputprobe;
public final class Probe extends android.app.Activity {
 public void onCreate(android.os.Bundle b) {
  super.onCreate(b);
  android.widget.EditText text=new android.widget.EditText(this);
  text.setInputType(android.text.InputType.TYPE_CLASS_TEXT);
  text.setTextSize(24); setContentView(text); text.requestFocus();
  getWindow().setSoftInputMode(android.view.WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
 }
}
JAVA
cat > "$work/AndroidManifest.xml" <<'XML'
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.kyf37.inputprobe"><uses-sdk android:minSdkVersion="22" android:targetSdkVersion="22"/><application android:label="Input test"><activity android:name=".Probe" android:exported="true"/></application></manifest>
XML
"$java/javac" -source 1.7 -target 1.7 -cp "$sdk/current/android.jar" -d "$work/classes" "$work/Probe.java"
"$java/java" -jar "$sdk/tools/lib/dx.jar" --dex --output="$work/classes.dex" "$work/classes"
"$sdk/tools/linux/aapt" package -f -M "$work/AndroidManifest.xml" -I "$sdk/current/android.jar" -F "$work/unsigned.apk"
(cd "$work"; "$sdk/tools/linux/aapt" add unsigned.apk classes.dex)
"$java/java" -jar "$sdk/tools/lib/signapk.jar" /home/pablo/kyf37-twrp/build/target/product/security/testkey.x509.pem /home/pablo/kyf37-twrp/build/target/product/security/testkey.pk8 "$work/unsigned.apk" "$work/probe.apk"
cp "$work/probe.apk" /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/input-probe.apk
