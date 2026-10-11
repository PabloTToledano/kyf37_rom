from pathlib import Path
p=Path('/home/pablo/kyf37-rom/kernel-android10/security/selinux/nlmsgtab.c')
s=p.read_text()
lines=[line for line in s.splitlines() if '{ SOCK_DESTROY_BACKPORT,' in line]
assert len(lines)==1
line=lines[0]
replacement='#ifdef SOCK_DESTROY_BACKPORT\n'+line+'\n#endif'
if replacement not in s:
 assert s.count(line)==1
 p.write_text(s.replace(line,replacement))
print('Guarded absent optional netlink socket-destroy backport; no opcode invented')
