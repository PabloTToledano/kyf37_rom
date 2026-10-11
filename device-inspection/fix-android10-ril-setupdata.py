#!/usr/bin/env python3
"""Idempotent: hardware/ril/libril/ril_service.cpp dispatchStrings(varargs) allocates 2 extra NULL slots.
Root cause (2026-10-11): Kyocera's Android 5.1 qcril qcril_data_request_setup_data_call reads data[0..8] of the
RIL_REQUEST_SETUP_DATA_CALL string array (data[7], data[8] are optional) and does strcat(buf, data[8]) when data[8] != NULL.
Android 10 libril sends only 7 strings (version<=14 path) so data[8] was out-of-bounds heap garbage (observed r1=1) ->
SIGSEGV in strcat -> rild crash loop on every data call -> radio proxy dead -> service state flaps IN_SERVICE/OUT_OF_SERVICE.
calloc'ing countStrings+2 pointers (zeroed) makes the optional entries NULL; request length stays countStrings*sizeof(char*)."""
import pathlib
f = pathlib.Path.home() / 'kyf37-android10/hardware/ril/libril/ril_service.cpp'
t = f.read_text()
old = '''    char **pStrings;
    pStrings = (char **)calloc(countStrings, sizeof(char *));
    if (pStrings == NULL) {
        RLOGE("Memory allocation failed for request %s", requestToString(request));
        sendErrorResponse(pRI, RIL_E_NO_MEMORY);
        return false;
    }
    va_list ap;'''
new = old.replace('calloc(countStrings, sizeof(char *));', 'calloc(countStrings + 2, sizeof(char *)); /* KYF37_SETUPDATA_PATCH: qcril reads up to 9 strings */')
if 'KYF37_SETUPDATA_PATCH' in t:
    print('already patched')
else:
    assert t.count(old) == 1
    f.write_text(t.replace(old, new)); print('patched')
