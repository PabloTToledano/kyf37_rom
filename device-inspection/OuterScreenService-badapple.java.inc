    // Raw input is observed without grabbing it; policy still consumes closed-lid CAMERA.
    private static native int readSideKey();
    private static native void closeSideKey();
    private static native int updateVideo(byte[] packed);
    private volatile boolean inputRunning;
    private volatile boolean inputReady;
    private boolean sideHeld;
    private boolean movie;
    private long movieStart;
    private byte[] movieFrames;
    private android.media.MediaPlayer music;
    private android.media.AudioManager audio;
    private android.media.AudioFocusRequest audioRequest;
    private PowerManager.WakeLock movieLock;
    private final Runnable longSide=new Runnable(){public void run(){
        if(sideHeld && closed()) {sideHeld=false;startMovie();}
    }};
    private void observeSideKey() {
        inputRunning=true;
        new Thread(new Runnable(){public void run(){
            while(inputRunning) {
                int event=readSideKey();
                if(event<0){Log.e("KYF37OuterScreen","Side input unavailable: "+event);break;}
                inputReady=true;
                if(event==1 || event==2) {
                    final boolean down=event==1;
                    handler.post(new Runnable(){public void run(){if(inputRunning)sideKey(down);}});
                }
            }
            inputReady=false;closeSideKey();
        }},"OuterSideKey").start();
    }
    private void sideKey(boolean down) {
        if(!closed()){sideHeld=false;handler.removeCallbacks(longSide);return;}
        if(down) {
            if(movie) {sideHeld=false;stopMovie();refresh();return;}
            sideHeld=true;stopAnimation();startAnimation();
            handler.removeCallbacks(longSide);handler.postDelayed(longSide,800);
        } else {sideHeld=false;handler.removeCallbacks(longSide);}
    }
    private final Runnable videoTick=new Runnable(){public void run(){
        if(!movie)return;
        if(!closed()){stopMovie();refresh();return;}
        long elapsed=SystemClock.elapsedRealtime()-movieStart;
        // Audio playback is the clock when available; skip late video frames rather than drift.
        if(music!=null)try{elapsed=music.getCurrentPosition();}catch(IllegalStateException ignored){}
        int index=(int)(elapsed*15/1000);
        if(index>=movieFrames.length/576 || SystemClock.elapsedRealtime()-movieStart>225000) {
            stopMovie();refresh();return;
        }
        byte[] frameBytes=new byte[576];
        System.arraycopy(movieFrames,index*576,frameBytes,0,576);
        if(updateVideo(frameBytes)!=0){stopMovie();refresh();return;}
        handler.postDelayed(this,66);
    }};
    private void startMovie() {
        stopAnimation();stopMovie();alarms.cancel(tick);
        try {
            if(movieFrames==null) {
                java.io.InputStream in=new java.util.zip.GZIPInputStream(getAssets().open("badapple.frames.gz"));
                java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();
                try {byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){bytes.write(b,0,n);if(bytes.size()>2000000)throw new java.io.IOException("Movie too large");}}
                finally{in.close();}
                movieFrames=bytes.toByteArray();
                if(movieFrames.length==0 || movieFrames.length%576!=0)throw new java.io.IOException("Bad frames");
            }
            audio=(android.media.AudioManager)getSystemService(AUDIO_SERVICE);
            android.media.AudioAttributes attributes=new android.media.AudioAttributes.Builder()
                .setUsage(android.media.AudioAttributes.USAGE_MEDIA).setContentType(android.media.AudioAttributes.CONTENT_TYPE_MUSIC).build();
            audioRequest=new android.media.AudioFocusRequest.Builder(android.media.AudioManager.AUDIOFOCUS_GAIN)
                .setAudioAttributes(attributes).setOnAudioFocusChangeListener(new android.media.AudioManager.OnAudioFocusChangeListener(){
                    public void onAudioFocusChange(int focus){if(focus<0){stopMovie();refresh();}}
                },handler).build();
            if(audio.requestAudioFocus(audioRequest)==android.media.AudioManager.AUDIOFOCUS_REQUEST_GRANTED) {
                try {
                    music=new android.media.MediaPlayer();music.setAudioAttributes(attributes);
                    android.content.res.AssetFileDescriptor afd=getAssets().openFd("badapple.m4a");
                    try{music.setDataSource(afd.getFileDescriptor(),afd.getStartOffset(),afd.getLength());}finally{afd.close();}
                    music.setOnErrorListener(new android.media.MediaPlayer.OnErrorListener(){public boolean onError(android.media.MediaPlayer p,int what,int extra){stopMovie();refresh();return true;}});
                    music.prepare();music.start();
                } catch(Exception e) {if(music!=null){music.release();music=null;}Log.w("KYF37OuterScreen","Silent video fallback",e);}
            }
            movie=true;movieStart=SystemClock.elapsedRealtime();
            movieLock=((PowerManager)getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"KYF37:BadApple");
            movieLock.acquire(230000);refresh();handler.post(videoTick);
            Log.i("KYF37OuterScreen","BadApple started audio="+(music!=null));
        } catch(Exception e){Log.e("KYF37OuterScreen","BadApple failed",e);stopMovie();refresh();}
    }
    private void stopMovie() {
        boolean was=movie;movie=false;handler.removeCallbacks(videoTick);
        if(music!=null){music.release();music=null;}
        if(audio!=null && audioRequest!=null){audio.abandonAudioFocusRequest(audioRequest);audioRequest=null;}
        if(movieLock!=null && movieLock.isHeld())movieLock.release();
        if(was)Log.i("KYF37OuterScreen","BadApple stopped");
    }
