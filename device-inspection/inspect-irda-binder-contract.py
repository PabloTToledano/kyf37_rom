from pathlib import Path
p=Path('/home/pablo/kyf37-rom/vendor-framework-smali/jp/kyocera/felicaservice/IFeliCaServiceUartExclusion$Stub.smali')
s=p.read_text();print('\n'.join(x for x in s.splitlines() if 'TRANSACTION_' in x or 'DESCRIPTOR' in x))
