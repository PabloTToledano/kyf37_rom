#include <openssl/rsa.h>
#include <openssl/bn.h>
#include <openssl/sha.h>
#include <openssl/evp.h>
#include <stdio.h>
#include <string.h>
/* Same delegation as the pending ABI restoration. */
#ifndef KYF37_TEST_EXPORTED
int RSA_verify_PKCS1_PSS(RSA *key, const unsigned char *digest,
                       const EVP_MD *algorithm, const unsigned char *encoded,
                       int salt_length) {
    return RSA_verify_PKCS1_PSS_mgf1(key, digest, algorithm, NULL, encoded,
                                    salt_length);
}
#else
extern int RSA_verify_PKCS1_PSS(RSA *, const unsigned char *, const EVP_MD *,
                              const unsigned char *, int);
#endif
int main(void) {
    RSA *key=RSA_new(); BIGNUM *e=BN_new();
    unsigned char digest[SHA256_DIGEST_LENGTH], bad[SHA256_DIGEST_LENGTH];
    unsigned char encoded[256];
    if (!key || !e || !BN_set_word(e,65537) ||
        !RSA_generate_key_ex(key,2048,e,NULL)) return 2;
    SHA256((const unsigned char *)"KYF37 compatibility test",24,digest);
    if (!RSA_padding_add_PKCS1_PSS_mgf1(key,encoded,digest,EVP_sha256(),NULL,32)) return 3;
    int valid=RSA_verify_PKCS1_PSS(key,digest,EVP_sha256(),encoded,32);
    memcpy(bad,digest,sizeof bad); bad[0]^=1;
    int wrong_digest=RSA_verify_PKCS1_PSS(key,bad,EVP_sha256(),encoded,32);
    int wrong_salt=RSA_verify_PKCS1_PSS(key,digest,EVP_sha256(),encoded,20);
    encoded[255]^=1;
    int corrupted=RSA_verify_PKCS1_PSS(key,digest,EVP_sha256(),encoded,32);
    printf("valid=%d wrong_digest=%d wrong_salt=%d corrupted=%d\n",
           valid,wrong_digest,wrong_salt,corrupted);
    RSA_free(key); BN_free(e);
    return valid==1 && !wrong_digest && !wrong_salt && !corrupted ? 0 : 1;
}
