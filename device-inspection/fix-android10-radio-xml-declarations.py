"""Make imported stock radio XML valid for Android's PRODUCT_COPY_FILES check.

Stock puts license comments before the XML declaration. Preserve all content,
moving only the declaration to the start. Idempotent, run in WSL.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

radio = Path.home() / 'kyf37-android10/device/kyocera/kyf37/radio'
for name in ('stock_data_qmi_config.xml', 'stock_data_dsi_config.xml',
             'stock_data_netmgr_config.xml'):
    path = radio / name
    text = path.read_text()
    match = re.search(r'<\?xml\s[^?]*\?>', text)
    assert match, name
    normalized = match.group() + '\n' + (text[:match.start()] + text[match.end():]).lstrip('\n')
    ET.fromstring(normalized)
    if normalized != text:
        path.write_text(normalized)
        print('normalized', name)
