from pathlib import Path
p=Path('/home/pablo/kyf37-rom/vendor-framework-smali/com/kyocera/mdm/MdmPolicyManagerForKddi.smali')
s=p.read_text();a=s.find('.method public getRestrictionForKddi');b=s.find('.end method',a);print(s[a:b+11]);print(s[:2000])
