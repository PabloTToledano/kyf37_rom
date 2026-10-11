package org.kyf37.gallery;

import android.app.Instrumentation;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.provider.MediaStore;
import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.UUID;
import org.json.JSONArray;
import org.json.JSONObject;

/** Uses only self-created synthetic media. No user file is edited, trashed or deleted. */
public final class GalleryInstrumentation extends Instrumentation {
    final ArrayList<Uri> owned=new ArrayList<>();
    final ArrayList<String> ownedTrash=new ArrayList<>();
    String fixturePath;
    GalleryStore store;
    Bundle arguments;
    String phase="start";
    @Override public void onCreate(Bundle args){super.onCreate(args);arguments=args;start();}
    private void check(boolean condition,String message){if(!condition)throw new AssertionError(message);}
    private MediaItem item(Uri uri)throws Exception {
        for(MediaItem m:store.scan())if(m.uri.equals(uri))return m;
        throw new Exception("Synthetic fixture was not indexed");
    }
    private Uri fixture()throws Exception {
        Context c=getTargetContext();ContentValues values=new ContentValues();
        fixturePath="Pictures/Kyf37GalleryTest-"+UUID.randomUUID()+"/";
        values.put("_display_name","Synthetic keypad gallery test.png");values.put("mime_type","image/png");
        values.put("relative_path",fixturePath);values.put("is_pending",1);
        Uri uri=c.getContentResolver().insert(MediaStore.Images.Media.getContentUri("external_primary"),values);check(uri!=null,"insert");owned.add(uri);
        Bitmap b=Bitmap.createBitmap(64,48,Bitmap.Config.ARGB_8888);b.eraseColor(Color.rgb(230,190,240));
        for(int y=0;y<24;y++)for(int x=0;x<32;x++)b.setPixel(x,y,Color.rgb(30,80,160));
        ParcelFileDescriptor fd=c.getContentResolver().openFileDescriptor(uri,"w");
        try(ParcelFileDescriptor.AutoCloseOutputStream out=new ParcelFileDescriptor.AutoCloseOutputStream(fd)){check(b.compress(Bitmap.CompressFormat.PNG,100,out),"PNG write");out.getFD().sync();}b.recycle();
        values.clear();values.put("is_pending",0);check(c.getContentResolver().update(uri,values,null,null)==1,"publish");return uri;
    }
    private MediaItem trashed(Uri original)throws Exception {
        for(MediaItem m:store.trashItems())if(store.originalKey(m.trashId).equals(original.toString())){ownedTrash.add(m.trashId);return m;}
        throw new Exception("Synthetic trash record missing");
    }
    private Uri videoFixture()throws Exception {
        ContentValues values=new ContentValues();values.put("_display_name","Synthetic gallery video.mp4");values.put("mime_type","video/mp4");
        values.put("relative_path","Movies/Kyf37GalleryTest-"+UUID.randomUUID()+"/");values.put("is_pending",1);
        Uri uri=getTargetContext().getContentResolver().insert(MediaStore.Video.Media.getContentUri("external_primary"),values);check(uri!=null,"video insert");owned.add(uri);
        ParcelFileDescriptor fd=getTargetContext().getContentResolver().openFileDescriptor(uri,"w");
        try(java.io.InputStream in=getContext().getAssets().open("clip.mp4");ParcelFileDescriptor.AutoCloseOutputStream out=new ParcelFileDescriptor.AutoCloseOutputStream(fd)){
            byte[] bytes=new byte[8192];int n;while((n=in.read(bytes))!=-1)out.write(bytes,0,n);out.getFD().sync();
        }
        values.clear();values.put("is_pending",0);getTargetContext().getContentResolver().update(uri,values,null,null);return uri;
    }
    @Override public void onStart(){
        Bundle results=new Bundle();store=new GalleryStore(getTargetContext());Uri kept=null;
        try {
            phase="fixture";Uri source=fixture();phase="scan";MediaItem m=item(source);long originalSize=m.size;
            Bitmap decoded=store.decode(source,1600);check(decoded.getWidth()==64&&decoded.getHeight()==48,"decode dimensions");
            check(decoded.getPixel(10,10)==Color.rgb(30,80,160),"decode pixels");
            phase="export";Uri exported=store.export(m,decoded);owned.add(exported);decoded.recycle();check(item(source).size==originalSize,"export preserved original");
            phase="copy";Uri copy=store.copyTo(m,fixturePath+"Copy/","external_primary");owned.add(copy);MediaItem copied=item(copy);
            phase="rename";store.rename(copied,"Synthetic renamed.png");copied=item(copy);check(copied.name.equals("Synthetic renamed.png"),"rename");
            phase="move";store.move(copied,fixturePath+"Moved/");copied=item(copy);check(copied.path.equals(fixturePath+"Moved/"),"move");
            phase="trash";store.trash(copied);MediaItem trash=trashed(copy);check(new File(trash.uri.getPath()).isFile(),"durable trash copy");
            phase="restore";Uri restored=store.restore(trash);owned.add(restored);check(item(restored).size==copied.size,"restore bytes");
            check(!new File(trash.uri.getPath()).exists(),"restore cleanup");
            Uri second=store.copyTo(m,fixturePath+"Failure/","external_primary");owned.add(second);store.trash(item(second));MediaItem pending=trashed(second);
            String volume=pending.volume;pending.volume="kyf37_test_unmounted";boolean failed=false;
            try{store.restore(pending);}catch(Exception expected){failed=true;}check(failed,"unavailable volume fails");
            check(new File(pending.uri.getPath()).isFile(),"failed restore kept backup");pending.volume=volume;
            store.deleteForever(pending);check(!new File(pending.uri.getPath()).exists(),"explicit trash deletion");
            // Recreate the durable 'copied' state that remains after power loss before source deletion.
            m=item(source);String id=UUID.randomUUID().toString();ownedTrash.add(id);
            File dir=getTargetContext().getExternalFilesDir("gallery-trash");File backup=new File(dir,id+".media");
            try(java.io.InputStream in=getTargetContext().getContentResolver().openInputStream(source);FileOutputStream out=new FileOutputStream(backup)){byte[] bytes=new byte[1024];int n;while((n=in.read(bytes))!=-1)out.write(bytes,0,n);out.getFD().sync();}
            JSONArray journal=store.journal.getBaseFile().exists()?new JSONArray(new String(store.journal.readFully(),java.nio.charset.StandardCharsets.UTF_8)):new JSONArray();
            journal.put(new JSONObject().put("id",id).put("name",m.name).put("mime",m.mime).put("video",false).put("path",m.path).put("volume",m.volume).put("date",m.date).put("modified",m.modified).put("size",m.size).put("original",m.key()).put("state","copied"));
            FileOutputStream output=store.journal.startWrite();output.write(journal.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));store.journal.finishWrite(output);
            MediaItem recovery=trashed(source);check(store.restore(recovery).equals(source),"power-loss recovery reused matching original");
            check(item(source).size==originalSize,"source survived all tests");
            Uri video=videoFixture();MediaItem movie=item(video);movie.duration=5000;
            Uri trimmed=store.trimVideo(movie,1000,3000);owned.add(trimmed);
            android.media.MediaMetadataRetriever metadata=new android.media.MediaMetadataRetriever();
            try{metadata.setDataSource(getTargetContext(),trimmed);long duration=Long.parseLong(metadata.extractMetadata(android.media.MediaMetadataRetriever.METADATA_KEY_DURATION));
                check(duration>=1900&&duration<=2300,"trim interval");check(metadata.getScaledFrameAtTime(0,android.media.MediaMetadataRetriever.OPTION_CLOSEST_SYNC,80,60)!=null,"trim decodes");
            }finally{metadata.release();}
            android.media.MediaExtractor tracks=new android.media.MediaExtractor();try{tracks.setDataSource(getTargetContext(),trimmed,null);check(tracks.getTrackCount()==2,"trim kept video and audio tracks");}finally{tracks.release();}
            check(item(video).size==movie.size,"trim kept original video");
            if(arguments!=null&&"true".equals(arguments.getString("keep_fixture")))kept=source;
            results.putString("result","PASS: synthetic scan/decode/export/copy/rename/move/trash/restore/permanent-delete/failure recovery/video trim with audio");
            if(kept!=null)results.putString("fixture_uri",kept.toString());
        }catch(Throwable failure){results.putString("result","FAIL at "+phase+": "+failure.getClass().getSimpleName()+": "+failure.getMessage());results.putString("trace",android.util.Log.getStackTraceString(failure));}
        finally {
            for(String id:ownedTrash)try{for(MediaItem m:store.trashItems())if(id.equals(m.trashId))store.deleteForever(m);}catch(Exception ignored){}
            for(Uri uri:owned)if(!uri.equals(kept))try{getTargetContext().getContentResolver().delete(uri,null,null);}catch(Exception ignored){}
        }
        finish(results.getString("result","").startsWith("PASS")?ActivityResult.OK:ActivityResult.FAIL,results);
    }
    private static final class ActivityResult {static final int OK=-1,FAIL=0;}
}
