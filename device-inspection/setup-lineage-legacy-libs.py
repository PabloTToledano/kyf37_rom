import urllib.request,re,pathlib,subprocess
base='https://archive.ubuntu.com/ubuntu/pool/main/n/ncurses/'
s=urllib.request.urlopen(base).read().decode();dest=pathlib.Path('/home/pablo/kyf37-host-tools/legacy-libs');dest.mkdir(exist_ok=True)
for name in ['libncurses5','libtinfo5']:
 matches=sorted(set(re.findall('href="('+name+'_[^"]+_amd64.deb)"',s)))
 assert matches,name
 f=matches[-1];print(f);urllib.request.urlretrieve(base+f,dest/f);subprocess.run(['dpkg-deb','-x',str(dest/f),str(dest)],check=True)
