from pathlib import Path
p=Path('/home/pablo/kyf37-lineage/hardware/qcom/display-caf/msm8916/libhdmi/hdmi.cpp')
s=p.read_text()
line='    EDIDData(HDMI_EVFRMT_4096x2160p24_16_9, 4096, 2160, 24, 35),'
guard='#ifdef HDMI_EVFRMT_4096x2160p24_16_9\n'+line+'\n#endif'
if guard not in s:
    assert s.count(line)==1
    p.write_text(s.replace(line,guard))
print('HDMI mode table excludes the unsupported kernel mode when absent.')
