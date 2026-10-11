import re
def irq(p):
    d={}
    for l in open(p,errors='ignore'):
        m=re.match(r'\s*(\S+):\s+((?:\d+\s+)+)(.*)',l)
        if m: d[m.group(1)+' '+m.group(3).strip()[:50]]=sum(int(x) for x in m.group(2).split())
    return d
a,b=irq('kyf37-rom/idle-irq1.txt'),irq('kyf37-rom/idle-irq2.txt')
print('--- interrupts in 60 s (top 12)')
for k,v in sorted(((k,b[k]-a.get(k,0)) for k in b),key=lambda x:-x[1])[:12]: print(v,k)
def procs(p):
    d={}
    for l in open(p,errors='ignore'):
        t=l.split(None,3)
        if len(t)>=3 and t[2].isdigit() and t[3-1].isdigit(): d[t[0]]=(int(t[1]) if False else 0)
    return d
def proc2(p):
    d={}
    for l in open(p,errors='ignore'):
        parts=l.rstrip('\n').split(' ',4)
        if len(parts)>=4:
            try: d[parts[0]]=(int(parts[2])+int(parts[3]), parts[1]+' '+(parts[4] if len(parts)>4 else ''))
            except ValueError: pass
    return d
p1,p2=proc2('kyf37-rom/idle-p1.txt'),proc2('kyf37-rom/idle-p2.txt')
print('--- cpu ticks (utime+stime) in 60 s (top 12)')
for pid,(t,n) in sorted(((k,(v[0]-p1.get(k,(0,''))[0],v[1])) for k,v in p2.items()),key=lambda x:-x[1][0])[:12]: print(pid,t,n)
def ws(p):
    d={}
    for l in open(p,errors='ignore').read().splitlines()[1:]:
        c=l.split()
        if len(c)>5:
            try: d[c[0]]=(int(c[2]),int(c[6]) if len(c)>6 else 0)
            except ValueError: pass
    return d
w1,w2=ws('kyf37-rom/idle-ws1.txt'),ws('kyf37-rom/idle-ws2.txt')
print('--- wakeup sources by active_count delta (top 10)')
for k,v in sorted(((k,w2[k][0]-w1.get(k,(0,0))[0]) for k in w2),key=lambda x:-x[1])[:10]: print(v,k)
