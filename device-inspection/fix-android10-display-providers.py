from pathlib import Path
import re,json,hashlib,shutil
r=Path('/home/pablo/kyf37-android10');product=r/'out/target/product/kyf37/system';names=['liboverlay.so','libhdmi.so','libqdutils.so','libmemalloc.so','libqdMetaData.so','libqservice.so'];hal=['hwcomposer.msm8909.so','gralloc.msm8909.so','copybit.msm8909.so','memtrack.msm8909.so'];rels=['lib/'+n for n in names]+['lib/hw/'+n for n in hal]
p=r/'vendor/kyocera/kyf37/kyf37-vendor.mk';s=p.read_text();removed=[]
for rel in rels:
 pattern=r'\S+:system/'+re.escape(rel)+r'(?=\s|$)'
 s,n=re.subn(pattern,'',s);removed.append({'path':rel,'removed_copy_rules':n})
p.write_text(s)
# Preserve default-namespace lookup with source-built copies from the same CAF build.
d=r/'device/kyocera/kyf37/device.mk';text=d.read_text();marker='# CAF display providers in the legacy default namespace'
assert marker not in text
text+='\n'+marker+'\nPRODUCT_COPY_FILES += \\\n'+' \\\n'.join('    $(TARGET_OUT_VENDOR)/'+rel+':system/'+rel for rel in rels)+'\n';d.write_text(text)
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/v6-display-providers');host.mkdir(exist_ok=True)
records=[]
for rel in rels:
 source=product/'vendor'/rel;target=product/rel
 assert source.read_bytes()[:5]==b'\x7fELF\x01'
 if target.exists(): records.append({'path':rel,'previous_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'new_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
 dest=host/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
(host/'manifest.json').write_text(json.dumps(records,indent=2))
print(json.dumps(removed))
