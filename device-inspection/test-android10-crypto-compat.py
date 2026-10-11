"""Exercise real rebuilt host crypto implementations, without using owner keys."""
import ctypes as c, hashlib, json
from pathlib import Path
lib=c.CDLL('/home/pablo/kyf37-android10/out/host/linux-x86/lib64/libcrypto-host.so')
def fn(name,result,args):
    f=getattr(lib,name);f.restype=result;f.argtypes=args;return f
ptr=c.c_void_p;integer=c.c_int
bio_base64=fn('BIO_f_base64',ptr,[])
bio_new=fn('BIO_new',ptr,[ptr])
bio_mem=fn('BIO_new_mem_buf',ptr,[ptr,integer])
bio_flags=fn('BIO_set_flags',None,[ptr,integer])
bio_push=fn('BIO_push',ptr,[ptr,ptr])
bio_read=fn('BIO_read',integer,[ptr,ptr,integer])
bio_free=fn('BIO_free_all',None,[ptr])
results={}
for label,encoded,expected in [('base64_valid',b'a3lmMzc=',b'kyf37'),('base64_invalid',b'!!!!',None)]:
    data=c.create_string_buffer(encoded);out=c.create_string_buffer(64)
    chain=bio_new(bio_base64());assert chain
    bio_flags(chain,0x100)
    mem=bio_mem(data,len(encoded));assert mem
    assert bio_push(chain,mem)==chain
    try:
        size=bio_read(chain,out,64)
        if expected is None:assert size<=0
        else:assert size==len(expected) and out.raw[:size]==expected
        results[label]={'passed':True,'bytes_read':size}
    finally:bio_free(chain)
bn_new=fn('BN_new',ptr,[]);bn_set=fn('BN_set_word',integer,[ptr,c.c_ulong]);bn_free=fn('BN_free',None,[ptr])
rsa_new=fn('RSA_new',ptr,[]);rsa_free=fn('RSA_free',None,[ptr]);rsa_gen=fn('RSA_generate_key_ex',integer,[ptr,integer,ptr,ptr]);rsa_size=fn('RSA_size',c.c_uint,[ptr])
sha256=fn('EVP_sha256',ptr,[])
encode=fn('RSA_padding_add_PKCS1_PSS_mgf1',integer,[ptr,ptr,ptr,ptr,ptr,integer])
verify=fn('RSA_verify_PKCS1_PSS',integer,[ptr,ptr,ptr,ptr,integer])
key=rsa_new();exponent=bn_new();assert key and exponent
try:
    assert bn_set(exponent,65537)==1 and rsa_gen(key,1024,exponent,None)==1
    digest=c.create_string_buffer(hashlib.sha256(b'KYF37 Android 10 compatibility').digest())
    wrong=c.create_string_buffer(hashlib.sha256(b'wrong message').digest())
    encoded=c.create_string_buffer(rsa_size(key))
    assert encode(key,encoded,digest,sha256(),None,32)==1
    assert verify(key,digest,sha256(),encoded,32)==1
    assert verify(key,wrong,sha256(),encoded,32)==0
    corrupted=c.create_string_buffer(bytes([encoded.raw[0]^1])+encoded.raw[1:])
    assert verify(key,digest,sha256(),corrupted,32)==0
    results['rsa_pss']={'valid_passed':True,'wrong_digest_rejected':True,'corrupted_encoding_rejected':True}
finally:
    rsa_free(key);bn_free(exponent)
report={'tests':results,'scope':'Rebuilt host library implementations only; Android ARM exports/ABI and actual GPU loading require separate checks. Fresh disposable RSA key; owner signing key never accessed.'}
Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/kyf37-rom/android10-crypto-compat-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
