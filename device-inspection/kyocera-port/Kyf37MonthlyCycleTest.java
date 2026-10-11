import java.text.SimpleDateFormat;
import java.util.TimeZone;
import org.kyf37.stockcompat.Kyf37MonthlyCycle;

public final class Kyf37MonthlyCycleTest {
 static long time(String value,String zone)throws Exception {
  SimpleDateFormat f=new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
  f.setTimeZone(TimeZone.getTimeZone(zone));return f.parse(value).getTime();
 }
 static void check(String now,int day,String zone,boolean next,String expected)throws Exception {
  long actual=Kyf37MonthlyCycle.boundary(time(now,zone),day,zone,next);
  if(actual!=time(expected,zone))throw new AssertionError(now+" expected "+expected+" got "+actual);
 }
 public static void main(String[] args)throws Exception {
  check("2026-01-15 00:00:00",15,"UTC",false,"2025-12-15 00:00:00");
  check("2026-01-15 00:00:00",15,"UTC",true,"2026-02-15 00:00:00");
  check("2026-01-15 00:00:01",15,"UTC",false,"2026-01-15 00:00:00");
  check("2026-02-15 12:00:00",31,"UTC",true,"2026-02-28 23:59:59");
  check("2024-02-15 12:00:00",31,"UTC",true,"2024-02-29 23:59:59");
  check("2026-03-01 00:00:00",31,"UTC",false,"2026-02-28 23:59:59");
  check("2026-03-29 12:00:00",29,"Europe/Madrid",false,"2026-03-29 00:00:00");
  check("2026-03-29 12:00:00",29,"Europe/Madrid",true,"2026-04-29 00:00:00");
  check("2026-10-25 12:00:00",25,"Europe/Madrid",false,"2026-10-25 00:00:00");
  check("2026-10-25 12:00:00",25,"Europe/Madrid",true,"2026-11-25 00:00:00");
  check("2026-01-01 12:00:00",1,"Asia/Tokyo",false,"2026-01-01 00:00:00");
  long fractional=time("2026-01-15 00:00:00","UTC")+999;
  if(Kyf37MonthlyCycle.boundary(fractional,15,"UTC",false)!=time("2025-12-15 00:00:00","UTC"))throw new AssertionError("Legacy second precision lost");
  if(Kyf37MonthlyCycle.boundary(fractional,15,"UTC",true)!=time("2026-02-15 00:00:00","UTC"))throw new AssertionError("Legacy next boundary precision lost");
  for(int invalid:new int[]{-1,0,32}) {
   try{Kyf37MonthlyCycle.boundary(0,invalid,"UTC",false);throw new AssertionError("Invalid day accepted");}
   catch(IllegalArgumentException expected){}
  }
  System.out.println("16 cycle boundary/range cases passed");
 }
}
