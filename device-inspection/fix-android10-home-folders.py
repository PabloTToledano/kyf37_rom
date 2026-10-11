"""Stage persistent D-pad launcher folders after all older Home generators."""
from pathlib import Path
here=Path(__file__).resolve().parent
paths=[here/'Kyf37Home.java.txt',Path('/home/pablo/kyf37-android10/packages/apps/Kyf37Home/src/org/kyf37/home/Home.java')]
for p in paths:
 s=p.read_text()
 original=s
 s=s.replace('        t.intent = intent;', '        t.intent = new Intent(intent).setComponent(new ComponentName(info.activityInfo.packageName, info.activityInfo.name));')
 s=s.replace('if(code==KeyEvent.KEYCODE_F2)', 'if(code==KeyEvent.KEYCODE_STAR)')
 if '// Persistent launcher folders:' in s:
  start=s.index('    // Persistent launcher folders:')
  s=s[:start]+(here/'Kyf37HomeFolders.java.inc').read_text()+'\n}\n'
  if s!=original:p.write_text(s)
  continue
 s=s.replace('        Intent intent;','        Intent intent;\n        String folderId;')
 s=s.replace('launch(tiles.get(pos).intent);','activate(tiles.get(pos));')
 s=s.replace('launch(tiles.get(i).intent);','activate(tiles.get(i));')
 s=s.replace('        grid.setOnItemClickListener(','''        grid.setOnItemLongClickListener((parent,view,pos,id)->{grid.setSelection(pos);folderMenu();return true;});
        grid.setOnItemClickListener(''')
 s=s.replace('        grid = new GridView(this);','''        folderTitle=new TextView(this);
        folderTitle.setTextColor(Color.WHITE);folderTitle.setTextSize(18);
        folderTitle.setGravity(Gravity.CENTER);folderTitle.setShadowLayer(3*d,0,d,0xff233c50);
        folderTitle.setPadding(0,(int)(8*d),0,(int)(8*d));folderTitle.setVisibility(View.GONE);
        root.addView(folderTitle);
        grid = new GridView(this);''')
 anchor='        adapter.notifyDataSetChanged();\n        grid.requestFocus();'
 assert anchor in s
 s=s.replace(anchor,'''        int selected=grid.getSelectedItemPosition();
        allApps.clear();allApps.addAll(tiles);loadFolders();showFolder(openFolder,selected);
        adapter.notifyDataSetChanged();
        grid.requestFocus();''',1)
 s=s.replace('        if (event.getRepeatCount() == 0) {','''        if (event.getRepeatCount() == 0) {
            if(code==KeyEvent.KEYCODE_STAR){folderMenu();return true;}''')
 s=s.replace('    @Override public void onBackPressed() { grid.setSelection(0); }','''    @Override public void onBackPressed() {
        if(openFolder!=null)showFolder(null,homePosition);else grid.setSelection(0);
    }
'''+(here/'Kyf37HomeFolders.java.inc').read_text())
 p.write_text(s)
print('Home folders staged')
