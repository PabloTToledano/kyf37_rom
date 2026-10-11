"""Validate baseline DT include closure and preparation-script syntax."""
from pathlib import Path
import ast
import re

root = Path(__file__).resolve().parent
for name in ('prepare-kyf37-318.py', 'compare-kernels.py'):
    ast.parse((root / name).read_text(), filename=name)
base = Path('/home/pablo/kyf37-rom/kernel-android10/arch/arm/boot/dts')
pending = [base / 'qcom/msm8909-pm8916-qrd-skut-evt.dts',
           base / 'qcom/msm8909-pm8916-qrd-skut-dvt.dts']
seen = set()
while pending:
    p = pending.pop().resolve()
    if p in seen:
        continue
    assert p.is_file() and p.is_relative_to(base.resolve()), p
    seen.add(p)
    pending.extend(p.parent / name for name in re.findall(
        r'^\s*#include\s+"([^"]+)"', p.read_text(), re.M))
print('Python syntax valid; baseline board include closure:', len(seen), 'files')
