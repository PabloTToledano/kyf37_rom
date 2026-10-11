from pathlib import Path
r=Path('/home/pablo/kyf37-android10/hardware/qcom-caf/msm8916/display')
for name in ['libhwcomposer/hwc_mdpcomp.cpp','libhwcomposer/hwc_fbupdate.cpp','libhwcomposer/hwc_qclient.cpp']:
 p=r/name;s=p.read_text().splitlines()
 for i,l in enumerate(s):
  if any(x in l for x in ['getPartialUpdatePref','enablePartialUpdateForMDP3','partialUpdate','partial_update','PARTIAL_UPDATE']):print(str(p.relative_to(r)),i+1,'\n'.join(s[max(0,i-2):i+9]))
