from pathlib import Path
root=Path('/home/pablo/kyf37-rom/afphome-port-smali')
p=root/'jp/kyocera/afphome/util/TransferAccessor.smali'
s=p.read_text()
old='Ljp/kyocera/internal/clomask/Transfer;->get(Ljava/lang/String;)Ljava/lang/String;'
new='Lorg/kyf37/compat/VariantSettings;->get(Ljava/lang/String;)Ljava/lang/String;'
if old in s:
 assert s.count(old)==1
 p.write_text(s.replace(old,new))
else: assert new in s
p=root/'org/kyf37/compat/VariantSettings.smali'
p.write_text('''.class public final Lorg/kyf37/compat/VariantSettings;
.super Ljava/lang/Object;

.method public static get(Ljava/lang/String;)Ljava/lang/String;
    .locals 2
    const-string v0, "rw_proximitysensor_colorvariation"
    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :missing
    const-string v0, "ro.kyf37.color_variation"
    invoke-static {v0}, Landroid/os/SystemProperties;->get(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v0
    invoke-virtual {v0}, Ljava/lang/String;->isEmpty()Z
    move-result v1
    if-nez v1, :missing
    return-object v0
    :missing
    new-instance v0, Ljava/io/IOException;
    const-string v1, "KYF37 variant setting unavailable"
    invoke-direct {v0, v1}, Ljava/io/IOException;-><init>(Ljava/lang/String;)V
    throw v0
.end method
''')
print('Launcher color variant now uses captured read-only ROM property')
