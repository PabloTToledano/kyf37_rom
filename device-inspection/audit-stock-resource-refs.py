"""Track original typed resource references while performing normal remapping."""
import re
class TrackedMap(dict):
 def __init__(self,mapping):super().__init__(mapping);self.references=set()
 def __contains__(self,key):
  if key>>24==1:self.references.add(key)
  return super().__contains__(key)
def literals(smali):
 return {int(value,16) for p in smali.rglob('*.smali') for value in re.findall(r'(?<![\w])0x1[0-9a-fA-F]{6}(?![\w])',p.read_text())}
