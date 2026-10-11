package org.kyf37.stockcompat;

import android.content.ContentResolver;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;

/** Compute the stock folder change fingerprint without SQL in a provider projection. */
public final class Kyf37MediaQuery {
 public static Cursor sense(ContentResolver resolver, Uri uri, String[] projection,
         String selection, String[] args, String order) {
  // Android 10 MediaProvider only accepts named columns. Keep filtering and
  // permissions in the provider; aggregate the same six values in app memory.
  String[] columns={"date_added","date_modified","_size"};
  Cursor c=resolver.query(uri,columns,selection,args,null);
  if(c==null)return null;
  double[] sum=new double[3]; long[] count=new long[3];
  long rows=0; Long maxAdded=null,maxModified=null;
  try {
   while(c.moveToNext()) {
    rows++;
    for(int i=0;i<3;i++) if(!c.isNull(i)){sum[i]+=c.getDouble(i);count[i]++;}
    if(!c.isNull(0)){long v=c.getLong(0);if(maxAdded==null||v>maxAdded)maxAdded=v;}
    if(!c.isNull(1)){long v=c.getLong(1);if(maxModified==null||v>maxModified)maxModified=v;}
   }
  } finally {c.close();}
  MatrixCursor result=new MatrixCursor(projection,1);
  result.addRow(new Object[]{count[0]==0?null:sum[0]/count[0]*10000,
    count[1]==0?null:sum[1]/count[1]*10000,count[2]==0?null:sum[2]/count[2]*10000,
    rows,maxAdded,maxModified});
  return result;
 }
}
