from pathlib import Path
p=Path('/home/pablo/kyf37-rom/kernel-android10/kernel/sched/sched_avg.c')
s=p.read_text()
if 'KYF37: sample time while holding' not in s:
 s=s.replace('static DEFINE_PER_CPU(unsigned long, iowait_prod_sum);','static DEFINE_PER_CPU(u64, iowait_prod_sum);')
 s=s.replace('\tlast_get_time = curr_time;\n\t/* read and reset nr_running counts */','\t/* read and reset nr_running counts */')
 s=s.replace('\t\tspin_lock_irqsave(&per_cpu(nr_lock, cpu), flags);','\t\tspin_lock_irqsave(&per_cpu(nr_lock, cpu), flags);\n\t\t/* KYF37: sample time while holding the counter lock, as in newer CAF. */\n\t\tcurr_time = sched_clock();',1)
 s=s.replace('tmp_iowait = per_cpu(iowait_prod_sum, cpu);','tmp_iowait += per_cpu(iowait_prod_sum, cpu);')
 s=s.replace('\t*avg = (int)div64_u64', '\tdiff = curr_time - last_get_time;\n\tlast_get_time = curr_time;\n\n\t*avg = (int)div64_u64',1)
 s=s.replace('\tint diff;\n\ts64 curr_time;', '\tu64 diff;\n\tu64 curr_time;')
 p.write_text(s)
print('Fixed lock-time race, 32-bit nanosecond truncation and cross-CPU iowait accumulation; BUG checks retained')
