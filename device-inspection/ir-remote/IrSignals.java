package org.kyf37.remote;
import java.util.ArrayList;
/** Pure protocol codec; values are microseconds and LSB-first unless specified. */
public final class IrSignals {
 public static final class Wave {
  public final int hz; public final int[] timings;
  public Wave(int f,int[] p){hz=f;timings=p;validate(f,p);}
 }
 public static void validate(int f,int[] p){
  if(f<30000||f>60000||p.length<1||p.length>1024)throw new IllegalArgumentException("30–60 kHz, 1–1024 durations required");
  long total=0;
  for(int i=0;i<p.length;i++){if(p[i]<=0||p[i]>100000||((i&1)==0&&p[i]>10000))throw new IllegalArgumentException("Invalid mark/space duration");total+=p[i];}
  if(total>400000)throw new IllegalArgumentException("Frame exceeds 400 ms");
 }
 static void pair(ArrayList<Integer> p,int a,int b){p.add(a);p.add(b);}
 static void bits(ArrayList<Integer> p,long value,int count,int mark,int zero,int one){
  for(int i=0;i<count;i++)pair(p,mark,((value>>>i)&1)==0?zero:one);
 }
 static int[] array(ArrayList<Integer> p){int[] a=new int[p.size()];for(int i=0;i<a.length;i++)a[i]=p.get(i);return a;}
 public static Wave nec(int address,int command,boolean samsung){
  if(address<0||address>65535||command<0||command>255)throw new IllegalArgumentException("Address/command out of range");
  ArrayList<Integer> p=new ArrayList<>();pair(p,samsung?4500:9000,4500);
  int addr=samsung?address:(address<=255?address|((address^255)<<8):address);
  long data=(addr&65535L)|((long)command<<16)|((long)(command^255)<<24);
  bits(p,data,32,560,560,1690);p.add(560);return new Wave(38000,array(p));
 }
 public static Wave sony(int address,int command){
  if(address<0||address>31||command<0||command>127)throw new IllegalArgumentException("SIRC-12 address/command out of range");
  ArrayList<Integer> p=new ArrayList<>();
  for(int repeat=0;repeat<3;repeat++){
   int begin=p.size();pair(p,2400,600);long value=command|((long)address<<7);
   for(int i=0;i<12;i++)pair(p,((value>>>i)&1)==0?600:1200,600);
   int duration=0;for(int i=begin;i<p.size();i++)duration+=p.get(i);
   p.set(p.size()-1,p.get(p.size()-1)+45000-duration);
  }
  return new Wave(40000,array(p));
 }
 public static int[] greeState(boolean power,int temp,int mode,int fan,boolean swing,boolean modelA){
  if(temp<16||temp>30||mode<0||mode>4||fan<0||fan>3)throw new IllegalArgumentException("Invalid AC state");
  if(mode==0)temp=25;if(mode==2)fan=1;
  int[] b={mode|(power?8:0)|(fan<<4)|(swing?64:0),temp-16,32|(power&&modelA?64:0),80,swing?1:0,32,0,0};
  int sum=10;for(int i=0;i<4;i++)sum+=b[i]&15;for(int i=4;i<7;i++)sum+=b[i]>>>4;
  b[7]=(sum&15)<<4;return b;
 }
 public static Wave gree(int[] bytes){
  if(bytes.length!=8)throw new IllegalArgumentException("Gree requires 8 state bytes");
  ArrayList<Integer> p=new ArrayList<>();pair(p,9000,4500);
  for(int i=0;i<4;i++)bits(p,bytes[i],8,620,540,1600);
  bits(p,2,3,620,540,1600);pair(p,620,19980);
  for(int i=4;i<8;i++)bits(p,bytes[i],8,620,540,1600);
  pair(p,620,19980);return new Wave(38000,array(p));
 }
}
