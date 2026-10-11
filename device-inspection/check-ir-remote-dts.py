"""Check the SIX actual boot QCDT payloads expose the original IR GPIO mux."""
from pathlib import Path
import subprocess,struct,json,hashlib
k=Path.home()/'kyf37-rom/kernel-android10';build=Path.home()/'kyf37-rom/kernel-android10-gcc48-build'
out=Path.home()/'kyf37-rom/ir-remote-tests';out.mkdir(exist_ok=True)
cpp=out/'msm8909-ir-remote.dts';dtb=out/'msm8909-ir-remote.dtb';decoded=out/'msm8909-ir-remote-decoded.dts'
with cpp.open('w') as f:
    subprocess.run(['gcc','-E','-P','-x','assembler-with-cpp','-nostdinc','-undef','-D__DTS__','-I',str(k/'include'),'-I',str(k/'arch/arm/boot/dts'),str(k/'arch/arm/boot/dts/qcom/msm8909-qrd-skua.dts')],stdout=f,check=True)
dtc=build/'scripts/dtc/dtc'
with (out/'dts-validation.log').open('w') as log:
    subprocess.run([str(dtc),'-I','dts','-O','dtb','-o',str(dtb),str(cpp)],stderr=log,check=True)
    subprocess.run([str(dtc),'-I','dtb','-O','dts','-o',str(decoded),str(dtb)],stderr=log,check=True)
def nodes(blob):
    magic,size,so,strings=struct.unpack_from('>4I',blob)
    assert magic==0xd00dfeed and size<=len(blob)
    pos=so;stack=[];result={}
    while True:
        token=struct.unpack_from('>I',blob,pos)[0];pos+=4
        if token==1:
            end=blob.index(0,pos);name=blob[pos:end].decode();pos=(end+4)&~3
            stack.append(name);result['/'.join(stack)]={}
        elif token==2:stack.pop()
        elif token==3:
            length,noff=struct.unpack_from('>2I',blob,pos);pos+=8
            end=blob.index(0,strings+noff);name=blob[strings+noff:end].decode()
            result['/'.join(stack)][name]=blob[pos:pos+length];pos=(pos+length+3)&~3
        elif token==4:pass
        elif token==9:return result
        else:raise AssertionError(token)
def cells(p):return list(struct.unpack('>'+str(len(p)//4)+'I',p))
raw=(Path.home()/'kyf37-android10/device/kyocera/kyf37/dt.img').read_bytes()
magic,version,count=struct.unpack_from('<3I',raw);assert magic==0x54444351 and version==3 and count==6
report=[]
for i in range(count):
    e=struct.unpack_from('<10I',raw,12+i*40);blob=raw[e[8]:e[8]+e[9]];ns=nodes(blob)
    handles={cells(p.get('phandle',p.get('linux,phandle')))[0]:n for n,p in ns.items() if 'phandle' in p or 'linux,phandle' in p}
    uart=next((n for n,p in ns.items() if 'reg' in p and 0x078b0000 in cells(p['reg'])),None);assert uart
    names=ns[uart]['pinctrl-names'].rstrip(b'\0').decode().split('\0')
    assert 'uart3_inactive' in names and 'uart3_active' in names
    states={}
    for label,function in [('uart3_inactive',0),('uart3_active',3)]:
        phandles=cells(ns[uart]['pinctrl-'+str(names.index(label))]);found=[]
        for h in phandles:
            node=handles[h];parent=node.rsplit('/',1)[0];p=ns[parent]
            if 'qcom,pins' in p and cells(p['qcom,pins'])[-1]==20:
                assert cells(p['qcom,pin-func'])==[function],(label,p)
                found.append(node)
        assert len(found)==1,(label,found);states[label]=found[0]
    report.append({'entry':i,'identity':e[:8],'uart':uart,'tx_gpio':20,'states':states,'dtb_sha256':hashlib.sha256(blob).hexdigest()})
deliver=Path(__file__).resolve().parent.parent/'kyf37-rom/ir-remote'
(deliver/'stock-qcdt-ir-audit.json').write_text(json.dumps({'qcdt_sha256':hashlib.sha256(raw).hexdigest(),'entries':report,'modified':False},indent=2)+'\n')
print('PASS: all six actual stock QCDT entries expose TX20 GPIO inactive / UART active states')
print('Stock dt.img unchanged; representative source DTS also compiles; no new DTB required')
