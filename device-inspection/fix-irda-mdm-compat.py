from pathlib import Path
r=Path('/home/pablo/kyf37-rom');p=r/'irda-compat/src/com/kyocera/mdm/MdmPolicyManagerForKddi.java';p.parent.mkdir(parents=True,exist_ok=True)
p.write_text('''package com.kyocera.mdm;
import android.content.ComponentName;
import android.content.Context;
import android.os.Bundle;
import android.os.UserManager;
/** Maps legacy infrared policy bits to actual Android managed application restrictions. */
public final class MdmPolicyManagerForKddi {
 public static final int INFRARED_SENDING_DISABLE=1, INFRARED_RECEIVING_DISABLE=2, NOT_ACTIVE=0;
 public int getRestrictionForKddi(ComponentName admin) {
  try {
   Class<?> at=Class.forName("android.app.ActivityThread");
   Context c=(Context)at.getMethod("currentApplication").invoke(null);
   if(c==null) return 3;
   UserManager u=(UserManager)c.getSystemService(Context.USER_SERVICE);
   if(u==null) return 3;
   Bundle b=u.getApplicationRestrictions(c.getPackageName());
   int mask=b.getInt("mdm-restriction_for_kddi",0);
   if(b.getBoolean("infrared_sending_disabled",false)) mask|=1;
   if(b.getBoolean("infrared_receiving_disabled",false)) mask|=2;
   return mask;
  } catch(Exception e) {
   android.util.Log.e("Kyf37IrdaPolicy","Unable to read managed restrictions",e);
   return 3;
  }
 }
}
''')
p=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/build-irda-android10-port.py');s=p.read_text();marker="run([jdk/'java','-jar',r/'tools/smali.jar','assemble',app,'-o',stage/'classes.dex'])"
insert="""for p in (r/'vendor-framework-smali/com/kyocera/mdm').glob('*.smali'):
 if p.name.startswith(('IMdmPolicyManager','IConfigChangedListener','OnConfigChangedListener')):
  dst=app/'com/kyocera/mdm'/p.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
"""
if insert not in s:s=s.replace(marker,insert+marker)
p.write_text(s)
print('Actual managed application policy adapter and original Binder/listener definitions supplied')
