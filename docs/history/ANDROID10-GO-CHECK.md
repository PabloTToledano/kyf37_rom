# KYF37 Android 10 Go offline assessment

Android 10 is a plausible investigation target, not a bootable or verified ROM.
The phone was not accessed, rebooted or flashed during this assessment.

Pinned AOSP reference: android-10.0.0_r47. Downloaded source files and their
SHA-256 values are recorded in android10-reference/provenance.json. This is a
targeted source audit, not a full Android 10 source checkout or build.

Verified in the actual Android 10 references:

- Go product configuration enables ro.config.low_ram, profile-based system
  compilation and an in-process network stack. Inheriting only one property
  would miss other Go configuration.
- libbinder and libhwbinder retain the binder32bit build option. Preserve the
  KYF37's 32-bit protocol across both libraries and the kernel.
- lmkd retains the in-kernel lowmemorykiller interface and falls back from PSI
  monitoring to vmpressure. Lack of PSI alone is not a blocker.
- Bionic's examined seccomp install_filter path uses PR_SET_SECCOMP. This does
  not establish compatibility with every Android 10 sandbox or syscall.
- Stock Kyocera getSoftkeyGuide/getCurrentSoftkeys/setSoftkeys Window APIs are
  absent from the downloaded Android 10 Window.java; the softkey port must not
  depend on those extensions.

The locally built, unflashed kernel-oreo-build/.config has Binder devices
binder,hwbinder,vndbinder; 32-bit Binder; SECCOMP_FILTER; SWAP; ZRAM; and
ANDROID_LOW_MEMORY_KILLER. MEMCG is disabled. Android 10's per-app memory-cgroup
default for low-RAM devices therefore needs explicit configuration or a tested
kernel backport. Kernel compilation previously succeeded; no Android 10 runtime
compatibility follows from that result.

Remaining bring-up work: complete Android 10 product/source configuration;
kernel API audit and matching modules; early boot/init/mount compatibility;
legacy graphics, audio, camera, radio and Bluetooth HAL adaptation; SELinux
policy; storage sizing; and physical-key framework integration. The Android 7
vendor symbol audit cannot be reused as proof of Android 10 binary compatibility.
The presently flashed Android 7 candidate's first boot also remains unverified.

Kyocera port progress: an app-local five-label softkey guide compiles against
both the Android 7 SDK and official API 29 SDK (provenance saved alongside the
references). Merging it into the partially adapted original launcher DEX reduces
unresolved vendor helper methods from 13 to zero after implementing dialog/list
helpers and adapting overflow hiding. The Android 7 method-reference audit passes
all 1,213 references, including checking methods inside owned classes. An unsigned
APK is staged. Modified physical-key policy sources compile separately but have
not been applied to the ROM tree. No Android 10 ROM build, APK install, or physical
key behavior test has passed. OEM provider contracts remain integration work.

The full launcher audit against API 29 public SDK flags nine calls; all nine are
still present in the downloaded Android 10 platform sources. This identifies
hidden or deprecated APIs rather than proving removed methods. Access policy,
platform signing, field compatibility and runtime behavior still need checking.
