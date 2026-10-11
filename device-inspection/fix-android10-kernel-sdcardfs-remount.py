#!/usr/bin/env python3
"""KYF37: propagate_remount() from the backported android-3.10 'private mount data' patch skips the LAST slave
(loop condition m->mnt_slave.next != &mnt->mnt_slave_list), so a mount with a single slave never receives the new per-view
sdcardfs options. Zygote's namespace clone is exactly that case, so every app saw the *default* view (gid 1015, no write)
and camera apps could not create DCIM/Camera ('Insert an SD card'). Walk all slaves, recursively. Idempotent (WSL)."""
import os
p = os.path.expanduser('~/kyf37-rom/kernel-android10/fs/pnode.c')
s = open(p).read()
if 'KYF37 propagate_remount' in s:
    print('already'); raise SystemExit
a = s.index('int propagate_remount(struct mount *mnt) {')
b = s.index(chr(10) + '}' + chr(10), a) + 3
new = '''/* KYF37 propagate_remount: update every (transitive) slave, including the last one */
static void kyf37_copy_to_slaves(struct super_block *sb, struct mount *master, struct mount *src)
{
	struct mount *m;

	list_for_each_entry(m, &master->mnt_slave_list, mnt_slave) {
		sb->s_op->copy_mnt_data(m->mnt.data, src->mnt.data);
		kyf37_copy_to_slaves(sb, m, src);
	}
}

int propagate_remount(struct mount *mnt)
{
	struct super_block *sb = mnt->mnt.mnt_sb;

	if (sb->s_op->copy_mnt_data)
		kyf37_copy_to_slaves(sb, mnt, mnt);

	return 0;
}
'''
open(p, 'w').write(s[:a] + new + s[b:])
print('patched')
