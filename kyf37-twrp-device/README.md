# KYF37 physical-key TWRP

Built and flashed TWRP 3.7.0_9-0 from Omni android-5.1 recovery sources (90e5d955), using the original KYF37 kernel and six matching stock MSM8909 MTP device-tree entries. Framebuffer graphics render at 480 x 854. USB ADB runs as root independently of the GUI.

## Controls

- D-pad arrows move the visible cursor. Hold an arrow to repeat.
- Center/Enter presses the selected control.
- Hold Center while moving the D-pad to drag, including confirmation sliders.
- Physical Back returns to the previous screen.
- Open recovery from Android with `adb reboot recovery`.
- Return to Android through TWRP's Reboot > System (or `adb shell twrp reboot system`); this clears recovery boot state.

The keypad advertises ABS events despite having no touchscreen. The input patch ignores its non-key events to prevent false touch releases. The stock kernel supplies keypad codes.

## Installed image

`kyf37-twrp-owner-signed.img`, 16,777,216 bytes.
SHA-256: `9c1f7d5db657bf78f9aae53d0d6bab2f49cb335ecef026451a2c7640ba06da2e`
MD5: `7c564a1e8bac242b14d99a7f2f9b0c5c`

`BoardConfig.mk`, `recovery.fstab`, `kernel`, `dt.img`, and `keypad-and-compatibility.patch` contain the device configuration. Build tree: `/home/pablo/kyf37-twrp` in WSL Ubuntu. Host scripts in `../device-inspection` prepare, build, and sign it.

## Signing and restoration

The bootloader remains locked. A custom public key is installed in the user keystore. Stock boot code is preserved, with its signature changed to the owner's key. Recovery is signed with that same key. Keep `owner-signing-key.pem` private and backed up: future boot and recovery images must use this key while this keystore is installed.

For stock recovery while retaining owner signing, use `stock-recovery-owner-signed.img`. For full original verification state, restore original boot, original recovery, and original keystore together. Original boot/recovery are in `../phone-backup/kyf37-root-backup`, and original keystore is `../phone-backup/keystore-current.img`. Do not restore an original OEM-signed boot by itself while the owner keystore remains active.

The device reapplies temporary eMMC write protection at boot. Existing narrowly scoped helpers clear temporary protection before partition writes; they do not change permanent protection. Installation scripts have exact before/after hash guards and are tied to specific updates, not generic reinstallation tools.

## Validation and backup

Framebuffer screenshots and root ADB verified. Injected Linux key events through the actual matrix keypad input node verified arrows, Center selection, and Back navigation. Physical-button/display confirmation from the owner is still pending.

TWRP backed up Data, Boot, and Recovery in 21 seconds; all three MD5 checks passed. Backup location: `/data/media/0/TWRP/BACKUPS/981108631314/kyf37-first-recovery-backup`. This first backup contains the initial framebuffer recovery before the final keypad synchronization and recovery boot-state fixes. TWRP Data backup excludes internal media (photos/downloads). The earlier full eMMC backup is retained separately. No userdata restore or wipe was performed. MicroSD and restore operations have not been tested; no card is inserted.

Normal Android boot completed after the misc fix. Persistent root returned UID 0, and the final recovery partition MD5 still matched `7c564a1e8bac242b14d99a7f2f9b0c5c` after Android boot.

A separate `kyf37-final-recovery` backup contains the final owner-signed Boot and Recovery images. Backup copies are under `../phone-backup/twrp` on the computer. The phone is left in TWRP.
