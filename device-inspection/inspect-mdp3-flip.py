from pathlib import Path
p=Path('/home/pablo/kyf37-rom/kernel-android10/drivers/video/msm/mdss/mdp3_ctrl.c');s=p.read_text()
for needle in ['static void mdp3_ctrl_pan_display(', 'static int mdp3_ctrl_display_commit','dma->update','mdp3_ctrl_overlay_play']:
 a=s.find(needle,s.find(needle)+1) if needle=='static void mdp3_ctrl_pan_display(' else s.find(needle)
 print('\nMATCH',needle);print(s[a:a+3200])
