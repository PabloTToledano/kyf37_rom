"""Sign stock boot and KYF37 TWRP with a locally generated owner key."""
from pathlib import Path
import hashlib,json,runpy
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa,padding

p=Path(__file__).resolve().parent
t=runpy.run_path(str(p/'prepare-recovery-signing.py'))
read_tlv=t['read_tlv'];children=t['children'];boot_parts=t['boot_parts']
out=p.parent/'kyf37-twrp-device';out.mkdir(exist_ok=True)
def tlv(tag,data):
    n=len(data)
    length=bytes([n]) if n<128 else bytes([128+(n.bit_length()+7)//8])+n.to_bytes((n.bit_length()+7)//8,'big')
    return bytes([tag])+length+data
def seq(*data):return tlv(0x30,b''.join(data))
def integer(n):
    b=n.to_bytes(max(1,(n.bit_length()+7)//8),'big')
    if b[0]&128:b=b'\0'+b
    return tlv(2,b)

key_path=out/'owner-signing-key.pem'
if key_path.exists():
    private=serialization.load_pem_private_key(key_path.read_bytes(),password=None)
else:
    private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    key_path.write_bytes(private.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
public=private.public_key()
public_der=public.public_bytes(serialization.Encoding.DER,serialization.PublicFormat.PKCS1)
(out/'owner-public-key.der').write_bytes(public_der)
oem=t['oem'];ks=t['ks'];key=t['key']
new_keybag=seq(seq(key[0][2],public_der))
new_keystore=seq(ks[0][2],new_keybag,ks[2][2])
assert len(new_keystore)==len(oem)
original=(p.parent/'phone-backup/keystore-current.img').read_bytes()
owner_keystore=new_keystore+original[len(new_keystore):]
(out/'owner-keystore.img').write_bytes(owner_keystore)

report={'owner_key_bits':public.key_size,'private_key_file':str(key_path),'public_key_sha256':hashlib.sha256(public_der).hexdigest(),'keystore_sha256':hashlib.sha256(owner_keystore).hexdigest(),'images':[]}
items=[('boot-owner-signed.img',p.parent/'phone-backup/kyf37-root-backup/boot.img',b'/boot'),('stock-recovery-owner-signed.img',p.parent/'phone-backup/kyf37-root-backup/recovery.img',b'/recovery'),('kyf37-twrp-owner-signed.img',out/'kyf37-twrp-candidate.img',b'/recovery')]
for name,source,target in items:
    b,f,end=boot_parts(source)
    # Use the vendor's exact version/certificate/algorithm envelope. Its verifier
    # checks signatures with the selected keystore RSA key; see 0x8f60aee8.
    template=p.parent/'phone-backup/kyf37-root-backup'/('boot.img' if target==b'/boot' else 'recovery.img')
    tb,_,te=boot_parts(template)
    _,payload,_,_=read_tlv(tb,te)
    sig=children(payload);assert len(sig)==5
    attr=seq(tlv(0x13,target),integer(end))
    signed=private.sign(b[:end]+attr,padding.PKCS1v15(),hashes.SHA256())
    envelope=seq(sig[0][2],sig[1][2],sig[2][2],attr,tlv(4,signed))
    result=b[:end]+envelope
    assert len(result)<=16777216
    result+=bytes(16777216-len(result))
    public.verify(signed,result[:end]+attr,padding.PKCS1v15(),hashes.SHA256())
    assert result[:end]==b[:end]
    destination=out/name;destination.write_bytes(result)
    report['images'].append({'name':name,'source':str(source),'partition_bytes':len(result),'body_bytes':end,'source_body_preserved':True,'signature_verified':True,'sha256':hashlib.sha256(result).hexdigest(),'md5':hashlib.md5(result).hexdigest()})
(out/'owner-signing-manifest.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
