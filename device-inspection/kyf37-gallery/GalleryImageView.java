package org.kyf37.gallery;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.drawable.AnimatedImageDrawable;
import android.graphics.drawable.Drawable;
import android.view.KeyEvent;
import android.view.View;

/** Physical-key zoom/pan and crop selection; no touch gesture is required. */
final class GalleryImageView extends View {
    Bitmap bitmap;
    float zoom=1, panX, panY;
    final RectF crop=new RectF(.1f,.1f,.9f,.9f);
    boolean cropping;
    AnimatedImageDrawable animation;
    final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG|Paint.FILTER_BITMAP_FLAG);
    GalleryImageView(Context c) { super(c); setBackgroundColor(0xff101018); }
    void setBitmap(Bitmap b) { if(animation!=null){animation.stop();animation.setCallback(null);animation=null;}bitmap=b;zoom=1;panX=panY=0;crop.set(.1f,.1f,.9f,.9f);invalidate(); }
    void setAnimation(AnimatedImageDrawable d){animation=d;if(d!=null){d.setCallback(this);d.start();}invalidate();}
    @Override protected boolean verifyDrawable(Drawable d){return d==animation||super.verifyDrawable(d);}
    @Override protected void onDetachedFromWindow(){if(animation!=null){animation.stop();animation.setCallback(null);}super.onDetachedFromWindow();}
    void changeZoom(float scale) { zoom=Math.max(1,Math.min(8,zoom*scale));if(zoom==1)panX=panY=0;invalidate(); }
    boolean pan(int key) {
        if(bitmap==null)return false;
        float dx=key==KeyEvent.KEYCODE_DPAD_LEFT?-.04f:key==KeyEvent.KEYCODE_DPAD_RIGHT?.04f:0;
        float dy=key==KeyEvent.KEYCODE_DPAD_UP?-.04f:key==KeyEvent.KEYCODE_DPAD_DOWN?.04f:0;
        if(dx==0&&dy==0)return false;
        if(cropping) {
            dx=Math.max(-crop.left,Math.min(1-crop.right,dx));
            dy=Math.max(-crop.top,Math.min(1-crop.bottom,dy));crop.offset(dx,dy);
        } else {
            if(zoom<=1)return false;
            panX=Math.max(-1,Math.min(1,panX-dx));panY=Math.max(-1,Math.min(1,panY-dy));
        }
        invalidate();return true;
    }
    void resizeCrop(float dw,float dh) {
        float w=Math.max(.08f,Math.min(1,crop.width()+dw)), h=Math.max(.08f,Math.min(1,crop.height()+dh));
        float l=Math.max(0,Math.min(1-w,crop.centerX()-w/2)), t=Math.max(0,Math.min(1-h,crop.centerY()-h/2));
        crop.set(l,t,l+w,t+h);invalidate();
    }
    void cropRatio(float ratio) {
        if(bitmap==null)return;
        float w=.85f,h=w*bitmap.getWidth()/(ratio*bitmap.getHeight());
        if(h>.85f){h=.85f;w=h*ratio*bitmap.getHeight()/bitmap.getWidth();}
        crop.set((1-w)/2,(1-h)/2,(1+w)/2,(1+h)/2);invalidate();
    }
    @Override protected void onDraw(Canvas c) {
        super.onDraw(c);if(bitmap==null)return;
        float fit=Math.min((float)getWidth()/bitmap.getWidth(),(float)getHeight()/bitmap.getHeight());
        float scale=fit*(cropping?1:zoom), w=bitmap.getWidth()*scale,h=bitmap.getHeight()*scale;
        float left=(getWidth()-w)/2+(cropping?0:panX*Math.max(0,w-getWidth())/2);
        float top=(getHeight()-h)/2+(cropping?0:panY*Math.max(0,h-getHeight())/2);
        RectF dst=new RectF(left,top,left+w,top+h);
        if(animation!=null&&!cropping){animation.setBounds(Math.round(left),Math.round(top),Math.round(left+w),Math.round(top+h));animation.draw(c);}else c.drawBitmap(bitmap,null,dst,paint);
        if(cropping) {
            RectF r=new RectF(left+crop.left*w,top+crop.top*h,left+crop.right*w,top+crop.bottom*h);
            paint.setColor(0x99000000);c.drawRect(dst.left,dst.top,dst.right,r.top,paint);
            c.drawRect(dst.left,r.bottom,dst.right,dst.bottom,paint);
            c.drawRect(dst.left,r.top,r.left,r.bottom,paint);c.drawRect(r.right,r.top,dst.right,r.bottom,paint);
            paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(3);paint.setColor(0xffffc7e2);c.drawRect(r,paint);
            paint.setStrokeWidth(1);c.drawLine(r.left+r.width()/3,r.top,r.left+r.width()/3,r.bottom,paint);
            c.drawLine(r.left+r.width()*2/3,r.top,r.left+r.width()*2/3,r.bottom,paint);
            c.drawLine(r.left,r.top+r.height()/3,r.right,r.top+r.height()/3,paint);
            c.drawLine(r.left,r.top+r.height()*2/3,r.right,r.top+r.height()*2/3,paint);
            paint.setStyle(Paint.Style.FILL);paint.setColor(Color.WHITE);
        }
    }
}
