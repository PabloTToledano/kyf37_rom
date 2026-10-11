package org.kyf37.gallery;

import android.content.ContentResolver;
import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.ImageDecoder;
import android.graphics.drawable.AnimatedImageDrawable;
import android.graphics.drawable.Drawable;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.media.MediaMuxer;
import android.media.MediaMetadataRetriever;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.os.StatFs;
import android.provider.MediaStore;
import android.util.AtomicFile;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.UUID;
import org.json.JSONArray;
import org.json.JSONObject;

/** Serialized by the activity's single media executor. Originals are never edited in place. */
final class GalleryStore {
    final Context context;
    final ContentResolver resolver;
    final AtomicFile journal;
    GalleryStore(Context c) {
        context = c.getApplicationContext(); resolver = context.getContentResolver();
        journal = new AtomicFile(new File(context.getFilesDir(), "kyf37-gallery-trash.json"));
    }
    ArrayList<MediaItem> scan() {
        ArrayList<MediaItem> result = new ArrayList<>();
        Uri files = MediaStore.Files.getContentUri("external");
        String[] projection = {"_id", "_display_name", "mime_type", "media_type", "date_modified",
                "_size", "width", "height", "duration", "relative_path", "volume_name", "datetaken"};
        try (Cursor c = resolver.query(files, projection,
                "(media_type=1 OR media_type=3) AND is_pending=0", null, "date_modified DESC, _id DESC")) {
            if (c != null) while (c.moveToNext()) {
                MediaItem m = new MediaItem();
                m.name = text(c, 1, "Untitled"); m.mime = text(c, 2, "image/jpeg");
                m.video = c.getInt(3) == 3; m.modified=c.getLong(4)*1000;
                m.date=c.isNull(11)||c.getLong(11)<=0?m.modified:c.getLong(11);m.size = c.getLong(5);m.managed=true;
                m.width = c.getInt(6); m.height = c.getInt(7); m.duration = c.getLong(8);
                m.path = text(c, 9, ""); m.volume = text(c, 10, "external_primary");
                m.uri = ContentUris.withAppendedId(m.video ? MediaStore.Video.Media.getContentUri(m.volume)
                        : MediaStore.Images.Media.getContentUri(m.volume), c.getLong(0));
                String p = m.path.endsWith("/") ? m.path.substring(0, m.path.length()-1) : m.path;
                m.album = p.isEmpty() ? "Other" : p.substring(p.lastIndexOf('/')+1);
                result.add(m);
            }
        }
        return result;
    }
    private static String text(Cursor c, int at, String fallback) { return c.isNull(at) ? fallback : c.getString(at); }
    Bitmap decode(Uri uri, int side) throws Exception {
        ImageDecoder.Source source = ImageDecoder.createSource(resolver, uri);
        return ImageDecoder.decodeBitmap(source, (decoder, info, src) -> {
            int w = info.getSize().getWidth(), h = info.getSize().getHeight();
            float scale = Math.min(1f, (float)side / Math.max(w,h));
            decoder.setTargetSize(Math.max(1, Math.round(w*scale)), Math.max(1, Math.round(h*scale)));
            decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE);
        });
    }
    AnimatedImageDrawable animation(Uri uri) throws Exception {
        Drawable drawable=ImageDecoder.decodeDrawable(ImageDecoder.createSource(resolver,uri),(decoder,info,source)->{
            int w=info.getSize().getWidth(),h=info.getSize().getHeight();float scale=Math.min(1f,854f/Math.max(w,h));
            decoder.setTargetSize(Math.max(1,Math.round(w*scale)),Math.max(1,Math.round(h*scale)));
        });
        return drawable instanceof AnimatedImageDrawable?(AnimatedImageDrawable)drawable:null;
    }
    private File trashDir() throws Exception {
        File dir = context.getExternalFilesDir("gallery-trash");
        if (dir == null) throw new Exception("Trash storage is unavailable");
        if (!dir.isDirectory() && !dir.mkdirs()) throw new Exception("Cannot open trash storage");
        return dir;
    }
    private JSONArray readJournal() throws Exception {
        if (!journal.getBaseFile().exists() && !new File(journal.getBaseFile()+".bak").exists()) return new JSONArray();
        return new JSONArray(new String(journal.readFully(), StandardCharsets.UTF_8));
    }
    private void saveJournal(JSONArray data) throws Exception {
        FileOutputStream out = null;
        try { out = journal.startWrite(); out.write(data.toString().getBytes(StandardCharsets.UTF_8)); journal.finishWrite(out); }
        catch (Exception e) { if(out != null) journal.failWrite(out); throw e; }
    }
    private File trashFile(String id) throws Exception {
        // Journal IDs are never filenames supplied by the user.
        if (!id.matches("[a-f0-9-]{36}")) throw new Exception("Invalid trash record");
        return new File(trashDir(), id + ".media");
    }
    ArrayList<MediaItem> trashItems() throws Exception {
        ArrayList<MediaItem> result = new ArrayList<>(); JSONArray data=readJournal();
        for (int i=0;i<data.length();i++) {
            JSONObject o=data.getJSONObject(i);File f=trashFile(o.getString("id"));
            if (!f.isFile()) continue;
            MediaItem m=new MediaItem();m.trash=true;m.trashId=o.getString("id");m.uri=Uri.fromFile(f);
            m.name=o.getString("name");m.mime=o.getString("mime");m.video=o.optBoolean("video");
            m.path=o.optString("path");m.volume=o.optString("volume","external_primary");
            m.album="Trash";m.date=o.optLong("date");m.size=f.length();result.add(m);
        }
        return result;
    }
    private void mediaOnly(MediaItem m) throws Exception {
        if (!m.managed || m.trash || !"content".equals(m.uri.getScheme()) || !"media".equals(m.uri.getAuthority()))
            throw new Exception("This item can be viewed, but managed only by its source app");
    }
    void trash(MediaItem m) throws Exception {
        mediaOnly(m);
        File dir=trashDir();
        if (new StatFs(dir.getPath()).getAvailableBytes() < m.size + 16*1024*1024L)
            throw new Exception("Not enough free space to keep a recoverable trash copy");
        String id=UUID.randomUUID().toString();File backup=trashFile(id);
        try (InputStream in=resolver.openInputStream(m.uri);FileOutputStream out=new FileOutputStream(backup)) {
            copy(in,out);out.getFD().sync();
        } catch (Exception e) { backup.delete(); throw e; }
        JSONArray data=readJournal();JSONObject record=new JSONObject();
        record.put("id",id).put("name",m.name).put("mime",m.mime).put("video",m.video)
                .put("path",m.path).put("volume",m.volume).put("date",m.date).put("modified",m.modified).put("size",m.size).put("original",m.key())
                .put("state","copied");
        data.put(record);
        // Durable backup and record come BEFORE deleting the original. A power loss may leave
        // a duplicate recoverable copy, never a deleted original without a recovery record.
        try { saveJournal(data); } catch (Exception e) { backup.delete(); throw e; }
        int deleted;
        try { deleted=resolver.delete(m.uri,null,null); }
        catch (Exception e) { throw new Exception("Original kept; recovery copy is also available in Trash",e); }
        if (deleted!=1) throw new Exception("Original could not be removed; recovery copy remains in Trash");
        record.put("state","trashed");saveJournal(data);
    }
    Uri restore(MediaItem item) throws Exception {
        JSONArray data=readJournal();JSONObject record=null;
        for(int i=0;i<data.length();i++)if(data.getJSONObject(i).getString("id").equals(item.trashId))record=data.getJSONObject(i);
        if(record==null)throw new Exception("Trash record no longer exists");
        Uri original=Uri.parse(record.getString("original"));
        boolean originalPresent=false;
        if(record.optString("state").equals("copied")) {
            // Provider IDs may be reused. Only a matching undeleted source is a recovery duplicate.
            try(Cursor c=resolver.query(original,new String[]{"_display_name","_size","date_modified"},null,null,null)) {
                originalPresent=c!=null&&c.moveToFirst()&&record.getString("name").equals(c.getString(0))
                        &&record.optLong("size",-1)==c.getLong(1)&&record.optLong("modified",record.optLong("date",-1))==c.getLong(2)*1000;
            }
            if(originalPresent)try(InputStream in=resolver.openInputStream(original);InputStream backup=new FileInputStream(trashFile(item.trashId))){originalPresent=sameBytes(in,backup);}
            catch(java.io.FileNotFoundException missing){originalPresent=false;}
        }
        // Copied-state recovery is idempotent after a failed delete/crash: never duplicate an existing original.
        Uri restored=original;
        if(!originalPresent) {
            File f=trashFile(item.trashId);
            restored=insertCopy(item,item.name,GalleryLogic.restoredPath(item.path,item.video),item.volume,() -> new FileInputStream(f));
        }
        removeRecord(item.trashId);trashFile(item.trashId).delete();return restored;
    }
    String originalKey(String trashId) throws Exception {
        JSONArray data=readJournal();for(int i=0;i<data.length();i++)if(data.getJSONObject(i).getString("id").equals(trashId))return data.getJSONObject(i).getString("original");
        return "";
    }
    void deleteForever(MediaItem m) throws Exception {
        File file=trashFile(m.trashId);
        if(file.exists()&&!file.delete())throw new Exception("Could not delete this trash file");
        removeRecord(m.trashId);
    }
    private void removeRecord(String id) throws Exception {
        JSONArray old=readJournal(),next=new JSONArray();
        for(int i=0;i<old.length();i++)if(!old.getJSONObject(i).getString("id").equals(id))next.put(old.getJSONObject(i));
        saveJournal(next);
    }
    interface Input { InputStream open() throws Exception; }
    private Uri insertCopy(MediaItem m,String name,String path,String volume,Input source) throws Exception {
        ContentValues values=new ContentValues();values.put("_display_name",GalleryLogic.fileName(name));
        values.put("mime_type",m.mime);values.put("relative_path",path);values.put("is_pending",1);
        if(m.date>0)values.put("datetaken",m.date);
        Uri collection=m.video?MediaStore.Video.Media.getContentUri(volume):MediaStore.Images.Media.getContentUri(volume);
        Uri uri=resolver.insert(collection,values);if(uri==null)throw new Exception("Cannot create media item");
        try {
            ParcelFileDescriptor fd=resolver.openFileDescriptor(uri,"w");
            if(fd==null)throw new Exception("Cannot open destination");
            try(InputStream in=source.open();ParcelFileDescriptor.AutoCloseOutputStream out=new ParcelFileDescriptor.AutoCloseOutputStream(fd)) {
                copy(in,out);out.getFD().sync();
            }
            values.clear();values.put("is_pending",0);
            if(resolver.update(uri,values,null,null)!=1)throw new Exception("Could not publish the copy");
            return uri;
        } catch(Exception e) { resolver.delete(uri,null,null);throw e; }
    }
    void rename(MediaItem m,String name) throws Exception {
        mediaOnly(m);ContentValues v=new ContentValues();v.put("_display_name",GalleryLogic.fileName(name));
        if(resolver.update(m.uri,v,null,null)!=1)throw new Exception("Rename was not applied");
    }
    void move(MediaItem m,String path) throws Exception {
        mediaOnly(m);ContentValues v=new ContentValues();v.put("relative_path",path);
        if(resolver.update(m.uri,v,null,null)!=1)throw new Exception("Move was not applied");
    }
    Uri copyTo(MediaItem m,String path,String volume) throws Exception {
        mediaOnly(m);return insertCopy(m,m.name,path,volume,() -> resolver.openInputStream(m.uri));
    }
    Uri export(MediaItem m,Bitmap bitmap) throws Exception {
        File tmp=File.createTempFile("gallery-export-",".jpg",context.getCacheDir());
        try {
            try(FileOutputStream out=new FileOutputStream(tmp)) {
                if(!bitmap.compress(Bitmap.CompressFormat.JPEG,95,out))throw new Exception("JPEG export failed");
                out.getFD().sync();
            }
            MediaItem copy=new MediaItem();copy.mime="image/jpeg";
            return insertCopy(copy,"Edited-"+System.currentTimeMillis()+".jpg","Pictures/Edits/","external_primary",() -> new FileInputStream(tmp));
        } finally { tmp.delete(); }
    }
    Uri trimVideo(MediaItem m,long startMillis,long endMillis) throws Exception {
        if(!m.video||startMillis<0||endMillis<=startMillis||(m.duration>0&&endMillis>m.duration))
            throw new IllegalArgumentException("Choose start < end within the video's duration");
        File tmp=File.createTempFile("gallery-trim-",".mp4",context.getCacheDir());
        MediaExtractor extractor=new MediaExtractor();MediaMuxer muxer=null;boolean started=false;
        try {
            extractor.setDataSource(context,m.uri,null);int videoTrack=-1;
            for(int i=0;i<extractor.getTrackCount();i++)if(extractor.getTrackFormat(i).getString(MediaFormat.KEY_MIME).startsWith("video/")){videoTrack=i;break;}
            if(videoTrack<0)throw new Exception("No supported video track");
            extractor.selectTrack(videoTrack);extractor.seekTo(startMillis*1000,MediaExtractor.SEEK_TO_PREVIOUS_SYNC);
            long actualStart=Math.max(0,extractor.getSampleTime());extractor.unselectTrack(videoTrack);
            muxer=new MediaMuxer(tmp.getPath(),MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4);
            MediaMetadataRetriever metadata=new MediaMetadataRetriever();
            try{metadata.setDataSource(context,m.uri);String rotation=metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_ROTATION);if(rotation!=null)muxer.setOrientationHint(Integer.parseInt(rotation));}finally{metadata.release();}
            int[] tracks=new int[extractor.getTrackCount()];java.util.Arrays.fill(tracks,-1);int capacity=4*1024*1024;
            for(int i=0;i<tracks.length;i++){MediaFormat format=extractor.getTrackFormat(i);String mime=format.getString(MediaFormat.KEY_MIME);
                if(mime.startsWith("video/")||mime.startsWith("audio/")){tracks[i]=muxer.addTrack(format);extractor.selectTrack(i);if(format.containsKey(MediaFormat.KEY_MAX_INPUT_SIZE))capacity=Math.max(capacity,format.getInteger(MediaFormat.KEY_MAX_INPUT_SIZE));}}
            if(capacity>16*1024*1024)throw new Exception("This video needs more edit memory than the phone allows");
            muxer.start();started=true;extractor.seekTo(actualStart,MediaExtractor.SEEK_TO_PREVIOUS_SYNC);
            ByteBuffer buffer=ByteBuffer.allocateDirect(capacity);MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();int samples=0;
            while(true){int track=extractor.getSampleTrackIndex();long at=extractor.getSampleTime();if(track<0||at>=endMillis*1000)break;
                if(at>=actualStart&&tracks[track]>=0){buffer.clear();int size=extractor.readSampleData(buffer,0);if(size<0)break;
                    if((extractor.getSampleFlags()&MediaExtractor.SAMPLE_FLAG_ENCRYPTED)!=0)throw new Exception("Encrypted video cannot be trimmed");
                    info.set(0,size,at-actualStart,(extractor.getSampleFlags()&MediaExtractor.SAMPLE_FLAG_SYNC)!=0?MediaCodec.BUFFER_FLAG_KEY_FRAME:0);muxer.writeSampleData(tracks[track],buffer,info);samples++;}
                if(!extractor.advance())break;
            }
            if(samples==0)throw new Exception("The selected interval contains no playable samples");
            muxer.stop();started=false;muxer.release();muxer=null;
            MediaItem output=new MediaItem();output.video=true;output.mime="video/mp4";
            return insertCopy(output,"Trimmed-"+System.currentTimeMillis()+".mp4","Movies/Edits/","external_primary",()->new FileInputStream(tmp));
        } finally {
            extractor.release();if(muxer!=null){if(started)try{muxer.stop();}catch(Exception ignored){}muxer.release();}tmp.delete();
        }
    }
    private static void copy(InputStream in,OutputStream out) throws Exception {
        if(in==null)throw new Exception("Cannot open the source");byte[] buffer=new byte[64*1024];int n;
        while((n=in.read(buffer))!=-1)out.write(buffer,0,n);
    }
    private static boolean sameBytes(InputStream a,InputStream b)throws Exception {
        if(a==null||b==null)return false;byte[] left=new byte[64*1024],right=new byte[64*1024];
        while(true){int n=readBlock(a,left),m=readBlock(b,right);if(n!=m)return false;if(n==0)return true;for(int i=0;i<n;i++)if(left[i]!=right[i])return false;}
    }
    private static int readBlock(InputStream in,byte[] bytes)throws Exception {
        int at=0;while(at<bytes.length){int n=in.read(bytes,at,bytes.length-at);if(n<0)break;if(n>0)at+=n;}return at;
    }
}
