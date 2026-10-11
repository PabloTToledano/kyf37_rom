package org.kyf37.remote;
import java.util.Arrays;
public class IrSignalsTest {
 static void check(boolean b,String s){if(!b)throw new AssertionError(s);}
 static long decode(IrSignals.Wave w,int start,int count,int threshold){long n=0;for(int i=0;i<count;i++)if(w.timings[start+2*i+1]>threshold)n|=1L<<i;return n;}
 static void rejects(Runnable r){try{r.run();throw new AssertionError("Accepted malformed signal");}catch(IllegalArgumentException good){}}
 public static void main(String[] args){
  IrSignals.Wave n=IrSignals.nec(4,8,false);
  check(n.hz==38000&&n.timings.length==67&&n.timings[0]==9000,"NEC shape");
  check(decode(n,2,32,1000)==0xF708FB04L,"LG NEC power payload");
  check(decode(IrSignals.nec(0x0707,2,true),2,32,1000)==0xFD020707L,"Samsung power payload");
  check(decode(IrSignals.nec(0x1234,0x56,false),2,32,1000)==0xA9561234L,"Extended NEC");
  IrSignals.Wave sony=IrSignals.sony(1,21);int sum=0;for(int t:sony.timings)sum+=t;
  check(sony.hz==40000&&sony.timings.length==78&&sum==135000,"Sony three 45ms frames");
  int decoded=0;for(int i=0;i<12;i++)if(sony.timings[2+i*2]>900)decoded|=1<<i;
  check(decoded==149,"Sony command/address");
  int[] reset=IrSignals.greeState(false,25,0,0,false,true);
  check(Arrays.equals(reset,new int[]{0,9,32,80,0,32,0,80}),"Upstream Gree initial-state vector");
  int[] on=IrSignals.greeState(true,24,1,0,false,true);
  check(on[0]==9&&on[1]==8&&on[2]==96&&on[7]==208,"Gree cool24 checksum/power model A");
  check(IrSignals.greeState(true,24,1,0,false,false)[2]==32,"Gree model B");
  int[] bytes={0x12,0x34,0x56,0x78,0x90,0xAB,0xCD,0xEF};
  IrSignals.Wave g=IrSignals.gree(bytes);
  check(g.timings.length==140&&g.timings[0]==9000&&g.timings[1]==4500,"Gree framing");
  check(decode(g,2,32,1000)==0x78563412L&&decode(g,74,32,1000)==0xEFCDAB90L,"Gree upstream payload vector");
  check(g.timings[72]==620&&g.timings[73]==19980,"Gree block separator");
  for(int t=16;t<=30;t++)for(int m=0;m<5;m++)for(int f=0;f<4;f++)for(boolean p:new boolean[]{false,true})IrSignals.gree(IrSignals.greeState(p,t,m,f,true,true));
  rejects(()->new IrSignals.Wave(10000,new int[]{560}));rejects(()->new IrSignals.Wave(38000,new int[]{0}));
  rejects(()->new IrSignals.Wave(38000,new int[]{10001}));rejects(()->new IrSignals.Wave(38000,new int[]{560,-1}));
  rejects(()->IrSignals.nec(-1,2,false));rejects(()->IrSignals.sony(32,1));
  System.out.println("PASS: NEC, Samsung, Sony, Gree vectors; 600 AC combinations; invalid-waveform bounds");
 }
}
