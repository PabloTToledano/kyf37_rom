from pathlib import Path
r=Path('/home/pablo/kyf37-android10')
p=r/'frameworks/base/services/core/java/com/android/server/policy/Kyf37UartBroker.java'
p.write_text('''package com.android.server.policy;
import android.content.Context;
import android.content.pm.PackageManager;
import android.net.LocalSocket;
import android.net.LocalSocketAddress;
import android.os.*;
import android.util.Slog;
import java.io.*;
import java.nio.*;
/** Uses the original kflcd hardware arbitration protocol, never fabricates a free UART. */
public final class Kyf37UartBroker extends Binder {
 private static final String DESCRIPTOR="jp.kyocera.felicaservice.IFeliCaServiceUartExclusion";
 private final Context context;
 private int owner=-1;
 public Kyf37UartBroker(Context c){context=c;attachInterface(null,DESCRIPTOR);}
 private void enforceOwner(){
  int uid=Binder.getCallingUid();
  PackageManager pm=context.getPackageManager();
  String[] packages=pm.getPackagesForUid(uid);boolean permitted=false;
  if(packages!=null)for(String p:packages)if("com.kyocera.irda".equals(p))permitted=true;
  if(!permitted || pm.checkSignatures(android.os.Process.SYSTEM_UID,uid)!=PackageManager.SIGNATURE_MATCH)
   throw new SecurityException("Only the platform-signed infrared port may arbitrate this UART");
 }
 private int exchange(int command){
  try(LocalSocket socket=new LocalSocket()){
   socket.connect(new LocalSocketAddress("kflcd",LocalSocketAddress.Namespace.RESERVED));
   socket.setSoTimeout(2500);
   byte[] request=new byte[8];request[0]=(byte)command;
   socket.getOutputStream().write(request);socket.getOutputStream().flush();
   byte[] response=new byte[8];int offset=0;
   while(offset<8){int n=socket.getInputStream().read(response,offset,8-offset);if(n<=0)throw new EOFException();offset+=n;}
   return ByteBuffer.wrap(response,4,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
  }catch(IOException e){Slog.w("Kyf37Uart","Hardware UART arbitration failed",e);return -1;}
 }
 @Override protected synchronized boolean onTransact(int code,Parcel data,Parcel reply,int flags)throws RemoteException{
  if(code==INTERFACE_TRANSACTION){reply.writeString(DESCRIPTOR);return true;}
  if(code!=FIRST_CALL_TRANSACTION && code!=FIRST_CALL_TRANSACTION+1)return super.onTransact(code,data,reply,flags);
  data.enforceInterface(DESCRIPTOR);enforceOwner();int uid=Binder.getCallingUid();boolean ok=false;
  long identity=Binder.clearCallingIdentity();
  try{
   if(code==FIRST_CALL_TRANSACTION){
    if(owner==-1 || owner==uid){int status=exchange(0x11);ok=status==2;if(ok)owner=uid;}
   }else if(owner==uid){ok=exchange(0x12)!=-1;if(ok)owner=-1;}
  }finally{Binder.restoreCallingIdentity(identity);}
  reply.writeNoException();reply.writeInt(ok?1:0);return true;
 }
}
''')
p=r/'frameworks/base/services/core/java/com/android/server/policy/PhoneWindowManager.java'
s=p.read_text()
idx=s.find('mKyf37Navigation = new')
print(s[idx-120:idx+160])
# Initialize the broker beside existing KYF37-specific input policy.
line=next(x for x in s.splitlines() if 'mKyf37Navigation = new' in x)
if 'new Kyf37UartBroker' not in s:s=s.replace(line,line+'\n            android.os.ServiceManager.addService("jp.kyocera.felicaservice.FeliCaServiceUartExclusion", new Kyf37UartBroker(mContext));')
a='''                        if (!canceled) {
                            if ((mEndcallBehavior'''
b='''                        if (!canceled) {
                            if (mKyf37Navigation != null) {
                                Intent endKey = new Intent("org.kyf37.END_CALL");
                                endKey.setPackage("com.kyocera.irda");
                                mContext.sendBroadcastAsUser(endKey, UserHandle.CURRENT);
                            }
                            if ((mEndcallBehavior'''
if 'new Intent("org.kyf37.END_CALL")' not in s:
 assert a in s;s=s.replace(a,b,1)
p.write_text(s)
p=r/'frameworks/base/core/res/AndroidManifest.xml'
s=p.read_text()
if 'org.kyf37.END_CALL' not in s:s=s.replace('<protected-broadcast android:name="android.intent.action.BOOT_COMPLETED" />','<protected-broadcast android:name="android.intent.action.BOOT_COMPLETED" />\n    <protected-broadcast android:name="org.kyf37.END_CALL" />')
p.write_text(s)
print('Real kflcd UART broker and foreground infrared red-key bridge added; untested')
