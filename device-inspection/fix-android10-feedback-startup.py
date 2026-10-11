from pathlib import Path
p=Path('/home/pablo/kyf37-android10/frameworks/base/services/core/java/com/android/server/policy/Kyf37Feedback.java');s=p.read_text();s=s.replace('import android.content.Context;','import android.content.Context;\nimport android.content.BroadcastReceiver;\nimport android.content.Intent;\nimport android.content.IntentFilter;').replace('import android.os.Handler;','import android.os.Handler;\nimport android.os.HandlerThread;')
s=s.replace('/** OEM recordings and physical feedback, executed on the policy handler. */','/** OEM feedback runs after boot on its own worker, never on policy/input threads. */')
s=s.replace('private final AudioManager audio;','private AudioManager audio;').replace('private final SoundPool pool;','private SoundPool pool;').replace('private final int openSound, closeSound;','private int openSound, closeSound;')
start=s.index('        this.handler=handler;');end=s.index('\n    private boolean enabled',start)
s=s[:start]+'''        HandlerThread worker=new HandlerThread("KYF37Feedback");
        worker.start();
        this.handler=new Handler(worker.getLooper());
        // Policy initialization precedes AudioService. Creating SoundPool here
        // synchronously waits for audio policy and deadlocks system startup.
        context.registerReceiver(new BroadcastReceiver() {
            @Override public void onReceive(Context ignored,Intent intent) {
                Kyf37Feedback.this.handler.post(new Runnable() {
                    @Override public void run() { initializeAudio(); }
                });
            }
        },new IntentFilter(Intent.ACTION_BOOT_COMPLETED));
        if("1".equals(SystemProperties.get("sys.boot_completed"))) {
            this.handler.post(new Runnable() {
                @Override public void run() { initializeAudio(); }
            });
        }
    }

    private void initializeAudio() {
        if(pool!=null || ServiceManager.checkService("audio")==null
            || ServiceManager.checkService("media.audio_policy")==null) return;
        audio=(AudioManager)context.getSystemService(Context.AUDIO_SERVICE);
        SoundPool loaded=new SoundPool(1,AudioManager.STREAM_SYSTEM,0);
        pool=loaded;
        loaded.setOnLoadCompleteListener(new SoundPool.OnLoadCompleteListener() {
            public void onLoadComplete(SoundPool source,int id,int status) {
                if(status==0) {
                    if(id==openSound) openReady=true;
                    if(id==closeSound) closeReady=true;
                }
            }
        });
        openSound=loaded.load("/system/media/audio/ui/open.mp3",1);
        closeSound=loaded.load("/system/media/audio/ui/close.mp3",1);
    }
''' +s[end:]
s=s.replace('if(open?openReady:closeReady) pool.play','if(pool!=null && (open?openReady:closeReady)) pool.play')
p.write_text(s)
print('Feedback constructor no longer creates SoundPool; all audio uses dedicated worker after boot')
