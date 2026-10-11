from pathlib import Path

root=Path('/home/pablo/kyf37-rom/afphome-port-smali')
p=root/'jp/kyocera/afphome/infosign/view/AFPHomeInfosignListItem.smali'
s=p.read_text()
old='    const v1, 0x1080551'
new='''    invoke-static {p0}, Lorg/kyf37/compat/FrameworkResources;->listSelector(Landroid/view/View;)I
    move-result v1'''
if old in s:
    assert s.count(old)==1
    p.write_text(s.replace(old,new))
else:
    assert new in s
p=root/'org/kyf37/compat/FrameworkResources.smali'
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text('''.class public final Lorg/kyf37/compat/FrameworkResources;
.super Ljava/lang/Object;

.method public static listSelector(Landroid/view/View;)I
    .locals 4
    invoke-virtual {p0}, Landroid/view/View;->getResources()Landroid/content/res/Resources;
    move-result-object v0
    const-string v1, "kc_list_selector"
    const-string v2, "drawable"
    const-string v3, "android"
    invoke-virtual {v0, v1, v2, v3}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I
    move-result v0
    if-nez v0, :found
    new-instance v0, Landroid/content/res/Resources$NotFoundException;
    const-string v1, "KYF37 framework selector is missing"
    invoke-direct {v0, v1}, Landroid/content/res/Resources$NotFoundException;-><init>(Ljava/lang/String;)V
    throw v0
    :found
    return v0
.end method
''')
print('Replaced private selector ID with named framework lookup; requires selector overlay')
