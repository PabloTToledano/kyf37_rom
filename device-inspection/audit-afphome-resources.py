from pathlib import Path
import json, re, zipfile
from loguru import logger
from androguard.core.axml import AXMLPrinter, ARSCParser
from androguard.core.dex import DEX

logger.remove()
root = Path('kyf37-rom')
with zipfile.ZipFile(root/'stock-framework-res.apk') as z:
    fw = ARSCParser(z.read('resources.arsc'))
with zipfile.ZipFile(root/'android-7-sdk-classes.jar') as z:
    target = ARSCParser(z.read('resources.arsc'))
refs = {}
def add(value, source):
    if value >> 24 != 1:
        return
    refs.setdefault(value, set()).add(source)
with zipfile.ZipFile(root/'AfpHome-stock.apk') as z:
    for name in z.namelist():
        if not name.endswith('.xml'):
            continue
        data = z.read(name)
        if data[:4] != b'\x03\x00\x08\x00':
            continue
        xml = AXMLPrinter(data).get_xml().decode('utf8')
        for match in re.finditer(r'@(?:android:)?([0-9a-fA-F]{8})', xml):
            add(int(match.group(1),16), name)
dex = DEX((root/'AfpHome-partial-port.dex').read_bytes())
for cls in dex.get_classes():
    for method in cls.get_methods():
        if not method.get_code():
            continue
        for ins in method.get_instructions():
            if ins.get_name() not in ('const','const/high16'):
                continue
            for operand in ins.get_operands():
                # Androguard Operand.LITERAL == 1; excludes register operands.
                if int(operand[0]) == 1:
                    add(operand[1], cls.get_name()+'->'+method.get_name())
report = []
for value, sources in sorted(refs.items()):
    stock_name = fw.get_resource_xml_name(value, 'android')
    target_name = target.get_resource_xml_name(value, 'android')
    target_id = None
    if stock_name:
        resource_type, key = stock_name.lstrip('@').split('/',1)
        target_id = target.get_res_id_by_key('android', resource_type, key)
    report.append({'id':f'0x{value:08x}',
                   'stock_name':stock_name,
                   'sdk25_name_at_same_id':target_name,
                   'sdk25_id_for_stock_name':f'0x{target_id:08x}' if target_id else None,
                   'same_id_and_name':bool(stock_name and stock_name==target_name),
                   'sources':sorted(sources)})
(root/'afphome-framework-resource-references.json').write_text(json.dumps({
    'references':report,
    'note':'Compiled XML references and DEX const literals only, compared to SDK25 resources (not final ROM framework). Integer literals can be false positives; XML attribute IDs, resource table, reflection, style inheritance and runtime are not fully covered.'
},indent=2))
print('Framework resource candidates:',len(report))
print('Resolvable against stock framework:',sum(bool(x['stock_name']) for x in report))
for x in report:
    if x['stock_name'] and not x['same_id_and_name']:
        print('Resource mismatch:', x['id'], x['stock_name'], 'target:', x['sdk25_name_at_same_id'])
