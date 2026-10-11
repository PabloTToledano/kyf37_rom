from pathlib import Path
import shutil
root=Path('/home/pablo/kyf37-android10')
p=root/'vendor/kyocera/kyf37/proprietary/etc/media_codecs.xml'
backup=p.with_suffix('.xml.stock-reference')
if not backup.exists():shutil.copy2(p,backup)
p.write_text('''<?xml version="1.0" encoding="utf-8"?>
<!-- KYF37 Android 10: tested legacy OMX software baseline. -->
<MediaCodecs>
 <Include href="media_codecs_google_audio.xml" />
 <Include href="media_codecs_google_telephony.xml" />
 <Include href="media_codecs_google_video.xml" />
</MediaCodecs>
''')
p=root/'device/kyocera/kyf37/device.mk'
s=p.read_text()
if '# KYF37 tested OMX software codecs' not in s:
 s+='\n# KYF37 tested OMX software codecs; Codec2 requires an unavailable HIDL mapper.\nPRODUCT_PROPERTY_OVERRIDES += debug.stagefright.ccodec=0\nPRODUCT_COPY_FILES += \\\n'
 files=['audio','telephony','video']
 s+=' \\\n'.join('    frameworks/av/media/libstagefright/data/media_codecs_google_'+f+'.xml:system/etc/media_codecs_google_'+f+'.xml' for f in files)+'\n'
p.write_text(s)
print('Actual OMX video tested; software audio/telephony XML supplied for coherent codec baseline')
