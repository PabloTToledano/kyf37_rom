package org.kyf37.stockcompat;

import java.util.Calendar;
import java.util.TimeZone;

/** Legacy monthly boundary semantics, including short-month end-of-day snapping. */
public final class Kyf37MonthlyCycle {
 public static long boundary(long now,int day,String zone,boolean next) {
  if(day<1||day>31)throw new IllegalArgumentException("No monthly cycle day");
  Calendar current=Calendar.getInstance(TimeZone.getTimeZone(zone));
  current.setTimeInMillis(now);
  // android.text.format.Time compares only whole seconds in the OEM wrapper.
  current.set(Calendar.MILLISECOND,0);
  long comparison=current.getTimeInMillis();
  Calendar cycle=(Calendar)current.clone();
  snap(cycle,day);
  if(next?cycle.getTimeInMillis()<=comparison:cycle.getTimeInMillis()>=comparison) {
   cycle=(Calendar)current.clone();
   cycle.set(Calendar.DAY_OF_MONTH,1);
   cycle.add(Calendar.MONTH,next?1:-1);
   snap(cycle,day);
  }
  return cycle.getTimeInMillis();
 }
 private static void snap(Calendar cycle,int day) {
  cycle.set(Calendar.MILLISECOND,0);
  cycle.set(Calendar.HOUR_OF_DAY,0);
  cycle.set(Calendar.MINUTE,0);
  cycle.set(Calendar.SECOND,0);
  if(day>cycle.getActualMaximum(Calendar.DAY_OF_MONTH)) {
   cycle.set(Calendar.DAY_OF_MONTH,1);
   cycle.add(Calendar.MONTH,1);
   cycle.add(Calendar.SECOND,-1);
  } else cycle.set(Calendar.DAY_OF_MONTH,day);
 }
}
