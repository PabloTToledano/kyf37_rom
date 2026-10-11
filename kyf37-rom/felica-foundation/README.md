# KYF37 FeliCa foundation, offline

The rebuilt kernel has CONFIG_KFELICA=y. The stock kflcd daemon and snfc aliases
are already staged. Actual chip access and service execution are unverified.

Stock libc's identity table identifies kmfc as UID 9000, validated against the
same table's root=0, system=1000, radio=1001 and nfc=1027 entries. Android 10 lacks
this identity and its android.uid.felica shared-user assignment. Original FeliCa
device access depends on that UID; replacing it with Android's NFC UID is incorrect.

Prepared artifacts:

* Three exact stock etc/felica configuration files with recorded hashes.
* Thirteen exact stock device rules with numeric UID/GID values, preserving modes.
* An identity patch for native kmfc=9000, the PackageManager shared user, an explicit
  platform-signed app context, and a build-property gate for the infrared fallback
  Binder so the original FeliCa UART service can own its service name.

The Android identity generator accepts kmfc=9000. Python compilation and staging
checks pass. No kernel/native/framework build or hardware chip test is claimed.
The patch is prepared, not applied: another session is building the shared tree.
No wallet app, chip initialization, persistent provisioning or payment operation
has been enabled. The OEM-service build property remains unset.

Reproduce in WSL using device-inspection/inspect-stock-felica-uids.py,
fix-android10-felica-foundation.py and prepare-felica-identity.py. The latter two
default to staging only. Their --apply option takes a nonblocking shared build
lock and refuses to modify an actively built tree. Apply before a locked rebuild.
The identity script also checks that source files have not changed since staging.

Next required work: compile matched native identity/framework/SELinux changes;
complete daemon, Binder and device labels/permissions; audit original FeliCa
certificate and client/service contracts; activate a minimal validated stack;
then test actual chip communication when phone access is authorized. Payment
provisioning is a separate compatibility question. No standard Android NFC reader
feature is advertised by this work.
