"""Run only between builds: restore legacy ABI required by stock Adreno."""
from pathlib import Path
tree=Path('/home/pablo/kyf37-lineage')
header=tree/'external/boringssl/src/include/openssl/rsa.h'
source=tree/'external/boringssl/src/crypto/rsa/padding.c'
declaration='''/* Legacy vendor ABI; NULL MGF digest uses the message digest. */
OPENSSL_EXPORT int RSA_verify_PKCS1_PSS(RSA *key, const uint8_t *digest,
                                      const EVP_MD *algorithm,
                                      const uint8_t *encoded, int salt_length);

'''
function='''/* Legacy vendor ABI; validation stays in the existing PSS verifier. */
int RSA_verify_PKCS1_PSS(RSA *key, const uint8_t *digest,
                       const EVP_MD *algorithm, const uint8_t *encoded,
                       int salt_length) {
  return RSA_verify_PKCS1_PSS_mgf1(key, digest, algorithm, NULL, encoded,
                                  salt_length);
}

'''
s=header.read_text()
if 'int RSA_verify_PKCS1_PSS(' not in s:
    anchor='/* RSA_verify_PKCS1_PSS_mgf1 verifies'
    assert s.count(anchor)==1
    header.write_text(s.replace(anchor,declaration+anchor))
s=source.read_text()
if 'int RSA_verify_PKCS1_PSS(' not in s:
    anchor='int RSA_verify_PKCS1_PSS_mgf1('
    assert s.count(anchor)==1
    source.write_text(s.replace(anchor,function+anchor))
print('Legacy PSS symbol restored by delegation to the existing verifier.')
