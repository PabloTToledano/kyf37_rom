from pathlib import Path
import shutil,json
src=Path('/home/pablo/kyf37-rom/afphome-smali');out=Path('/home/pablo/kyf37-rom/afphome-port-smali')
shutil.copytree(src,out,dirs_exist_ok=True)
old='Landroid/provider/Settings$SilentModeSettings;->getSilentMode(Landroid/content/Context;)Ljava/lang/String;'
new='Lorg/kyf37/compat/SilentModeSettings;->getSilentMode(Landroid/content/Context;)Ljava/lang/String;'
changed=[]
for p in out.rglob('*.smali'):
 s=p.read_text()
 if old in s:p.write_text(s.replace(old,new));changed.append(str(p.relative_to(out)))
assert changed
p=out/'org/kyf37/compat/SilentModeSettings.smali';p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(""".class public final Lorg/kyf37/compat/SilentModeSettings;
.super Ljava/lang/Object;

.method public static getSilentMode(Landroid/content/Context;)Ljava/lang/String;
    .locals 2
    if-nez p0, :read
    const/4 v0, 0x0
    return-object v0
    :read
    invoke-virtual {p0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;
    move-result-object v0
    const-string v1, "silent_mode_type"
    invoke-static {v0, v1}, Landroid/provider/Settings$Global;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    return-object v0
.end method
""")
report={'changed_files':changed,'replacement':new,'behavior':'Preserves stock getSilentMode getter: reads Global silent_mode_type, null for null Context. ROM must also preserve/update the setting for meaningful status.','remaining':'15 vendor framework calls remain; this is a partial port, not a bootable/compatible launcher claim.'}
Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/afphome-port-changes.json').write_text(json.dumps(report,indent=2))
print('Patched getter in',len(changed),'class files')
