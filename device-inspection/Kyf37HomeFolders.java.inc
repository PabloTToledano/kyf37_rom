    // Persistent launcher folders: component membership never changes installed apps.
    private final ArrayList<Tile> allApps = new ArrayList<Tile>();
    private org.json.JSONObject folders;
    private String openFolder;
    private int homePosition;
    private TextView folderTitle;
    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if(intent.hasCategory(Intent.CATEGORY_HOME) && folders!=null)showFolder(null,homePosition);
    }
    private android.content.SharedPreferences folderPrefs() { return getSharedPreferences("folders", MODE_PRIVATE); }
    private String component(Tile t) { return t.intent == null || t.intent.getComponent() == null ? "" : t.intent.getComponent().flattenToString(); }
    private void saveFolders() { folderPrefs().edit().putString("layout",folders.toString()).apply(); }
    private void loadFolders() {
        if (folders != null) return;
        try { folders = new org.json.JSONObject(folderPrefs().getString("layout","{}")); }
        catch (org.json.JSONException e) { folders = new org.json.JSONObject(); }
        if (!folderPrefs().getBoolean("seeded", false)) {
            try {
                org.json.JSONObject f = new org.json.JSONObject();
                f.put("name", "Kyocera Apps");
                org.json.JSONArray members = new org.json.JSONArray();
                java.util.Set<String> ports = new java.util.HashSet<String>(java.util.Arrays.asList(
                    "com.kyocera.calculator2", "jp.kyocera.charactercheck", "jp.kyocera.datafolder",
                    "jp.kyocera.camera", "jp.kyocera.memo", "jp.kyocera.kc_soundrecorder",
                    "jp.kyocera.barcodereader", "org.kyf37.dialerxx"));
                for (Tile t : allApps) if(t.intent != null && t.intent.getComponent() != null
                        && ports.contains(t.intent.getComponent().getPackageName())) members.put(component(t));
                f.put("members", members); folders.put("kyocera", f); saveFolders();
                folderPrefs().edit().putBoolean("seeded",true).apply();
            } catch (org.json.JSONException impossible) { throw new IllegalStateException(impossible); }
        }
    }
    private String owner(Tile t) {
        String key=component(t);
        java.util.Iterator<String> ids=folders.keys();
        while(ids.hasNext()) {
            String id=ids.next(); org.json.JSONArray a=folders.optJSONObject(id).optJSONArray("members");
            if(a!=null)for(int i=0;i<a.length();i++)if(key.equals(a.optString(i)))return id;
        }
        return null;
    }
    private void showFolder(String id, int selection) {
        openFolder=id; tiles.clear();
        if(id!=null && !folders.has(id))openFolder=null;
        if(openFolder==null) {
            for(Tile t:allApps)if(owner(t)==null)tiles.add(t);
            java.util.Iterator<String> ids=folders.keys();
            ArrayList<String> ordered=new ArrayList<String>();while(ids.hasNext())ordered.add(ids.next());
            Collections.sort(ordered);
            for(String fid:ordered) {
                Tile t=new Tile();t.folderId=fid;t.label=folders.optJSONObject(fid).optString("name","Folder");
                t.icon=new FolderIcon(fid); tiles.add(Math.min(5,tiles.size()),t);
            }
        } else for(Tile t:allApps)if(openFolder.equals(owner(t)))tiles.add(t);
        folderTitle.setVisibility(openFolder==null?View.GONE:View.VISIBLE);
        folderTitle.setText(openFolder==null?"":folders.optJSONObject(openFolder).optString("name")+"  ·  Back: Home");
        adapter.notifyDataSetChanged(); grid.requestFocus();
        grid.setSelection(Math.max(0,Math.min(selection,tiles.size()-1)));scheduleContrast();
    }
    private void activate(Tile t) {
        if(t.folderId!=null){homePosition=tiles.indexOf(t);showFolder(t.folderId,0);}
        else launch(t.intent);
    }
    private void move(Tile tile,String id) {
        try {
            String key=component(tile); java.util.Iterator<String> ids=folders.keys();
            while(ids.hasNext()) {
                org.json.JSONObject f=folders.getJSONObject(ids.next());
                org.json.JSONArray old=f.optJSONArray("members"), next=new org.json.JSONArray();
                if(old!=null)for(int i=0;i<old.length();i++)if(!key.equals(old.optString(i)))next.put(old.optString(i));
                f.put("members",next);
            }
            if(id!=null)folders.getJSONObject(id).getJSONArray("members").put(key);
            saveFolders();showFolder(openFolder,0);
        }catch(org.json.JSONException e){throw new IllegalStateException(e);}
    }
    private void nameFolder(final String id, final Tile app) {
        final android.widget.EditText edit=new android.widget.EditText(this);
        edit.setSingleLine(true);edit.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(40)});
        edit.setText(id==null?"":folders.optJSONObject(id).optString("name"));edit.setSelectAllOnFocus(true);
        new android.app.AlertDialog.Builder(this).setTitle(id==null?"New folder":"Rename folder").setView(edit)
            .setPositiveButton("Save",(dialog,which)->{
                String name=edit.getText().toString().trim();if(name.isEmpty())return;
                try {
                    String fid=id==null?java.util.UUID.randomUUID().toString():id;
                    if(id==null)folders.put(fid,new org.json.JSONObject().put("members",new org.json.JSONArray()));
                    folders.getJSONObject(fid).put("name",name);saveFolders();
                    if(app!=null && app.folderId==null)move(app,fid);else showFolder(openFolder,0);
                }catch(org.json.JSONException e){throw new IllegalStateException(e);}
            }).setNegativeButton(android.R.string.cancel,null).show();
    }
    private void folderMenu() {
        int pos=grid.getSelectedItemPosition();final Tile app=pos>=0&&pos<tiles.size()?tiles.get(pos):null;
        final String fid=app!=null&&app.folderId!=null?app.folderId:openFolder;
        ArrayList<String> choices=new ArrayList<String>();choices.add("New folder");
        if(app!=null&&app.folderId==null)choices.add("Move app to folder / Home");
        if(fid!=null){choices.add("Rename folder");choices.add("Remove folder (keep apps)");}
        final String[] labels=choices.toArray(new String[0]);
        new android.app.AlertDialog.Builder(this).setTitle("Folders · * / hold OK")
            .setItems(labels,(d,which)->{
                String action=labels[which];
                if(action.equals("New folder")){nameFolder(null,app);return;}
                if(action.startsWith("Move")) {
                    final ArrayList<String> ids=new ArrayList<String>();final ArrayList<String> names=new ArrayList<String>();
                    ids.add(null);names.add("Home");java.util.Iterator<String> it=folders.keys();
                    while(it.hasNext()){String id=it.next();ids.add(id);names.add(folders.optJSONObject(id).optString("name"));}
                    new android.app.AlertDialog.Builder(this).setTitle("Move "+app.label)
                        .setItems(names.toArray(new String[0]),(x,n)->move(app,ids.get(n))).show();return;
                }
                if(action.startsWith("Rename")){nameFolder(fid,null);return;}
                new android.app.AlertDialog.Builder(this).setMessage("Remove folder? Apps return to Home.")
                    .setPositiveButton("Remove",(x,n)->{folders.remove(fid);saveFolders();showFolder(null,homePosition);})
                    .setNegativeButton(android.R.string.cancel,null).show();
            }).show();
    }
    private final class FolderIcon extends android.graphics.drawable.Drawable {
        final String id;final android.graphics.Paint paint=new android.graphics.Paint(3);
        FolderIcon(String id){this.id=id;}
        public void draw(android.graphics.Canvas canvas) {
            android.graphics.Rect b=getBounds();float w=b.width(),h=b.height();int save=canvas.save();canvas.translate(b.left,b.top);
            paint.setColor(0xeedbe9ff);canvas.drawRoundRect(0,0,w,h,w*.24f,w*.24f,paint);
            int i=0;for(Tile t:allApps)if(id.equals(owner(t))&&i<4){
                float x=w*(.12f+(i%2)*.43f),y=h*(.12f+(i/2)*.43f);
                android.graphics.Rect old=new android.graphics.Rect(t.icon.getBounds());
                t.icon.setBounds((int)x,(int)y,(int)(x+w*.33f),(int)(y+h*.33f));t.icon.draw(canvas);t.icon.setBounds(old);i++;
            }
            if(i==0){paint.setColor(0xff31588a);paint.setTextSize(w*.48f);canvas.drawText("+",w*.32f,h*.66f,paint);}
            canvas.restoreToCount(save);
        }
        public void setAlpha(int a){}public void setColorFilter(android.graphics.ColorFilter f){}
        public int getOpacity(){return android.graphics.PixelFormat.TRANSLUCENT;}
    }
