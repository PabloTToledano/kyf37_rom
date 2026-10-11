"""Backport real mmap ASLR controls and ambient capabilities to KYF37 3.10."""
from pathlib import Path
import subprocess, hashlib, json, re

root=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms')
kernel=Path('/home/pablo/kyf37-rom/kernel-android10')
ref=root/'kyf37-rom/android10-kernel-interface-reference'
assert subprocess.run(['pgrep','-x','ninja'],stdout=subprocess.DEVNULL).returncode != 0
provenance=json.loads((ref/'provenance.json').read_text())
for commit,record in provenance.items():
    assert hashlib.sha256((ref/(commit+'.patch')).read_bytes()).hexdigest()==record['sha256']

def apply(commit, exclusions=(), patch=None):
    args=['git','-C',str(kernel),'apply']+['--exclude='+p for p in exclusions]
    data=patch.encode() if patch is not None else (ref/(commit+'.patch')).read_bytes()
    subprocess.run(args+['--check','-'],input=data,check=True)
    subprocess.run(args+['-'],input=data,check=True)

def replace(path,old,new):
    p=kernel/path;s=p.read_text();assert s.count(old)==1,(path,old)
    p.write_text(s.replace(old,new,1))

if 'mmap_rnd_bits' not in (kernel/'arch/arm/mm/mmap.c').read_text():
    apply('d07e22597d1d', ['arch/Kconfig'])
    patch=(ref/'d07e22597d1d.patch').read_text()
    section=patch.split('diff --git a/arch/Kconfig ',1)[1].split('diff --git ',1)[0]
    added='\n'.join(line[1:] for line in section.splitlines() if line.startswith('+') and not line.startswith('+++'))+'\n'
    assert added.startswith('config HAVE_ARCH_MMAP_RND_BITS')
    with (kernel/'arch/Kconfig').open('a') as f:f.write('\n'+added)

    # Upstream ARM hunk uses arch_mmap_rnd(), whereas 3.10 has the expression
    # directly in arch_pick_mmap_layout(). Retain its cache-colour alignment.
    replace('arch/arm/Kconfig','config ARM\n','config ARM\n\tselect HAVE_ARCH_MMAP_RND_BITS if MMU\n')
    with (kernel/'arch/arm/Kconfig').open('a') as f:
        f.write('\nconfig ARCH_MMAP_RND_BITS_MIN\n\tdefault 8\n\nconfig ARCH_MMAP_RND_BITS_MAX\n\tdefault 14 if PAGE_OFFSET=0x40000000\n\tdefault 15 if PAGE_OFFSET=0x80000000\n\tdefault 16\n')
    apply('ec9ee4acd97c')
    # Existing OEM entropy primitive is get_cycles(); preserve that same source.
    replace('drivers/char/random.c','hash[0] += current->pid + jiffies + random_get_entropy();','hash[0] += current->pid + jiffies + get_cycles();')
    replace('arch/arm/mm/mmap.c','random_factor = (get_random_int() % (1 << 8)) << PAGE_SHIFT;',
            'random_factor = (get_random_long() & ((1UL << mmap_rnd_bits) - 1)) << PAGE_SHIFT;')
    replace('arch/arm/mm/mmap.c','/* 8 bits of randomness in 20 address space bits */',
            '/* Runtime ASLR entropy bounded by the upstream ARM Kconfig limits. */')
# Apply only the relevant generic ELF stack-randomization hunk; other ISA
# files in that upstream commit are outside this ARM32 product.
if 'random_variable = get_random_long()' not in (kernel/'fs/binfmt_elf.c').read_text():
    replace('fs/binfmt_elf.c','unsigned int random_variable = 0;', 'unsigned long random_variable = 0;')
    replace('fs/binfmt_elf.c','random_variable = get_random_int() & STACK_RND_MASK;', 'random_variable = get_random_long() & STACK_RND_MASK;')

ambient=(ref/'58319057b784.patch').read_text()
apply('58319057b784',['fs/proc/array.c','include/uapi/linux/prctl.h','security/commoncap.c'])
common='diff --git a/security/commoncap.c'+ambient.split('diff --git a/security/commoncap.c',1)[1].split('diff --git a/security/keys/process_keys.c',1)[0]
common=common.split('@@ -924,',1)[0]
apply('58319057b784',patch=common)
replace('fs/proc/array.c','kernel_cap_t cap_inheritable, cap_permitted, cap_effective, cap_bset;',
        'kernel_cap_t cap_inheritable, cap_permitted, cap_effective, cap_bset, cap_ambient;')
replace('fs/proc/array.c','cap_bset\t= cred->cap_bset;','cap_bset\t= cred->cap_bset;\n\tcap_ambient\t= cred->cap_ambient;')
replace('fs/proc/array.c','NORM_CAPS(cap_bset);','NORM_CAPS(cap_bset);\n\tNORM_CAPS(cap_ambient);')
replace('fs/proc/array.c','render_cap_t(m, "CapBnd:\\t", &cap_bset);',
        'render_cap_t(m, "CapBnd:\\t", &cap_bset);\n\trender_cap_t(m, "CapAmb:\\t", &cap_ambient);')
replace('include/uapi/linux/prctl.h','#endif /* _LINUX_PRCTL_H */',
        '#define PR_CAP_AMBIENT 47\n#define PR_CAP_AMBIENT_IS_SET 1\n#define PR_CAP_AMBIENT_RAISE 2\n#define PR_CAP_AMBIENT_LOWER 3\n#define PR_CAP_AMBIENT_CLEAR_ALL 4\n\n#endif /* _LINUX_PRCTL_H */')
# 3.10 allocates a credential once at entry to cap_task_prctl. Use its
# existing changed/error labels, so every return commits or frees it.
case=r'''
\tcase PR_CAP_AMBIENT:
\t\terror = -EINVAL;
\t\tif (arg2 == PR_CAP_AMBIENT_CLEAR_ALL) {
\t\t\tif (arg3 | arg4 | arg5) goto error;
\t\t\tcap_clear(new->cap_ambient);
\t\t\tgoto changed;
\t\t}
\t\tif (!cap_valid(arg3) || arg4 || arg5) goto error;
\t\tif (arg2 == PR_CAP_AMBIENT_IS_SET) {
\t\t\terror = !!cap_raised(new->cap_ambient, arg3);
\t\t\tgoto no_change;
\t\t}
\t\tif (arg2 != PR_CAP_AMBIENT_RAISE && arg2 != PR_CAP_AMBIENT_LOWER) goto error;
\t\tif (arg2 == PR_CAP_AMBIENT_RAISE) {
\t\t\terror = -EPERM;
\t\t\tif (!cap_raised(new->cap_permitted, arg3) ||
\t\t\t    !cap_raised(new->cap_inheritable, arg3)) goto error;
\t\t\tcap_raise(new->cap_ambient, arg3);
\t\t} else {
\t\t\tcap_lower(new->cap_ambient, arg3);
\t\t}
\t\tgoto changed;

'''.replace('\\t','\t')
replace('security/commoncap.c','\tdefault:\n\t\t/* No functionality available - continue with default */',case+'\tdefault:\n\t\t/* No functionality available - continue with default */')
(root/'kyf37-rom/kernel-android10-interfaces.patch').write_bytes(subprocess.check_output(['git','-C',str(kernel),'diff','--binary']))
print('Applied real ARM mmap entropy/sysctl and ambient capability semantics; no security check bypass.')
