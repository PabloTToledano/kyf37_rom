"""Read the actual completed filesystem image, never a mounted live partition."""
from pathlib import Path
import subprocess,tempfile,hashlib,json
tree=Path('/home/pablo/kyf37-lineage')
product=tree/'out/target/product/kyf37'
host=Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom')
processes=subprocess.check_output(['ps','-eo','args'],text=True)
assert not any('ninja bootimage systemimage' in p for p in processes.splitlines()),'Build still active'
work=Path(tempfile.mkdtemp(prefix='system-image-',dir='/home/pablo/kyf37-rom'))
image=product/'system.img'
before=image.stat()
raw=work/'system.raw.img'
subprocess.run([str(tree/'out/host/linux-x86/bin/simg2img'),str(image),str(raw)],check=True)
assert raw.stat().st_size==1612709888
paths=['build.prop','framework/services.jar','framework/framework-res.apk',
       'priv-app/Kyf37OuterScreen/Kyf37OuterScreen.apk',
       'priv-app/Kyf37Home/Kyf37Home.apk',
       'app/Kyf37KeypadIME/Kyf37KeypadIME.apk',
       'etc/init.qcom.rootagent.sh','etc/enable-rom-app-root.sh',
       'usr/keylayout/matrix_keypad_67.kl','lib/libkyf37subdisplay.so',
       'lib/libcrypto.so','lib/libutils.so','lib/libEGL.so']
# Use the installed package locations recorded by this build, rather than
# assuming an app's privileged/nonprivileged path.
for i,relative in enumerate(paths):
    if not (product/'system'/relative).is_file() and relative.endswith('.apk'):
        matches=list((product/'system').rglob(Path(relative).name))
        assert len(matches)==1,(relative,matches)
        paths[i]=str(matches[0].relative_to(product/'system'))
paths += ['media/audio/ui/'+p.name for p in sorted((product/'system/media/audio/ui').iterdir()) if p.is_file()]
verified={}
for i,relative in enumerate(paths):
    destination=work/('asset-%03d'%i)
    result=subprocess.run(['debugfs','-R','dump /'+relative+' '+str(destination),str(raw)],capture_output=True,text=True)
    assert result.returncode==0 and destination.is_file(),(relative,result.stderr)
    installed=product/'system'/relative
    actual=destination.read_bytes();expected=installed.read_bytes()
    assert actual==expected,('Image differs from installed output',relative)
    verified[relative]={'bytes':len(actual),'sha256':hashlib.sha256(actual).hexdigest()}
absent=['bin/install-recovery.sh','etc/install-recovery.sh','recovery-from-boot.p','etc/recovery-resource.dat']
for relative in absent:
    result=subprocess.run(['debugfs','-R','stat /'+relative,str(raw)],capture_output=True,text=True)
    assert 'File not found' in result.stderr,(relative,result.stdout,result.stderr)
after=image.stat()
assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
(host/'final-system-content-verification.json').write_text(json.dumps({
    'image':str(image),'raw_image':str(raw),'verified_assets':verified,
    'recovery_replacement_payloads_absent':absent,
    'scope':'Actual filesystem image asset bytes and recovery payload absence; boot and hardware operation remain unverified.'},indent=2)+'\n')
print('Verified',len(verified),'assets inside the finished filesystem image; recovery replacement payloads absent.')
