#!/usr/bin/env python3
"""KYF37: backport a minimal memfd_create (ARM syscall 385) to the 3.10.49 kernel (idempotent, WSL).
Android 10 ART's JIT maps its code cache twice (RW + RX) from a memfd. Without the syscall the zygote logs
'Failed to initialize dual view JIT. memfd_create() error: Function not implemented' and system_server then crashes in the JIT
thread pool (SEGV_ACCERR in mspace_malloc), which is why JIT was disabled and all apps ran interpreted.
Sealing is not implemented (ART Q does not use it)."""
import os
k = os.path.expanduser('~/kyf37-rom/kernel-android10')
NL = chr(10); T = chr(9)
def edit(path, old, new, marker):
    s = open(k + '/' + path).read()
    if marker in s:
        return
    assert s.count(old) == 1, (path, s.count(old))
    open(k + '/' + path, 'w').write(s.replace(old, new))
    print('edited', path)
# syscall table: 382 renameat2, 383 seccomp, 384 getrandom (not implemented in this kernel), 385 memfd_create
edit('arch/arm/kernel/calls.S',
     T + T + 'CALL(sys_sched_getattr)' + NL,
     T + T + 'CALL(sys_sched_getattr)' + NL + T + T + 'CALL(sys_ni_syscall)' + NL + T + T + 'CALL(sys_ni_syscall)' + NL + T + T + 'CALL(sys_ni_syscall)' + NL + '/* 385 */' + T + 'CALL(sys_memfd_create)' + NL,
     'sys_memfd_create')
edit('arch/arm/include/asm/unistd.h', '#define __NR_syscalls  (384)', '#define __NR_syscalls  (388)', '(388)')
edit('arch/arm/include/uapi/asm/unistd.h',
     '#define __NR_sched_getattr' + T + T + '(__NR_SYSCALL_BASE+381)' + NL,
     '#define __NR_sched_getattr' + T + T + '(__NR_SYSCALL_BASE+381)' + NL + '#define __NR_memfd_create' + T + T + '(__NR_SYSCALL_BASE+385)' + NL,
     '__NR_memfd_create')
code = '''
/* KYF37: minimal memfd_create backport (see device-inspection/fix-android10-kernel-memfd.py) */
#define KYF37_MFD_CLOEXEC 0x0001U
#define KYF37_MFD_ALLOW_SEALING 0x0002U

SYSCALL_DEFINE2(memfd_create, const char __user *, uname, unsigned int, flags)
{
	struct file *file;
	int fd, error;
	char *name;
	long len;

	if (flags & ~(KYF37_MFD_CLOEXEC | KYF37_MFD_ALLOW_SEALING))
		return -EINVAL;

	len = strnlen_user(uname, 249);
	if (len <= 0)
		return -EFAULT;
	if (len > 249)
		return -EINVAL;

	name = kmalloc(len + 6, GFP_KERNEL);
	if (!name)
		return -ENOMEM;
	memcpy(name, "memfd:", 6);
	if (copy_from_user(name + 6, uname, len)) {
		error = -EFAULT;
		goto err_name;
	}
	name[len + 5] = 0;

	fd = get_unused_fd_flags((flags & KYF37_MFD_CLOEXEC) ? O_CLOEXEC : 0);
	if (fd < 0) {
		error = fd;
		goto err_name;
	}
	file = shmem_file_setup(name, 0, VM_NORESERVE);
	if (IS_ERR(file)) {
		error = PTR_ERR(file);
		goto err_fd;
	}
	file->f_mode |= FMODE_LSEEK | FMODE_PREAD | FMODE_PWRITE;
	file->f_flags |= O_RDWR | O_LARGEFILE;
	fd_install(fd, file);
	kfree(name);
	return fd;

err_fd:
	put_unused_fd(fd);
err_name:
	kfree(name);
	return error;
}
'''
p = k + '/mm/shmem.c'
s = open(p).read()
if 'sys_memfd_create' not in s and 'SYSCALL_DEFINE2(memfd_create' not in s:
    s = s.rstrip(NL) + NL + code
    if '#include <linux/syscalls.h>' not in s:
        s = s.replace('#include <linux/pagemap.h>', '#include <linux/pagemap.h>' + NL + '#include <linux/syscalls.h>', 1)
    open(p, 'w').write(s)
    print('mm/shmem.c: memfd_create added')
