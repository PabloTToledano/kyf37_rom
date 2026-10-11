#!/usr/bin/env python3
"""Adapt the stock Kyocera audio HAL's 36-byte PCM config to Android 10's 40-byte ABI."""
from pathlib import Path
w=Path(__file__).resolve().parent
tree=Path.home()/'kyf37-android10';p=tree/'external/tinyalsa/pcm.c';s=p.read_text()
if 'KYF37 legacy PCM config ABI' not in s:
 s='#ifndef _GNU_SOURCE\n#define _GNU_SOURCE\n#endif\n#include <dlfcn.h>\n#include <stddef.h>\n'+s
 anchor='''    pcm = calloc(1, sizeof(struct pcm));'''
 start=s.index('struct pcm *pcm_open(');at=s.index(anchor,start)
 patch='''    /* KYF37 legacy PCM config ABI: Android 5 has avail_min at offset 32;
     * Android 10 inserted silence_size there and moved avail_min to offset 36.
     * Only translate the owner device's proprietary HAL; modern callers retain
     * their original ABI. Never read past the stock 36-byte object. */
    struct pcm_config translated_config;
    struct pcm_config *legacy_config = NULL;
    Dl_info caller;
    if (dladdr(__builtin_return_address(0), &caller) && caller.dli_fname &&
        strstr(caller.dli_fname, "audio.primary.msm8909.so")) {
        legacy_config = config;
        memset(&translated_config, 0, sizeof translated_config);
        memcpy(&translated_config, config, offsetof(struct pcm_config, silence_size));
        memcpy(&translated_config.avail_min, (const char *)config + 32,
               sizeof translated_config.avail_min);
        config = &translated_config;
    }
'''
 s=s[:at]+patch+s[at:]
 anchor='''    config->period_count = param_get_int(&params, SNDRV_PCM_HW_PARAM_PERIODS);'''
 assert s.count(anchor)==1
 s=s.replace(anchor,anchor+'''
    if (legacy_config) {
        legacy_config->period_size = config->period_size;
        legacy_config->period_count = config->period_count;
    }''')
 p.write_text(s)
p=tree/'external/tinyalsa/pcm.c';s=p.read_text()
if '#ifdef __ANDROID__\n    struct pcm_config translated_config;' not in s:
 s=s.replace('    struct pcm_config translated_config;\n    struct pcm_config *legacy_config = NULL;','    struct pcm_config *legacy_config = NULL;\n#ifdef __ANDROID__\n    struct pcm_config translated_config;')
 s=s.replace('        config = &translated_config;\n    }\n    pcm = calloc','        config = &translated_config;\n    }\n#endif\n    pcm = calloc')
p.write_text(s)
p=tree/'external/tinyalsa/Android.bp';s=p.read_text()
s=s.replace('\n    shared_libs: ["libdl"],','')
if 'shared_libs: ["libdl"]' not in s:s=s.replace('    target: {','    target: {\n        android: { shared_libs: ["libdl"] },',1)
p.write_text(s)
print('Stock audio HAL pcm_open translation staged; other callers unchanged')
