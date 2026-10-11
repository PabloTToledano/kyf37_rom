from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/home/pablo/kyf37-android10/packages/apps/Kyf37KeypadSettings')
p=root/'src/org/kyf37/keypad/KeypadSettings.java'
s=p.read_text()
if 'Your little keypad' in s or 'Button settings' in s:
 print('Visual keypad already applied')
 raise SystemExit(0)
a=s.index(' private ArrayAdapter<String> adapter;')
b=s.index(' private int get(',a)
s=s[:a]+''' private final Button[] keys=new Button[28];
 private Button sleep,speed;
 private TextView detail;
 private int selected=15;
 private int dp(float n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
 private android.graphics.drawable.Drawable surface(int color,int stroke){
  android.graphics.drawable.GradientDrawable d=new android.graphics.drawable.GradientDrawable();
  d.setColor(color);d.setCornerRadius(dp(12));d.setStroke(dp(2),stroke);return d;
 }
 private android.graphics.drawable.Drawable keyBackground(){
  android.graphics.drawable.StateListDrawable d=new android.graphics.drawable.StateListDrawable();
  d.addState(new int[]{android.R.attr.state_pressed},surface(0xffcfdfd4,0xff476a59));
  d.addState(new int[]{android.R.attr.state_focused},surface(0xffdeeadf,0xff476a59));
  d.addState(new int[]{},surface(0xfffffdf8,0xffd8d4ca));return d;
 }
 private LinearLayout column(){LinearLayout l=new LinearLayout(this);l.setOrientation(1);return l;}
 private LinearLayout row(LinearLayout parent){LinearLayout l=new LinearLayout(this);l.setGravity(Gravity.CENTER);parent.addView(l,new LinearLayout.LayoutParams(-1,-2));return l;}
 private void cell(LinearLayout row,View v,float weight,int height){
  LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(height),weight);lp.setMargins(dp(2),dp(2),dp(2),dp(2));row.addView(v,lp);
 }
 private Button button(String title){Button b=new Button(this);b.setText(title);b.setTextSize(12);b.setAllCaps(false);b.setTextColor(0xff39463e);b.setPadding(dp(2),0,dp(2),0);b.setMinWidth(0);b.setMinimumWidth(0);b.setMinHeight(0);b.setMinimumHeight(0);b.setBackground(keyBackground());return b;}
 private Button key(int index,String label){
  Button b=button(label);keys[index]=b;b.setId(100+index);
  b.setOnFocusChangeListener((v,focused)->{if(focused){selected=index;updateDetail();}});
  b.setOnClickListener(v->{selected=index;updateDetail();choose(index+3);});return b;
 }
 private TextView text(String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(0xff39463e);t.setGravity(Gravity.CENTER);return t;}
 @Override public void onCreate(Bundle b){
  super.onCreate(b);if(getActionBar()!=null)getActionBar().hide();
  ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(0xfff4f1e9);
  LinearLayout page=column();page.setPadding(dp(8),dp(6),dp(8),dp(10));scroll.addView(page);setContentView(scroll);
  page.addView(text("Your little keypad",20));page.addView(text("Move with D-pad · Select to assign",11));
  LinearLayout cluster=row(page);
  LinearLayout left=column(),nav=column(),right=column();cell(cluster,left,1,104);cell(cluster,nav,1.65f,104);cell(cluster,right,1,104);
  android.graphics.drawable.GradientDrawable ring=new android.graphics.drawable.GradientDrawable();ring.setColor(0xffe7e8df);ring.setCornerRadius(dp(80));nav.setBackground(ring);
  cell(row(left),key(0,"Contacts"),1,46);cell(row(left),key(2,"Mail"),1,46);
  LinearLayout r=row(nav);View blank=new View(this);cell(r,blank,1,30);cell(r,key(11,"▲"),1,30);cell(r,new View(this),1,30);
  r=row(nav);cell(r,key(13,"◀"),1,30);cell(r,key(15,"OK"),1,30);cell(r,key(14,"▶"),1,30);
  r=row(nav);cell(r,new View(this),1,30);cell(r,key(12,"▼"),1,30);cell(r,new View(this),1,30);
  cell(row(right),key(1,"Camera"),1,46);cell(row(right),key(3,"Apps"),1,46);
  r=row(page);cell(r,key(8,"Call"),1,36);cell(r,key(7,"Clear"),1,36);cell(r,key(9,"End"),1,36);
  int[][] digits={{17,18,19},{20,21,22},{23,24,25},{26,16,27}};
  String[][] legends={{"1  · @","2  ABC","3  DEF"},{"4  GHI","5  JKL","6  MNO"},{"7  PQRS","8  TUV","9  WXYZ"},{"✱","0  +","#"}};
  for(int i=0;i<4;i++){r=row(page);for(int j=0;j<3;j++)cell(r,key(digits[i][j],legends[i][j]),1,36);}
  r=row(page);cell(r,key(4,"F1"),1,32);cell(r,key(5,"F2"),1,32);cell(r,key(6,"F3 · Point"),1,32);
  r=row(page);cell(r,key(10,"Side key"),1,32);
  detail=text("",12);detail.setPadding(0,dp(4),0,dp(4));page.addView(detail,new LinearLayout.LayoutParams(-1,dp(44)));
  r=row(page);sleep=button("");speed=button("");cell(r,sleep,1,36);cell(r,speed,1,36);sleep.setOnClickListener(v->choose(0));speed.setOnClickListener(v->choose(1));
  Button reset=button("Restore default keys");cell(row(page),reset,1,32);reset.setOnClickListener(v->choose(2));
  refresh();keys[15].requestFocus();
 }
 private String actionName(int j){
  String value=Settings.Secure.getString(getContentResolver(),"kyf37_key_"+scans[j]);
  if(value==null)return "Default";
  int code=get("kyf37_key_"+scans[j],defaults[j]);for(int i=1;i<actions.length;i++)if(actions[i]==code)return labels[i];
  return KeyEvent.keyCodeToString(code).replace("KEYCODE_","");
 }
 private void updateDetail(){detail.setText(names[selected]+"\\n"+actionName(selected)+" · Select to change");}
''' + s[b:]
a=s.index(' private void refresh(){');b=s.index(' private void choose(',a)
s=s[:a]+''' private void refresh(){
  sleep.setText("Lid sleep: "+(get("kyf37_lid_only_sleep",1)!=0?"On":"Off"));
  speed.setText("Pointer: "+get("kyf37_pointer_step",12)+" px");
  for(int j=0;j<keys.length;j++)keys[j].setContentDescription(names[j]+", "+actionName(j)+", select to assign");
  updateDetail();
 }
'''+s[b:]
s=s.replace('new AlertDialog.Builder(this).setTitle(names[j]).setItems(labels,(d,n)->{','new AlertDialog.Builder(this).setTitle(names[j]).setSingleChoiceItems(labels, actionIndex(j),(d,n)->{')
s=s.replace('actions[n]);refresh();}).show();','actions[n]);refresh();d.dismiss();}).show();')
s=s.replace(' private void choose(int pos){',' private int actionIndex(int j){if(Settings.Secure.getString(getContentResolver(),"kyf37_key_"+scans[j])==null)return 0;int code=get("kyf37_key_"+scans[j],defaults[j]);for(int i=1;i<actions.length;i++)if(actions[i]==code)return i;return -1;}\n private void choose(int pos){')
s=s.replace('Restore F3 pointer, F4 Home, Centre Clear Back and normal D-pad controls.','Restore all physical keys to their original actions, including F1 Menu, F2 Recents and F3 Pointer.')
p.write_text(s)
print('Applied neutral visual keypad with native focusable controls and current-action picker')





