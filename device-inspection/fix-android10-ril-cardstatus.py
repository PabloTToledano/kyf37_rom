#!/usr/bin/env python3
"""Idempotent patch of hardware/ril/libril/ril_service.cpp getIccCardStatusResponse.
Root cause (2026-10-11): Qualcomm's Android 5.1 qcril returns RIL_REQUEST_GET_SIM_STATUS as 284 bytes: a 7-word header
(card_state, universal_pin_state, [extra word], gsm_idx, cdma_idx, ims_idx, num_applications) followed by 8 x RIL_AppStatus (32 B),
whereas Android 10's RIL_CardStatus_v6 has a 6-word header (280 B). Android 10 rejected the response with
'getIccCardStatusResponse: Invalid response' (INVALID_RESPONSE) so UiccController never got a card status.
Fix: when responseLen == 284 convert the legacy layout into a local RIL_CardStatus_v6 before validating.
KYF37_RIL_MODE=diag adds a full hex dump of the response (debug builds only); default 'convert'."""
import os, pathlib, re
f = pathlib.Path.home() / 'kyf37-android10/hardware/ril/libril/ril_service.cpp'
t = f.read_text()
MODE = os.environ.get('KYF37_RIL_MODE', 'convert')
marker = 'KYF37_CARDSTATUS_PATCH'
old = '''        if (response == NULL || responseLen != sizeof(RIL_CardStatus_v6)
                || p_cur->gsm_umts_subscription_app_index >= p_cur->num_applications
                || p_cur->cdma_subscription_app_index >= p_cur->num_applications
                || p_cur->ims_subscription_app_index >= p_cur->num_applications) {
            RLOGE("getIccCardStatusResponse: Invalid response");'''
if marker in t:
    t = re.sub(r'/\* KYF37_CARDSTATUS_PATCH begin \*/.*?/\* KYF37_CARDSTATUS_PATCH end \*/', '@@ORIG@@', t, flags=re.S)
    t = t.replace('@@ORIG@@', old)
assert old in t, 'original check not found'
dump = ''
if MODE == 'diag':
    dump = r'''        if (response != NULL) {
            const unsigned char *kb = (const unsigned char *) response;
            char kh[2 * 300 + 1] = {0};
            size_t kn = responseLen < 300 ? responseLen : 300;
            for (size_t ki = 0; ki < kn; ki++) snprintf(kh + 2 * ki, 3, "%02x", kb[ki]);
            RLOGE("KYF37 card status raw len=%zu: %s", responseLen, kh);
        }
'''
conv = r'''/* KYF37_CARDSTATUS_PATCH begin */
        /* Qualcomm Android 5.1 qcril layout: 7-word header + 8 app slots (284 bytes). */
        RIL_CardStatus_v6 kyf37Conv;
        if (response != NULL && responseLen == sizeof(RIL_CardStatus_v6) + sizeof(int)) {
            const int *kw = (const int *) response;
            memset(&kyf37Conv, 0, sizeof(kyf37Conv));
            kyf37Conv.card_state = (RIL_CardState) kw[0];
            kyf37Conv.universal_pin_state = (RIL_PinState) kw[1];
            kyf37Conv.gsm_umts_subscription_app_index = kw[3];
            kyf37Conv.cdma_subscription_app_index = kw[4];
            kyf37Conv.ims_subscription_app_index = kw[5];
            kyf37Conv.num_applications = kw[6];
            memcpy(kyf37Conv.applications, kw + 7, sizeof(kyf37Conv.applications));
            p_cur = &kyf37Conv;
            responseLen = sizeof(RIL_CardStatus_v6);
        }
''' + dump
new_cond = old.replace('responseLen != sizeof(RIL_CardStatus_v6)',
        'responseLen != sizeof(RIL_CardStatus_v6) || p_cur->num_applications < 0 || p_cur->num_applications > RIL_CARD_MAX_APPS')
patched = conv + new_cond + '\n/* KYF37_CARDSTATUS_PATCH end */'
t = t.replace(old, patched, 1)
f.write_text(t, newline=chr(10))
print('patched ril_service.cpp, mode =', MODE)
