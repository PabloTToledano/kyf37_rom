from pathlib import Path
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--tree',default='/home/pablo/kyf37-lineage')
args=parser.parse_args()
p=Path(args.tree)/'hardware/qcom/audio-caf/msm8916/hal/audio_extn/utils.c'
s=p.read_text()
for codec in ['ALAC','APE']:
 old=f'''    case AUDIO_FORMAT_{codec}:
        id = SND_AUDIOCODEC_{codec};
        break;'''
 new=f'''#ifdef SND_AUDIOCODEC_{codec}
{old}
#endif'''
 if new not in s:
  assert s.count(old)==1,codec
  s=s.replace(old,new,1)
p.write_text(s)
print('Absent kernel codec IDs fall through to unsupported-offload result0')
