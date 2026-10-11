#!/usr/bin/env python3
"""KYF37: VFS core patches sdcardfs (android-3.10) needs: per-mount private data, permission2/setattr2/truncate2, magic number.
Patches are the AOSP android-3.10 commits stored in third-party/sdcardfs/patches (see README there). Idempotent (WSL).
Run after fix-android10-kernel-sdcardfs.py."""
import os, subprocess
home = os.path.expanduser('~')
k = home + '/kyf37-rom/kernel-android10'
P = '/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/third-party/sdcardfs/patches/'
APPLIED = 'permission2' in open(k + '/include/linux/fs.h').read()
if APPLIED:
    print('vfs patches already applied')
def run(*a):
    return subprocess.run(a, cwd=k, capture_output=True, text=True)
def git_apply(name, *extra):
    r = run('git', 'apply', *extra, P + name)
    assert r.returncode == 0, (name, r.stderr)
def fuzz_patch(name):
    r = subprocess.run('patch -p1 -F3 --no-backup-if-mismatch < ' + P + name, shell=True, cwd=k, capture_output=True, text=True)
    print(name, 'rc', r.returncode)
if not APPLIED:
    git_apply('0001-Initial-port-of-sdcardfs.patch', '--exclude=fs/Kconfig', '--exclude=fs/Makefile')
    git_apply('0001-mnt-Add-filesystem-private-data-to-mount-points.patch')
    for n in ['0001-vfs-Allow-filesystems-to-access-their-private-mount-.patch',
              '0001-vfs-Add-permission2-for-filesystems-with-per-mount-p.patch',   # 1 hunk (may_create) rejects, fixed below
              '0001-vfs-Add-setattr2-for-filesystems-with-per-mount-perm.patch']:
        fuzz_patch(n)
    git_apply('0001-ANDROID-vfs-Missed-updating-truncate-to-truncate2.patch')
    fuzz_patch('0001-ANDROID-mnt-Fix-freeing-of-mount-data.patch')
    git_apply('0001-ANDROID-xattr-Pass-EOPNOTSUPP-to-permission2.patch')
    git_apply('0001-sdcardfs-Change-magic-value.patch')
    p = k + '/fs/namei.c'
    s = open(p).read()
    NL = chr(10); T = chr(9)
    old = 'static inline int may_create(struct inode *dir, struct dentry *child)' + NL + '{' + NL + T + 'audit_inode_child(dir, child, AUDIT_TYPE_CHILD_CREATE);' + NL + T + 'if (child->d_inode)' + NL + T + T + 'return -EEXIST;' + NL + T + 'if (IS_DEADDIR(dir))' + NL + T + T + 'return -ENOENT;' + NL + T + 'return inode_permission(dir, MAY_WRITE | MAY_EXEC);'
    new = old.replace('(struct inode *dir,', '(struct vfsmount *mnt, struct inode *dir,').replace('inode_permission(dir,', 'inode_permission2(mnt, dir,')
    if old in s:
        open(p, 'w').write(s.replace(old, new))
    for rej in subprocess.run('find . -name "*.rej"', shell=True, cwd=k, capture_output=True, text=True).stdout.split():
        if rej.endswith('fs/namei.c.rej'):
            os.remove(k + '/' + rej)
        else:
            print('UNEXPECTED reject', rej)
    print('done')
NL = chr(10); T = chr(9)
# sdcardfs: this kernel has no d_canonical_path dentry op (only affects fsnotify canonical paths): drop the initializer and make the helper unused-safe
d = k + '/fs/sdcardfs/dentry.c'
t = open(d).read()
line = chr(9) + '.d_canonical_path = sdcardfs_canonical_path,' + NL
if line in t:
    t = t.replace(line, '')
    t = t.replace('static void sdcardfs_canonical_path(', '__maybe_unused static void sdcardfs_canonical_path(')
    open(d, 'w').write(t)
    print('dentry.c patched')
# 3.10.49 has no iterate()/dir_context (3.11+): use readdir()/vfs_readdir() and a tiny compat shim for lookup.c's name search
h = k + '/fs/sdcardfs/sdcardfs.h'
t = open(h).read()
if 'KYF37 dir_context compat' not in t:
    shim = ('/* KYF37 dir_context compat (3.10.49 has readdir/filldir only) */' + NL +
            'struct dir_context { filldir_t actor; loff_t pos; };' + NL +
            'static inline int iterate_dir(struct file *f, struct dir_context *ctx)' + NL +
            '{ return vfs_readdir(f, ctx->actor, ctx); }' + NL + NL)
    marker = '#include "multiuser.h"'
    assert t.count(marker) == 1
    open(h, 'w').write(t.replace(marker, marker + NL + NL + shim))
    print('sdcardfs.h shim added')
f = k + '/fs/sdcardfs/file.c'
t = open(f).read()
if 'struct dir_context *ctx)' in t:
    t = t.replace('static int sdcardfs_readdir(struct file *file, struct dir_context *ctx)', 'static int sdcardfs_readdir(struct file *file, void *dirent, filldir_t filldir)')
    t = t.replace('err = iterate_dir(lower_file, ctx);', 'err = vfs_readdir(lower_file, filldir, dirent);')
    t = t.replace('.iterate' + chr(9) + '= sdcardfs_readdir,', '.readdir' + chr(9) + '= sdcardfs_readdir,')
    open(f, 'w').write(t)
    print('file.c readdir adapted')
