from pathlib import Path
import zipfile, re, json
from loguru import logger
from androguard.core.axml import ARSCParser, AXMLPrinter

logger.remove()
root = Path('kyf37-rom')
out = root/'stock-selector-assets'
out.mkdir(exist_ok=True)
with zipfile.ZipFile(root/'stock-framework-res.apk') as z:
    arsc = ARSCParser(z.read('resources.arsc'))
    todo, done, manifest = [0x01080551], set(), []
    while todo:
        rid = todo.pop()
        if rid in done: continue
        done.add(rid)
        name = arsc.get_resource_xml_name(rid, 'android')
        for config, source in arsc.get_resolved_res_configs(rid):
            if not isinstance(source,str) or not source.startswith('res/'):
                raise ValueError(f'Non-file dependency {rid:x}: {source}')
            dest = out/source
            dest.parent.mkdir(parents=True,exist_ok=True)
            data = z.read(source)
            if source.endswith('.xml'):
                xml = AXMLPrinter(data).get_xml().decode()
                def replace(match):
                    ref = int(match.group(1),16)
                    todo.append(ref)
                    mapped = arsc.get_resource_xml_name(ref,'android')
                    if not mapped: raise ValueError(f'Unresolved reference {ref:x}')
                    return mapped
                data = re.sub(r'@android:([0-9a-fA-F]{8})', replace, xml).encode()
            dest.write_bytes(data)
            manifest.append({'stock_id':f'0x{rid:08x}', 'name':name,'source':source,
                'compiled_nine_patch':source.endswith('.9.png')})
    (out/'manifest.json').write_text(json.dumps({'files':manifest,
        'note':'XML is decoded with local symbolic references. PNGs retain original compiled nine-patch chunks and require proper nine-patch decoding before aapt source compilation. Not yet integrated or runtime tested.'},indent=2))
print('Extracted selector resource closure:',len(done),'resources')
