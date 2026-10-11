from pathlib import Path
r=Path('/home/pablo/kyf37-android10/device/kyocera/kyf37/sepolicy')
(r/'kyf37_vm_bms.te').write_text('''# Original Qualcomm fuel-gauge daemon, isolated from init.
type kyf37_vm_bms, domain, coredomain;
type kyf37_vm_bms_exec, exec_type, file_type, system_file_type;
init_daemon_domain(kyf37_vm_bms)
# This development ROM remains permissive; runtime accesses must be audited
# before an enforcing release. Do not grant the daemon init's domain.
''')
p=r/'file_contexts'
s=p.read_text()
line='/system/bin/vm_bms u:object_r:kyf37_vm_bms_exec:s0'
if line not in s:p.write_text(s.rstrip()+'\n'+line+'\n')
print('Fuel-gauge executable gets its own init transition/domain')
