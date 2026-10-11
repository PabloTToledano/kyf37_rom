from pathlib import Path
p=Path('/home/pablo/kyf37-lineage/build/core/definitions.mk');s=p.read_text()
old='$($(PRIVATE_2ND_ARCH_VAR_PREFIX)$(PRIVATE_PREFIX)AR) p $$lib_to_include $$f > $$ldir/$$ext$$f;'
new='mkdir -p "$$(dirname "$$ldir/$$ext$$f")"; '+chr(92)+'\n        $($(PRIVATE_2ND_ARCH_VAR_PREFIX)$(PRIVATE_PREFIX)AR) pP $$lib_to_include $$f > $$ldir/$$ext$$f;'
if old in s:p.write_text(s.replace(old,new,1))
root=Path('/home/pablo/kyf37-lineage/out/host').resolve();assert str(root)=='/home/pablo/kyf37-lineage/out/host'
count=0
for p in root.rglob('*.a'):
 assert root in p.resolve().parents
 p.unlink();count+=1
print('Invalidated',count,'generated host archives')
