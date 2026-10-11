# Kawaii first-boot setup and keypad keyguard

Source implementation: `device-inspection/fix-android10-kawaii-setup-keyguard.py`, applied after the earlier setup/keyguard generators by the locked build wrapper. Source contracts: `device-inspection/verify-kawaii-setup-keyguard.py`.

The native first-boot wizard keeps its provisioning/completion lifecycle and emergency action. Welcome and Finish use a lightweight vector bunny, pink/lavender surfaces and dark readable text. The flow is Welcome → Language → Date/time → Wi-Fi → Appearance → Finish. Appearance offers the existing Pastel Star, Sky Star and Kyocera Classic Home icon themes and saves the choice when advancing. D-pad selects controls, OK activates, Contacts/F1 advances, and Back returns to the previous page. Welcome retains its native emergency navigation button. The existing first-boot state is not reset, and userdata is not cleared to demonstrate the wizard.

SIM PIN: the visual numeric rows are hidden. Their view IDs/listeners remain available to Android’s physical-digit handling. Native SIM validation, retry limits, masked input, subscription handling and emergency/carrier area are preserved. Physical OK submits; Clear deletes a digit and consumes its release so it does not dismiss the bouncer. This does not change device PIN or SIM PUK layouts. The agent never enters a SIM PIN.

Lockscreen: the unlock control is removed from the clock/status layout and placed in the native bottom area, 18dp above its bottom. It is a borderless 12sp hint with a subtle shadow; the notification hint is 10sp. Native authentication and notification opening remain unchanged.

Build: `device-inspection/build-locked.sh /home/pablo/kawaii-setup-keyguard-final-build.log LineageSetupWizard SystemUI`. Changes to SystemUI must be delivered in a matching validated ROM image set; never install this SystemUI in isolation.

Hardware checks pending: first-boot forward/back navigation and theme choice, actual 480×854 layout, owner-entered SIM PIN and Clear, unlock hint with/without notifications and charging indications. Deployment requires the exclusive phone lock. No userdata wipe, provisioning reset, partition writes or reboots are part of this change.

Validation completed: final locked build of `LineageSetupWizard SystemUI` returned `BUILD_EXIT=0`; log saved at `kyf37-rom/kawaii-setup-keyguard-build.log`. Source contract checks passed. A second execution of the patch script left all managed sources byte-identical (`verify-kawaii-setup-idempotence.py`). These are build/source checks, not hardware verification. Nothing has been installed or flashed for this change.
