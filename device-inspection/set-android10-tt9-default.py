from pathlib import Path
root=Path('/home/pablo/kyf37-android10')
p=root/'packages/apps/Kyf37KeypadSettings/src/org/kyf37/keypad/Boot.java'
s=p.read_text()
a='  Settings.System.putInt(c.getContentResolver(),"end_button_behavior",0);'
b='''  if(Settings.Secure.getInt(c.getContentResolver(),"kyf37_tt9_initialized",0)==0) {
   final String ime="io.github.sspanak.tt9/.ime.TraditionalT9";
   String enabled=Settings.Secure.getString(c.getContentResolver(),"enabled_input_methods");
   if(enabled==null || enabled.isEmpty()) enabled=ime;
   else if(!enabled.contains(ime)) enabled += ":"+ime;
   Settings.Secure.putString(c.getContentResolver(),"enabled_input_methods",enabled);
   Settings.Secure.putString(c.getContentResolver(),"default_input_method",ime);
   Settings.Secure.putInt(c.getContentResolver(),"kyf37_tt9_initialized",1);
  }
'''
if 'kyf37_tt9_initialized' not in s:s=s.replace(a,b+a)
p.write_text(s)
print('TT9 initial default provisioning added, preserving later user choices')
