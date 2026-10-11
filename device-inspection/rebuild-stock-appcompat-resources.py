"""Reconstruct referenced non-final AppCompat R fields from actual APK resources.

Never invent resource IDs. Styleable indexes and arrays are rebuilt together.
Reports literal TypedArray indexing for review rather than claiming UI parity.
"""
from pathlib import Path
import re,subprocess,json
def rebuild(smali,apk,tree):
 # Preserve original definitions. Rebuilding existing R arrays could change
 # indexes used by inlined TypedArray accesses.
 if (smali/'android/support/v7/appcompat/R$styleable.smali').exists():
  return {'generated':False,'reason':'original-resource-classes-present'}
 refs={};arrayGroups=set();literal=[]
 for p in smali.rglob('*.smali'):
  text=p.read_text()
  for kind,name,desc in re.findall(r'Landroid/support/v7/appcompat/R\$(\w+);->([\w$]+):([^\s]+)',text):
   refs.setdefault(kind,{})[name]=desc
   if kind=='styleable' and desc=='[I':arrayGroups.add(name)
  if 'Landroid/support/v7/appcompat/R$styleable;' in text:
   # Const index reads need review; this is a conservative diagnostic, not a
   # control-flow proof that a constant belongs to the reconstructed TypedArray.
   for method in re.findall(r'\.method.*?\.end method',text,re.S):
    if 'R$styleable;' in method and 'Landroid/content/res/TypedArray;->' in method and re.search(r'const(?:/\w+)? \w+, 0x',method):literal.append(str(p.relative_to(smali))+':'+method.splitlines()[0])
 if not refs:return {'generated':False}
 aapt=tree/'out/host/linux-x86/bin/aapt2'
 def resources(file):
  text=subprocess.check_output([str(aapt),'dump','resources',str(file)],text=True);out={}
  for value,name in re.findall(r'resource (0x[0-9a-f]+) (\S+)',text):
   name=name.split(':')[-1];kind,field=name.split('/',1);out[(kind,field.replace('.','_'))]=int(value,16)
  return out
 app=resources(apk);framework=resources(tree/'out/target/product/kyf37/system/framework/framework-res.apk')
 values={};groups={};unresolved=[]
 for kind,fields in refs.items():
  values[kind]={}
  if kind=='styleable':continue
  for name,desc in fields.items():
   if desc!='I' or (kind,name) not in app:unresolved.append(kind+'/'+name);continue
   values[kind][name]=app[(kind,name)]
 for group in sorted(arrayGroups):
  attrs=[]
  for name,desc in refs.get('styleable',{}).items():
   if desc!='I' or not name.startswith(group+'_'):continue
   attr=name[len(group)+1:];table=app
   if attr.startswith('android_'):attr=attr[8:];table=framework
   if ('attr',attr) not in table:unresolved.append('styleable/'+name);continue
   attrs.append((table[('attr',attr)],name))
  attrs.sort();groups[group]=[value for value,name in attrs]
  for i,(value,name) in enumerate(attrs):values['styleable'][name]=i
 for name,desc in refs.get('styleable',{}).items():
  if desc=='I' and name not in values['styleable']:unresolved.append('styleable/'+name)
 if unresolved:return {'generated':False,'unresolved_resource_fields':sorted(set(unresolved)),'literal_index_review':literal}
 folder=smali/'android/support/v7/appcompat';folder.mkdir(parents=True,exist_ok=True)
 for kind,fields in values.items():
  owner='Landroid/support/v7/appcompat/R$'+kind+';'
  text='.class public final '+owner+'\n.super Ljava/lang/Object;\n\n'
  for name,value in sorted(fields.items()):text+='.field public static final '+name+':I = '+hex(value)+'\n'
  if kind=='styleable':
   for group in sorted(groups):text+='.field public static final '+group+':[I\n'
   text+='\n.method static constructor <clinit>()V\n .registers 1\n'
   for i,(group,attrs) in enumerate(sorted(groups.items())):
    text+=' const v0, '+hex(len(attrs))+'\n new-array v0, v0, [I\n'
    if attrs:text+=' fill-array-data v0, :array'+str(i)+'\n'
    text+=' sput-object v0, '+owner+'->'+group+':[I\n'
   text+=' return-void\n'
   for i,(group,attrs) in enumerate(sorted(groups.items())):
    if attrs:text+=' :array'+str(i)+'\n .array-data 4\n'+''.join(' '+hex(value)+'\n' for value in attrs)+' .end array-data\n'
   text+='.end method\n'
  (folder/('R$'+kind+'.smali')).write_text(text)
 return {'generated':True,'classes':len(values),'styleable_groups':len(groups),'literal_index_review':literal,'hardware_verified':False}
