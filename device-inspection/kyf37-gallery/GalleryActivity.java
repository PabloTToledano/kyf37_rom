package org.kyf37.gallery;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.WallpaperManager;
import android.content.ClipData;
import android.content.ComponentName;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.ContentObserver;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorMatrix;
import android.graphics.ColorMatrixColorFilter;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.media.AudioManager;
import android.media.ExifInterface;
import android.media.MediaMetadataRetriever;
import android.net.Uri;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Handler;
import android.provider.MediaStore;
import android.text.InputType;
import android.text.format.DateFormat;
import android.text.format.Formatter;
import android.util.LruCache;
import android.util.Size;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.EditText;
import android.widget.GridView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.VideoView;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Modern, local-only keypad front end inside the original Kyocera Data Folder APK. */
public final class GalleryActivity extends Activity {
    private static final String LEGACY="jp.kyocera.datafolder.activity.DataFolderActivity";
    private static final int INK=0xff493452, BG=0xfffff5fa, ACCENT=0xff7954a1;
    private final Handler main=new Handler();
    private static final ExecutorService MEDIA=Executors.newSingleThreadExecutor();
    private final ExecutorService media=MEDIA;
    private final ExecutorService thumbnails=Executors.newFixedThreadPool(2);
    private final ArrayList<MediaItem> all=new ArrayList<>(), shown=new ArrayList<>();
    private final ArrayList<Album> albums=new ArrayList<>();
    private final HashSet<String> selected=new HashSet<>(), favorites=new HashSet<>(), hidden=new HashSet<>();
    private final LruCache<String,Bitmap> cache=new LruCache<String,Bitmap>(6*1024*1024) {
        @Override protected int sizeOf(String key,Bitmap b){return b.getAllocationByteCount();}
    };
    private final HashSet<String> loadingThumbs=new HashSet<>();
    private GalleryStore store;
    private LinearLayout root, content;
    private TextView title, subtitle, hints, empty;
    private GridView grid;
    private GalleryImageView image;
    private VideoView video;
    private MediaItem current;
    private String tab="All", albumKey, search="", sort="Newest first";
    private boolean albumsMode, selecting, showHidden, busy, observerRegistered, destroyed, slideshow, externalView, edited, pendingEdit;
    private int generation, viewGeneration, position;
    private AlertDialog operationDialog;
    private static final class Album {String key,name;int count;MediaItem cover;}
    private final ContentObserver observer=new ContentObserver(main) {
        @Override public void onChange(boolean self){main.removeCallbacks(refresh);main.postDelayed(refresh,600);}
    };
    private final Runnable refresh=() -> {if(!busy&&current==null)reload();};
    private final Runnable slide=new Runnable(){public void run(){
        if(!slideshow||current==null)return;
        navigate(1,true);main.postDelayed(this,5000);
    }};
    private SharedPreferences prefs(){return getSharedPreferences("kyf37_gallery",MODE_PRIVATE);}
    private int dp(float n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private TextView text(String s,int size){TextView t=new TextView(this);t.setText(s);t.setTextColor(INK);t.setTextSize(size);return t;}
    @Override public void onCreate(Bundle state){
        setTheme(android.R.style.Theme_Material_Light_NoActionBar);super.onCreate(state);
        store=new GalleryStore(this);
        favorites.addAll(prefs().getStringSet("favorites",Collections.<String>emptySet()));
        hidden.addAll(prefs().getStringSet("hidden",Collections.<String>emptySet()));
        sort=prefs().getString("sort","Newest first");
        if(state!=null){tab=state.getString("tab","All");search=state.getString("search","");albumKey=state.getString("album");albumsMode=state.getBoolean("albums");position=state.getInt("position");}
        Intent incoming=getIntent();String action=incoming.getAction(),type=incoming.getType();
        if(type==null&&incoming.getData()!=null)try{type=getContentResolver().getType(incoming.getData());}catch(Exception ignored){}
        if((action!=null&&!Intent.ACTION_MAIN.equals(action)&&!Intent.ACTION_VIEW.equals(action)&&!isPicker())
                || (isPicker()&&type!=null&&!type.startsWith("image/")&&!type.startsWith("video/")&&!type.equals("*/*"))) {
            legacy(incoming,true);return;
        }
        root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(BG);
        title=text("Gallery",21);title.setPadding(dp(12),dp(9),dp(12),0);root.addView(title);
        subtitle=text("Loading your photos…",12);subtitle.setPadding(dp(12),0,dp(12),dp(7));root.addView(subtitle);
        content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);
        root.addView(content,new LinearLayout.LayoutParams(-1,0,1));
        hints=text("D-pad: browse   OK: open   *: options",11);hints.setGravity(Gravity.CENTER);
        hints.setTextColor(Color.WHITE);hints.setBackgroundColor(ACCENT);hints.setPadding(dp(4),dp(6),dp(4),dp(6));root.addView(hints);
        setContentView(root);showGrid();
        if(Intent.ACTION_VIEW.equals(action)&&incoming.getData()!=null){
            externalView=true;MediaItem m=new MediaItem();m.uri=incoming.getData();m.mime=type==null?"image/jpeg":type;m.video=m.mime.startsWith("video/");m.name="Shared media";
            if(!m.mime.startsWith("image/")&&!m.video){legacy(incoming,true);return;}open(m);
        }
    }
    @Override protected void onResume(){super.onResume();if(store==null||content==null)return;
        if(image!=null&&image.animation!=null)image.animation.start();
        if(checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE)!=PackageManager.PERMISSION_GRANTED){
            if(!externalView)requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE,Manifest.permission.WRITE_EXTERNAL_STORAGE},10);
            return;
        }
        if(!observerRegistered){getContentResolver().registerContentObserver(MediaStore.Files.getContentUri("external"),true,observer);observerRegistered=true;}
        if(current==null)reload();
    }
    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] grants){super.onRequestPermissionsResult(request,permissions,grants);
        if(request==10){if(grants.length>0&&grants[0]==PackageManager.PERMISSION_GRANTED)reload();else {empty.setText("Storage permission is needed to browse local media.\nPress * → Grant storage permission.");updateHints();}}
    }
    @Override protected void onPause(){super.onPause();stopSlideshow();if(video!=null)video.pause();if(image!=null&&image.animation!=null)image.animation.stop();}
    @Override protected void onDestroy(){destroyed=true;main.removeCallbacksAndMessages(null);
        if(observerRegistered)getContentResolver().unregisterContentObserver(observer);
        if(operationDialog!=null)operationDialog.dismiss();if(video!=null)video.stopPlayback();thumbnails.shutdownNow();cache.evictAll();super.onDestroy();}
    @Override protected void onSaveInstanceState(Bundle b){super.onSaveInstanceState(b);b.putString("tab",tab);b.putString("search",search);b.putString("album",albumKey);b.putBoolean("albums",albumsMode);b.putInt("position",grid==null?position:grid.getSelectedItemPosition());}
    private boolean isPicker(){return Intent.ACTION_PICK.equals(getIntent().getAction())||Intent.ACTION_GET_CONTENT.equals(getIntent().getAction());}
    private void legacy(Intent original,boolean forward){
        Intent intent=new Intent(original).setComponent(new ComponentName(getPackageName(),LEGACY));
        if(forward)intent.addFlags(Intent.FLAG_ACTIVITY_FORWARD_RESULT);
        try{startActivity(intent);}catch(Exception e){toast("Original Data Folder is unavailable");}if(forward)finish();
    }
    private void reload(){
        if(destroyed||busy||current!=null)return;
        final int token=++generation;subtitle.setText("Loading…");
        media.execute(() -> {try{
            ArrayList<MediaItem> result=tab.equals("Trash")?store.trashItems():store.scan();
            main.post(() -> {if(destroyed||token!=generation)return;all.clear();all.addAll(result);filter();});
        }catch(Exception e){main.post(() -> {if(destroyed||token!=generation)return;subtitle.setText("Could not load media");empty.setText("Storage unavailable or permission denied.\nPress * for options, then try Reload.");empty.setVisibility(View.VISIBLE);error(e);});}});
    }
    private void filter(){
        if(grid!=null)position=Math.max(0,grid.getSelectedItemPosition());
        shown.clear();albums.clear();LinkedHashMap<String,Album> map=new LinkedHashMap<>();
        String needle=search.toLowerCase(Locale.ROOT),pickType=getIntent().getType();
        for(MediaItem m:all){
            if(!showHidden&&hidden.contains(m.albumKey()))continue;
            if(tab.equals("Photos")&&m.video||tab.equals("Videos")&&!m.video||tab.equals("Favorites")&&!favorites.contains(m.key()))continue;
            if(isPicker()&&pickType!=null&&(pickType.startsWith("image/")&&m.video||pickType.startsWith("video/")&&!m.video))continue;
            if(!needle.isEmpty()&&!m.name.toLowerCase(Locale.ROOT).contains(needle)&&!m.album.toLowerCase(Locale.ROOT).contains(needle))continue;
            Album a=map.get(m.albumKey());if(a==null){a=new Album();a.key=m.albumKey();a.name=m.album;a.cover=m;map.put(a.key,a);}a.count++;
            if(albumKey==null||albumKey.equals(m.albumKey()))shown.add(m);
        }
        Comparator<MediaItem> comparator=sort.equals("Oldest first")?Comparator.comparingLong(m -> m.date)
                :sort.equals("Name A–Z")?Comparator.comparing(m -> m.name.toLowerCase(Locale.ROOT))
                :sort.equals("Largest first")?(a,b) -> Long.compare(b.size,a.size):(a,b) -> Long.compare(b.date,a.date);
        Collections.sort(shown,comparator);albums.addAll(map.values());Collections.sort(albums,(a,b)->a.name.compareToIgnoreCase(b.name));
        HashSet<String> live=new HashSet<>();for(MediaItem m:all)live.add(m.key());selected.retainAll(live);
        adapter.notifyDataSetChanged();grid.setSelection(Math.max(0,Math.min(position,adapter.getCount()-1)));
        empty.setVisibility(adapter.getCount()==0?View.VISIBLE:View.GONE);
        empty.setText(tab.equals("Trash")?"Trash is empty.\nRemoved items can be restored here.\nTrash is cleared only when you choose to delete forever.":"No matching photos or videos.\nUse Camera to take a photo, or change the filter.");
        updateHeader();updateHints();
    }
    private void updateHeader(){
        if(current!=null){title.setText(current.name);subtitle.setText(current.video?"Video · OK: play / pause":"Photo · 2 / 8: zoom · 5: fit");return;}
        title.setText(isPicker()?"Choose media":tab.equals("Trash")?"Trash":albumsMode?"Albums":albumKey!=null?albumName():tab.equals("All")?"Gallery":tab);
        subtitle.setText((albumsMode?albums.size()+" albums":shown.size()+" items")+" · "+sort+(search.isEmpty()?"":" · “"+search+"”")+(selecting?" · "+selected.size()+" selected":""));
    }
    private String albumName(){for(Album a:albums)if(a.key.equals(albumKey))return a.name;return "Album";}
    private void updateHints(){if(hints==null)return;
        hints.setText(current!=null?(image!=null&&image.cropping?"D-pad: move crop   4/6: width   2/8: height\nOK: apply   Back: cancel":current.video?"OK: play/pause   ←/→: seek   ↑/↓: volume\n*: options   Back: gallery":"←/→: photo / pan   2/8: zoom   5: fit\n*: options   Back: gallery")
                :selecting?"OK / Mail: mark   *: batch actions\nBrowser: done selecting   Back: cancel":"D-pad: browse   OK: open   * / Contacts: options\nCamera: capture   Mail: select   Browser: albums");
    }
    private void showGrid(){
        stopSlideshow();if(video!=null){video.stopPlayback();video=null;}image=null;current=null;viewGeneration++;
        content.removeAllViews();empty=text("No media yet",15);empty.setGravity(Gravity.CENTER);empty.setPadding(dp(16),dp(20),dp(16),dp(20));empty.setVisibility(View.GONE);content.addView(empty);
        grid=new GridView(this);grid.setNumColumns(3);grid.setStretchMode(GridView.STRETCH_COLUMN_WIDTH);grid.setVerticalSpacing(dp(3));grid.setHorizontalSpacing(dp(3));grid.setPadding(dp(5),0,dp(5),0);
        grid.setAdapter(adapter);grid.setSelector(new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT));
        grid.setOnItemClickListener((p,v,pos,id)->activate(pos));
        grid.setOnItemLongClickListener((p,v,pos,id)->{grid.setSelection(pos);selecting=true;toggle(pos);return true;});
        content.addView(grid,new LinearLayout.LayoutParams(-1,0,1));grid.requestFocus();updateHeader();updateHints();
    }
    private final BaseAdapter adapter=new BaseAdapter(){
        @Override public int getCount(){return albumsMode?albums.size():shown.size();}
        @Override public Object getItem(int i){return albumsMode?albums.get(i):shown.get(i);}
        @Override public long getItemId(int i){return i;}
        @Override public View getView(int pos,View recycled,ViewGroup parent){
            LinearLayout cell;ImageView thumb;TextView label;
            if(recycled==null){cell=new LinearLayout(GalleryActivity.this);cell.setOrientation(LinearLayout.VERTICAL);cell.setPadding(dp(3),dp(3),dp(3),dp(4));
                thumb=new ImageView(GalleryActivity.this);thumb.setId(1);thumb.setScaleType(ImageView.ScaleType.CENTER_CROP);cell.addView(thumb,new LinearLayout.LayoutParams(-1,dp(76)));
                label=text("",11);label.setId(2);label.setMaxLines(2);label.setGravity(Gravity.CENTER);label.setEllipsize(android.text.TextUtils.TruncateAt.END);cell.addView(label,new LinearLayout.LayoutParams(-1,dp(34)));
                cell.setLayoutParams(new GridView.LayoutParams(-1,dp(120)));cell.setWillNotDraw(false);
            }else{cell=(LinearLayout)recycled;thumb=cell.findViewById(1);label=cell.findViewById(2);}
            MediaItem m=albumsMode?albums.get(pos).cover:shown.get(pos);
            boolean marked=selected.contains(m.key());StateListDrawable background=new StateListDrawable();
            background.addState(new int[]{android.R.attr.state_selected},plate(0xffe6d7f4,true));background.addState(new int[]{android.R.attr.state_focused},plate(0xffe6d7f4,true));background.addState(new int[]{},plate(marked?0xffffd6e7:0xfff4eaf2,marked));cell.setBackground(background);
            label.setText(albumsMode?albums.get(pos).name+" ("+albums.get(pos).count+")":(marked?"✓ ":favorites.contains(m.key())?"♥ ":"")+(m.video?"▶ ":"")+m.name);
            thumb.setImageBitmap(cache.get(m.key()));thumb.setTag(m.key());loadThumb(m,thumb);return cell;
        }
    };
    private GradientDrawable plate(int color,boolean outline){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(10));if(outline)g.setStroke(dp(2),ACCENT);return g;}
    private void loadThumb(MediaItem m,ImageView target){
        if(cache.get(m.key())!=null)return;
        synchronized(loadingThumbs){if(loadingThumbs.size()>=24||!loadingThumbs.add(m.key()))return;}
        thumbnails.execute(() -> {Bitmap b=null;try{
            if(m.trash&&m.video){MediaMetadataRetriever reader=new MediaMetadataRetriever();try{reader.setDataSource(this,m.uri);b=reader.getScaledFrameAtTime(0,MediaMetadataRetriever.OPTION_CLOSEST_SYNC,144,144);}finally{reader.release();}}
            else if(m.trash)b=store.decode(m.uri,144);
            else b=getContentResolver().loadThumbnail(m.uri,new Size(144,144),new CancellationSignal());
        }catch(Exception|OutOfMemoryError ignored){}final Bitmap loaded=b;
        main.post(() -> {synchronized(loadingThumbs){loadingThumbs.remove(m.key());}if(destroyed)return;
            if(loaded!=null){cache.put(m.key(),loaded);if(m.key().equals(target.getTag()))target.setImageBitmap(loaded);if(current==null)adapter.notifyDataSetChanged();}
        });});
    }
    private void activate(int pos){if(pos<0||pos>=adapter.getCount())return;position=pos;
        if(albumsMode){albumKey=albums.get(pos).key;albumsMode=false;position=0;grid.setSelection(0);filter();}
        else if(selecting)toggle(pos);else if(isPicker())returnPicked(Collections.singletonList(shown.get(pos)));else open(shown.get(pos));
    }
    private void toggle(int pos){if(albumsMode){toast("Open an album before selecting items");return;}if(pos<0||pos>=shown.size())return;String key=shown.get(pos).key();if(!selected.add(key))selected.remove(key);adapter.notifyDataSetChanged();updateHeader();updateHints();}
    private void returnPicked(java.util.List<MediaItem> items){
        if(items.isEmpty())return;
        if(items.size()>1&&!getIntent().getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false)){toast("The requesting app allows only one item");return;}
        if(items.size()>100){toast("Choose up to 100 items at a time");return;}
        Intent result=new Intent().setDataAndType(items.get(0).uri,items.get(0).mime).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        ClipData clips=ClipData.newUri(getContentResolver(),"Media",items.get(0).uri);
        for(int i=1;i<items.size();i++)clips.addItem(new ClipData.Item(items.get(i).uri));result.setClipData(clips);setResult(RESULT_OK,result);finish();
    }
    private void open(MediaItem m){
        current=m;edited=false;viewGeneration++;final int token=viewGeneration;content.removeAllViews();updateHeader();updateHints();
        if(m.video){video=new VideoView(this);content.addView(video,new LinearLayout.LayoutParams(-1,0,1));video.setVideoURI(m.uri);
            video.setOnPreparedListener(player->{if(current==m){subtitle.setText("Video · "+time(player.getDuration())+" · OK: pause");video.start();}});
            video.setOnErrorListener((player,what,extra)->{toast("This video format cannot be played. Try Open with…");return true;});
        }else{image=new GalleryImageView(this);content.addView(image,new LinearLayout.LayoutParams(-1,0,1));subtitle.setText("Loading photo…");
            media.execute(()->{try{Bitmap bitmap=store.decode(m.uri,1600);
                android.graphics.drawable.AnimatedImageDrawable animation=(m.mime.equals("image/gif")||m.mime.equals("image/webp"))?store.animation(m.uri):null;
                main.post(()->{if(destroyed||token!=viewGeneration)return;image.setBitmap(bitmap);image.setAnimation(animation);updateHeader();if(pendingEdit){pendingEdit=false;editMenu();}});}
                catch(Exception|OutOfMemoryError e){main.post(()->{if(!destroyed&&token==viewGeneration){subtitle.setText("Cannot open this photo");toast("Unsupported image or insufficient memory");}});}});
        }
    }
    private void navigate(int delta,boolean onlyPhotos){
        if(externalView||shown.isEmpty())return;
        int at=shown.indexOf(current);for(int n=0;n<shown.size();n++){
            at=(at+delta+shown.size())%shown.size();MediaItem m=shown.get(at);
            if(!onlyPhotos||!m.video){if(video!=null){video.stopPlayback();video=null;}position=at;open(m);return;}
        }
        stopSlideshow();
    }
    private void stopSlideshow(){slideshow=false;main.removeCallbacks(slide);getWindow().clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);}
    private ArrayList<MediaItem> targets(){ArrayList<MediaItem> items=new ArrayList<>();
        if(selecting){for(MediaItem m:shown)if(selected.contains(m.key()))items.add(m);}
        else if(current!=null)items.add(current);
        else if(!albumsMode&&grid.getSelectedItemPosition()>=0&&grid.getSelectedItemPosition()<shown.size())items.add(shown.get(grid.getSelectedItemPosition()));
        return items;
    }
    private void menu(){
        if(busy)return;if(image!=null&&image.cropping){cropMenu();return;}
        ArrayList<String> choices=new ArrayList<>();ArrayList<Runnable> actions=new ArrayList<>();ArrayList<MediaItem> items=targets();
        if(!items.isEmpty()){
            if(isPicker()){add(choices,actions,"Use selected media",()->returnPicked(items));}
            else if(items.get(0).trash){add(choices,actions,"Restore ("+items.size()+")",()->batch("Restore",items,m->{String original=store.originalKey(m.trashId);Uri restored=store.restore(m);main.post(()->{if(favorites.remove(original)){favorites.add(restored.toString());prefs().edit().putStringSet("favorites",new HashSet<>(favorites)).apply();}});}));
                add(choices,actions,"Delete forever…",()->confirm("Delete forever?","These "+items.size()+" trash items cannot be recovered.",()->batch("Delete forever",items,m->store.deleteForever(m))));}
            else {
                add(choices,actions,"Share ("+items.size()+")",()->share(items));
                add(choices,actions,"Favorite / unfavorite",()->favorite(items));
                if(items.size()==1){MediaItem m=items.get(0);add(choices,actions,"Details",()->details(m));
                    add(choices,actions,"Rename…",()->input("Rename",m.name,name->batch("Rename",items,x->store.rename(x,name))));
                    if(!m.video){add(choices,actions,"Edit a copy…",()->{if(current!=m){pendingEdit=true;open(m);}else editMenu();});add(choices,actions,"Set wallpaper…",()->wallpaper(m));}
                    else add(choices,actions,"Trim video to a copy…",()->trim(m));
                    add(choices,actions,"Open with…",()->openWith(m));
                }
                add(choices,actions,"Copy to album…",()->pickAlbum(items,false));add(choices,actions,"Move to album…",()->pickAlbum(items,true));
                add(choices,actions,"Move to Trash…",()->confirm("Move to Trash?","Keep a recoverable copy of "+items.size()+" item(s). Trash uses app storage until restored or deleted forever.",()->batch("Move to Trash",items,m->store.trash(m))));
            }
        }
        if(current==null){
            if(!albumsMode){add(choices,actions,selecting?"Finish selection":"Select items",()->{selecting=!selecting;if(!selecting)selected.clear();updateHeader();updateHints();adapter.notifyDataSetChanged();});
                if(selecting){add(choices,actions,"Select all visible",()->{if(isPicker()&&!getIntent().getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false)){toast("This app allows one item");return;}for(MediaItem m:shown)selected.add(m.key());adapter.notifyDataSetChanged();updateHeader();});add(choices,actions,"Clear selection",()->{selected.clear();adapter.notifyDataSetChanged();updateHeader();});}}
            add(choices,actions,"Browse: All / Photos / Videos / Favorites / Trash",this::chooseTab);
            add(choices,actions,albumsMode?"Timeline":"Albums",()->{albumsMode=!albumsMode;albumKey=null;filter();});
            add(choices,actions,"Search filename / album…",()->input("Search",search,s->{search=s;filter();}));
            if(!search.isEmpty())add(choices,actions,"Clear search",()->{search="";filter();});
            add(choices,actions,"Sort…",this::chooseSort);
            if(albumKey!=null)add(choices,actions,"Hide this album",()->{hidden.add(albumKey);prefs().edit().putStringSet("hidden",new HashSet<>(hidden)).apply();albumKey=null;filter();});
            add(choices,actions,showHidden?"Hide hidden albums":"Show hidden albums",()->{showHidden=!showHidden;filter();});
            if(showHidden&&!hidden.isEmpty())add(choices,actions,"Unhide all albums",()->{hidden.clear();prefs().edit().putStringSet("hidden",new HashSet<>(hidden)).apply();filter();});
            if(!isPicker())add(choices,actions,"Photo slideshow",()->{for(MediaItem m:shown)if(!m.video){open(m);slideshow=true;getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);main.postDelayed(slide,5000);return;}toast("No photos in this view");});
            add(choices,actions,"Reload",this::reload);
        }
        if(!isPicker())add(choices,actions,"Original Kyocera Data Folder",()->legacy(new Intent(Intent.ACTION_MAIN),false));
        if(checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE)!=PackageManager.PERMISSION_GRANTED)add(choices,actions,"Grant storage permission",()->requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE,Manifest.permission.WRITE_EXTERNAL_STORAGE},10));
        add(choices,actions,"Keypad help",()->message("Keypad controls","D-pad: browse; OK: open / select\n*: options; Contacts: options\nCamera: take photo; Mail: select\nBrowser: albums / timeline\nPhotos: 2 zoom in, 8 zoom out, 5 fit; D-pad pans when zoomed\nVideo: OK play/pause, left/right seek 10s, up/down volume\nCrop: D-pad move, 4/6 width, 2/8 height, OK apply; Back cancel\nBack: leave viewer / album / selection\n\nEdits save a JPEG copy up to 1600px; originals are kept. Hidden albums are a display filter, not a secure vault. Trash is local app storage; uninstalling or clearing app data removes its recovery copies."));
        new AlertDialog.Builder(this).setTitle(selecting?selected.size()+" selected":"Gallery options").setItems(choices.toArray(new String[0]),(d,i)->actions.get(i).run()).setNegativeButton("Cancel",null).show();
    }
    private void add(ArrayList<String> labels,ArrayList<Runnable> actions,String label,Runnable action){labels.add(label);actions.add(action);}
    private void chooseTab(){String[] tabs=isPicker()?new String[]{"All","Photos","Videos"}:new String[]{"All","Photos","Videos","Favorites","Trash"};
        new AlertDialog.Builder(this).setTitle("Browse").setItems(tabs,(d,i)->{tab=tabs[i];albumKey=null;albumsMode=false;search="";selected.clear();selecting=false;position=0;reload();}).show();}
    private void chooseSort(){String[] sorts={"Newest first","Oldest first","Name A–Z","Largest first"};new AlertDialog.Builder(this).setTitle("Sort").setItems(sorts,(d,i)->{sort=sorts[i];prefs().edit().putString("sort",sort).apply();filter();}).show();}
    private void favorite(ArrayList<MediaItem> items){boolean add=false;for(MediaItem m:items)if(!favorites.contains(m.key()))add=true;
        for(MediaItem m:items)if(add)favorites.add(m.key());else favorites.remove(m.key());prefs().edit().putStringSet("favorites",new HashSet<>(favorites)).apply();toast(add?"Added to favorites":"Removed from favorites");if(current==null)filter();}
    private void share(ArrayList<MediaItem> items){if(items.size()>100){toast("Share up to 100 items at a time");return;}
        boolean images=true,videos=true;ArrayList<Uri> uris=new ArrayList<>();for(MediaItem m:items){images&=!m.video;videos&=m.video;uris.add(m.uri);}
        Intent intent=new Intent(items.size()==1?Intent.ACTION_SEND:Intent.ACTION_SEND_MULTIPLE).setType(images?"image/*":videos?"video/*":"*/*").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        if(items.size()==1)intent.putExtra(Intent.EXTRA_STREAM,uris.get(0));else intent.putParcelableArrayListExtra(Intent.EXTRA_STREAM,uris);
        ClipData data=ClipData.newUri(getContentResolver(),"Media",uris.get(0));for(int i=1;i<uris.size();i++)data.addItem(new ClipData.Item(uris.get(i)));intent.setClipData(data);
        try{startActivity(Intent.createChooser(intent,"Share media"));}catch(Exception e){error(e);}
    }
    private void openWith(MediaItem m){Intent intent=new Intent(Intent.ACTION_VIEW).setDataAndType(m.uri,m.mime).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        intent.setClipData(ClipData.newUri(getContentResolver(),"Media",m.uri));try{startActivity(Intent.createChooser(intent,"Open with"));}catch(Exception e){error(e);}}
    private void details(MediaItem m){
        final String base=m.name+"\n"+m.mime+" · "+Formatter.formatFileSize(this,m.size)+"\n"+m.width+" × "+m.height+(m.video?" · "+time(m.duration):"")+"\n"+DateFormat.format("yyyy-MM-dd HH:mm",m.date)+"\n"+m.path+"\nStorage: "+m.volume;
        media.execute(()->{String exif="";if(!m.video)try(InputStream in=getContentResolver().openInputStream(m.uri)){ExifInterface e=new ExifInterface(in);
            String make=e.getAttribute(ExifInterface.TAG_MAKE),model=e.getAttribute(ExifInterface.TAG_MODEL),iso=e.getAttribute(ExifInterface.TAG_ISO_SPEED_RATINGS);
            exif=(make==null?"":"\nCamera: "+make)+(model==null?"":" "+model)+(iso==null?"":"\nISO "+iso);
        }catch(Exception ignored){}final String full=base+exif;main.post(()->{if(!destroyed)message("Details",full);});});
    }
    interface Operation {void run(MediaItem m)throws Exception;}
    private void batch(String action,ArrayList<MediaItem> items,Operation operation){
        if(busy||items.isEmpty())return;busy=true;stopSlideshow();if(video!=null)video.pause();
        operationDialog=new AlertDialog.Builder(this).setTitle(action).setMessage("Working…").setCancelable(false).show();
        media.execute(()->{int done=0;ArrayList<String> failures=new ArrayList<>();for(MediaItem m:items){if(Thread.currentThread().isInterrupted())break;try{operation.run(m);done++;}catch(Exception e){failures.add(m.name+": "+e.getMessage());}}
            final int completed=done;main.post(()->{busy=false;if(destroyed)return;if(operationDialog!=null)operationDialog.dismiss();selected.clear();selecting=false;cache.evictAll();
                if(current!=null)showGrid();reload();toast(completed+" of "+items.size()+" completed");if(!failures.isEmpty())message("Some items were kept",android.text.TextUtils.join("\n",failures));});});
    }
    private void pickAlbum(ArrayList<MediaItem> items,boolean move){
        ArrayList<String> labels=new ArrayList<>(),paths=new ArrayList<>(),volumes=new ArrayList<>();labels.add("New album…");
        HashSet<String> seen=new HashSet<>();for(MediaItem m:all)if(!m.trash&&seen.add(m.albumKey())){labels.add(m.album+" · "+m.volume);paths.add(m.path);volumes.add(m.volume);}
        new AlertDialog.Builder(this).setTitle(move?"Move to album":"Copy to album").setItems(labels.toArray(new String[0]),(d,i)->{
            if(i==0)input("New album name","",name->{String path=GalleryLogic.albumPath(name);doAlbum(items,path,move,items.get(0).volume);});
            else doAlbum(items,paths.get(i-1),move,volumes.get(i-1));
        }).show();
    }
    private void doAlbum(ArrayList<MediaItem> items,String path,boolean move,String volume){
        if(move)for(MediaItem m:items)if(!m.volume.equals(volume)){message("Move between storage volumes","Copy to the other volume first, then move the originals to Trash. This keeps a recovery path if the SD card disconnects.");return;}
        batch(move?"Move":"Copy",items,m->{if(move)store.move(m,path);else store.copyTo(m,path,volume);});
    }
    interface StringAction {void run(String value);}
    private void input(String title,String value,StringAction action){EditText field=new EditText(this);field.setSingleLine();field.setInputType(InputType.TYPE_CLASS_TEXT);field.setText(value);field.selectAll();
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle(title).setView(field).setPositiveButton("Save",null).setNegativeButton("Cancel",null).create();
        dialog.setOnShowListener(d->{field.requestFocus();dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{try{action.run(field.getText().toString().trim());dialog.dismiss();}catch(IllegalArgumentException e){field.setError(e.getMessage());}});});dialog.show();}
    private void confirm(String title,String body,Runnable action){new AlertDialog.Builder(this).setTitle(title).setMessage(body).setNegativeButton("Cancel",null).setPositiveButton("Continue",(d,i)->action.run()).show();}
    private void wallpaper(MediaItem m){String[] where={"Home screen","Lockscreen","Both"};new AlertDialog.Builder(this).setTitle("Set wallpaper").setItems(where,(d,i)->batch("Wallpaper",new ArrayList<>(Collections.singletonList(m)),item->{
        Bitmap b=store.decode(item.uri,1600);try{WallpaperManager.getInstance(this).setBitmap(b,null,true,i==0?WallpaperManager.FLAG_SYSTEM:i==1?WallpaperManager.FLAG_LOCK:WallpaperManager.FLAG_SYSTEM|WallpaperManager.FLAG_LOCK);}finally{b.recycle();}
    })).show();}
    private void editMenu(){if(image==null||image.bitmap==null){toast("Wait for the photo to load");return;}if(current.trash){toast("Restore this item before editing");return;}
        String[] edits={"Rotate right","Rotate left","Crop…","Black and white","Brighten","Darken","Reset to original","Save edited copy (JPEG, up to 1600px)"};
        new AlertDialog.Builder(this).setTitle("Edit a copy · original kept").setItems(edits,(d,i)->{
            if(i==2){image.cropping=true;image.zoom=1;image.invalidate();updateHints();return;}
            if(i==6){open(current);return;}
            if(i==7){final Bitmap b=image.bitmap;batch("Save edited copy",new ArrayList<>(Collections.singletonList(current)),m->store.export(m,b));return;}
            transform(i);
        }).show();}
    private void trim(MediaItem m){
        confirm("Trim a video copy","The original is kept. The MP4 copy starts at the preceding keyframe, so its start may be slightly earlier than the time you choose.",()->input("Start,end in seconds (e.g. 2,10)","0,"+Math.max(1,m.duration/1000),value->{
            String[] times=value.split(",");if(times.length!=2)throw new IllegalArgumentException("Enter two seconds values separated by a comma");
            try{double from=Double.parseDouble(times[0].trim()),to=Double.parseDouble(times[1].trim());
                if(!Double.isFinite(from)||!Double.isFinite(to)||from<0||to<=from||to>Long.MAX_VALUE/1000d)throw new IllegalArgumentException("Choose valid start and end times");
                long start=Math.round(from*1000),end=Math.round(to*1000);if(m.duration>0&&end>m.duration)throw new IllegalArgumentException("End is after the video's duration");
                batch("Trim video copy",new ArrayList<>(Collections.singletonList(m)),item->store.trimVideo(item,start,end));
            }catch(NumberFormatException e){throw new IllegalArgumentException("Use seconds, for example 2,10");}
        }));
    }
    private void transform(int kind){final Bitmap source=image.bitmap;final int token=viewGeneration;
        media.execute(()->{try{Bitmap b;if(kind==0||kind==1){Matrix matrix=new Matrix();matrix.postRotate(kind==0?90:-90);b=Bitmap.createBitmap(source,0,0,source.getWidth(),source.getHeight(),matrix,true);}
            else{b=Bitmap.createBitmap(source.getWidth(),source.getHeight(),Bitmap.Config.ARGB_8888);ColorMatrix cm=new ColorMatrix();
                if(kind==3)cm.setSaturation(0);else{float gain=kind==4?1.15f:.85f;cm.set(new float[]{gain,0,0,0,0,0,gain,0,0,0,0,0,gain,0,0,0,0,0,1,0});}
                Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);p.setColorFilter(new ColorMatrixColorFilter(cm));new Canvas(b).drawBitmap(source,0,0,p);}
            main.post(()->{if(!destroyed&&token==viewGeneration&&image!=null){image.setBitmap(b);edited=true;subtitle.setText("Unsaved edit · * → Save edited copy");}});
        }catch(Exception|OutOfMemoryError e){main.post(()->{if(!destroyed)toast("Not enough memory to edit this photo");});}});
    }
    private void cropMenu(){String[] options={"Free crop","Square","4:3","16:9","Apply crop","Cancel crop"};new AlertDialog.Builder(this).setTitle("Crop").setItems(options,(d,i)->{
        if(i==1)image.cropRatio(1);else if(i==2)image.cropRatio(4f/3);else if(i==3)image.cropRatio(16f/9);else if(i==4)applyCrop();else if(i==5){image.cropping=false;image.invalidate();updateHints();}
    }).show();}
    private void applyCrop(){if(image==null||image.bitmap==null)return;int[] box=GalleryLogic.crop(image.bitmap.getWidth(),image.bitmap.getHeight(),image.crop.left,image.crop.top,image.crop.right,image.crop.bottom);
        try{Bitmap b=Bitmap.createBitmap(image.bitmap,box[0],box[1],box[2]-box[0],box[3]-box[1]);image.cropping=false;image.setBitmap(b);edited=true;subtitle.setText("Unsaved crop · * → Save edited copy");updateHints();}
        catch(OutOfMemoryError e){toast("Not enough memory to crop");}}
    @Override public boolean dispatchKeyEvent(KeyEvent event){
        if(busy)return true;int key=event.getKeyCode();
        boolean custom=key==KeyEvent.KEYCODE_STAR||key==KeyEvent.KEYCODE_MENU||key==KeyEvent.KEYCODE_F1||key==KeyEvent.KEYCODE_F2||key==KeyEvent.KEYCODE_F3||key==KeyEvent.KEYCODE_F4
                ||current!=null&&(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER||key>=KeyEvent.KEYCODE_DPAD_UP&&key<=KeyEvent.KEYCODE_DPAD_RIGHT||key>=KeyEvent.KEYCODE_0&&key<=KeyEvent.KEYCODE_9);
        if(custom){if(event.getAction()==KeyEvent.ACTION_DOWN&&(event.getRepeatCount()==0||current!=null&&key>=KeyEvent.KEYCODE_DPAD_UP&&key<=KeyEvent.KEYCODE_DPAD_RIGHT))handleKey(key);return true;}
        return super.dispatchKeyEvent(event);
    }
    private void handleKey(int key){
        if(key==KeyEvent.KEYCODE_STAR||key==KeyEvent.KEYCODE_MENU||key==KeyEvent.KEYCODE_F1){menu();return;}
        if(current!=null){
            if(video!=null){if(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER){if(video.isPlaying())video.pause();else video.start();}
                else if(key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_RIGHT)video.seekTo(Math.max(0,Math.min(video.getDuration(),video.getCurrentPosition()+(key==KeyEvent.KEYCODE_DPAD_RIGHT?10000:-10000))));
                else if(key==KeyEvent.KEYCODE_DPAD_UP||key==KeyEvent.KEYCODE_DPAD_DOWN)((AudioManager)getSystemService(AUDIO_SERVICE)).adjustStreamVolume(AudioManager.STREAM_MUSIC,key==KeyEvent.KEYCODE_DPAD_UP?AudioManager.ADJUST_RAISE:AudioManager.ADJUST_LOWER,AudioManager.FLAG_SHOW_UI);
                return;}
            if(image==null)return;if(image.cropping){
                if(key==KeyEvent.KEYCODE_DPAD_CENTER||key==KeyEvent.KEYCODE_ENTER)applyCrop();
                else if(key==KeyEvent.KEYCODE_4)image.resizeCrop(-.04f,0);else if(key==KeyEvent.KEYCODE_6)image.resizeCrop(.04f,0);
                else if(key==KeyEvent.KEYCODE_2)image.resizeCrop(0,-.04f);else if(key==KeyEvent.KEYCODE_8)image.resizeCrop(0,.04f);else image.pan(key);return;}
            if(key==KeyEvent.KEYCODE_2)image.changeZoom(1.4f);else if(key==KeyEvent.KEYCODE_8)image.changeZoom(1/1.4f);else if(key==KeyEvent.KEYCODE_5){image.zoom=1;image.panX=image.panY=0;image.invalidate();}
            else if(!image.pan(key)&&(key==KeyEvent.KEYCODE_DPAD_LEFT||key==KeyEvent.KEYCODE_DPAD_RIGHT)){stopSlideshow();if(edited){toast("Save the edited copy or use Reset to original before changing photos");return;}navigate(key==KeyEvent.KEYCODE_DPAD_RIGHT?1:-1,false);}return;
        }
        if(key==KeyEvent.KEYCODE_F2){try{startActivity(new Intent(MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA));}catch(Exception e){error(e);}}
        else if(key==KeyEvent.KEYCODE_F3&&!albumsMode){if(isPicker()&&!getIntent().getBooleanExtra(Intent.EXTRA_ALLOW_MULTIPLE,false)){activate(grid.getSelectedItemPosition());return;}selecting=true;toggle(grid.getSelectedItemPosition());}
        else if(key==KeyEvent.KEYCODE_F4){if(selecting){selecting=false;selected.clear();adapter.notifyDataSetChanged();updateHeader();updateHints();}else{albumsMode=!albumsMode;albumKey=null;filter();}}
    }
    @Override public void onBackPressed(){
        if(busy)return;if(image!=null&&image.cropping){image.cropping=false;image.invalidate();updateHints();return;}
        if(current!=null){if(edited){confirm("Discard unsaved edit?","The original photo is unchanged.",()->{edited=false;onBackPressed();});return;}if(externalView){finish();return;}showGrid();filter();return;}
        if(selecting){selecting=false;selected.clear();adapter.notifyDataSetChanged();updateHeader();updateHints();return;}
        if(albumKey!=null){albumKey=null;albumsMode=true;filter();return;}
        if(albumsMode){albumsMode=false;filter();return;}super.onBackPressed();
    }
    private static String time(long millis){long s=millis/1000;return String.format(Locale.ROOT,"%d:%02d",s/60,s%60);}
    private void toast(String message){if(!destroyed)Toast.makeText(this,message,Toast.LENGTH_LONG).show();}
    private void message(String title,String body){if(!destroyed)new AlertDialog.Builder(this).setTitle(title).setMessage(body).setPositiveButton("OK",null).show();}
    private void error(Exception e){message("Gallery",e.getMessage()==null?"The operation could not be completed":e.getMessage());}
}
