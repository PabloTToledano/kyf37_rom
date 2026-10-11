from pathlib import Path
import shutil
import subprocess

# Run the bootanimation sound integration script to ensure the latest 120-frame
# Kirby bootanimation with Movistar boot sound is integrated.
script = Path('/mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-bootanimation-sound.py')
subprocess.run(['python3', str(script)], check=True)
print('User animation with sound copied into configured TARGET_BOOTANIMATION with charger-only policy preserved')
