from elftools.elf.elffile import ELFFile
from pathlib import Path
import struct,json
p=Path(__file__).resolve().parent/'audio-primary-live.so'
with p.open('rb') as f:
 e=ELFFile(f);result={}
 for name in ('pcm_config_deep_buffer','pcm_config_low_latency'):
  symbol=e.get_section_by_name('.dynsym').get_symbol_by_name(name)[0]
  address=symbol['st_value'];seg=next(s for s in e.iter_segments() if s['p_type']=='PT_LOAD' and s['p_vaddr']<=address<s['p_vaddr']+s['p_filesz'])
  f.seek(seg['p_offset']+address-seg['p_vaddr']);data=f.read(symbol['st_size'])
  result[name]={'size':len(data),'fields':dict(zip(('channels','rate','period_size','period_count','format','start_threshold','stop_threshold','silence_threshold','avail_min'),struct.unpack('<9I',data)))}
print(json.dumps(result,indent=2))
(Path(__file__).resolve().parent/'stock-pcm-config-audit.json').write_text(json.dumps(result,indent=2))
