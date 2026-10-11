"""Repair copy-list continuations swallowing the next product assignment.

Preserves every copy pair/package. No other agent's generator is rewritten.
"""
from pathlib import Path
import re
root=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37');changed=[]
for p in root.glob('*.mk'):
 original=p.read_text();text=re.sub(r'([ \t]+[^\s:]+:[^\s]+)[ \t]+\\\r?\n(?=[ \t]*PRODUCT_[A-Z_]+[ \t]*[:+?]?=)',r'\1\n',original)
 if text!=original:p.write_text(text);changed.append(p.name)
print('Product continuation repairs:',', '.join(changed) if changed else 'none needed')
