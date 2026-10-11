# KYF37 newer Android ROM work

Goal: build a newer Android ROM, preserve stock flipphone apps where porting works, otherwise implement full physical-key navigation. Print the actual ROM/change summary before flashing. No custom ROM has been flashed.

Verified hardware: MSM8909 ARM32 Cortex-A7, approximately 1 GB physical RAM (909484 kB visible), stock Linux 3.10.49, 480x854 non-touch display. System partition 1612709888 bytes; userdata 4432330752 bytes. TWRP and owner-signing route verified independently.

Initial target: Android 7.1.2 / LineageOS 14.1, with the KYF37 stock kernel and own drivers. A related MSM8909 UL40 source tree boots Lineage 14 with stock kernel but lacks many hardware functions; reference only, not a drop-in ROM. Target version may change if evidence supports it. The stock Android 5.1.1 HAL/API gap and vendor framework compatibility remain unproven.

Extracted authoritative stock system image to WSL /home/pablo/kyf37-rom/stock-system using debugfs. Inventories here cover 161 APKs and 73 framework JARs. 159 APKs lack embedded classes.dex and depend on optimized ODEX code. Need deoptimization against the original boot classpath and dependency audit, then runtime compatibility validation; APK copying is insufficient.

Reference source cloned to /home/pablo/kyf37-rom/reference/ul40. Android source checkout /home/pablo/kyf37-lineage uses LineageOS/android cm-14.1. Repo sync launched in exec session 30459; inspect its actual process/session before any restart. Log /home/pablo/kyf37-rom-source-sync.log. Chromium WebView checkout errors already reported while other downloads continue; resolve after the process terminates. Do not assume the sync completed.

Required implementation/verification: own device and vendor trees; compatible graphics/audio/radio/Wi-Fi/camera drivers; flip state and power behavior; key layout; keypad text entry; D-pad/center/back and softkey navigation across system and apps; original app port/dependency audit with fallback navigation for incompatible apps; system/boot images within real partitions; owner-signed boot; recoverable installer; full pre-flash summary; boot and hardware/user interaction validation. Preserve user data and working recovery throughout. Completion remains unproven.

Next: deoptimize AfpHome and stock framework/flipphone apps; derive vendor dependency closure from original ELF files and init configuration; inspect and resolve source-sync errors; create KYF37-specific device configuration and navigation source. Do not reuse UL40 partition maps, modem configuration, or bootloader files.

## Further progress

157 stock app ODEX files have been converted using SmaliEx oat2dex against original ART 045 boot classes; every tool invocation succeeded without stderr. Tool success is not runtime compatibility proof. AfpHome code disassembled and references recorded in afphome-api-references.txt. External vendor APIs include KCfpSoftkeyGuide, KCfpDialogUtil, KCfpWidgetUtil, KCfpSharedResources and jp.kyocera.internal.clomask.Transfer; these require investigation/porting.

Native inventory covers 1134 ELF objects. A 105-file candidate dependency closure for hardware HALs, graphics and selected Qualcomm daemons has no missing stock libraries, but its Android platform ABI dependencies must be checked against the target version. File stock-native-dependencies.json is an inventory, not a working vendor tree.

Implemented initial framework cursor extension navigation/Kyf37Navigation.java and physical multi-tap IME under navigation/ime. IME javac against Android API22 completed with only a bootstrap warning. Framework cursor is not yet compiled/integrated or runtime tested. Integration script device-inspection/integrate-kyf37-navigation.py is staged and must run after source synchronization is terminal. F4 toggles cursor; arrows move; Center click/hold drag; reset hooks cancel on sleep/lid closure. Text entry supports abc/ABC/numeric, composing text and Menu delete. Full fallback launcher and default IME setup remain needed.

User asked why not Android Go. Evaluating Android 8.1 with official AOSP Go defaults (saved android-8.1-go-defaults-reference.mk), which fits RAM better. Do not treat Go as a hardware compatibility solution or infer certification/Google apps availability. Final Android version is not fixed. Current 7.1.2 download continues as compatibility reference and initial bring-up option; do not cancel/reinitialize live sync merely due to version evaluation.

Source repo sync session30459 confirmed still live and downloading (checkout grew beyond 8.6GB); Chromium WebView checkout failures need resolving once terminal. App conversion session84251 completed; remaining vendor apps converted by subsequent completed command. No ROM flashed. Pre-flash summary gate remains pending.

## Build bring-up progress

The original source sync session30459 terminated with four WebView checkout errors. Diagnosed missing git-lfs, installed it in WSL using apt, and successfully completed local checkout of all four WebView projects; arm git-lfs pull succeeded. No source sync currently running.

Integrated navigation using integrate-kyf37-navigation.py into frameworks/base/services/core/java/com/android/server/policy and packages/inputmethods/Kyf37KeypadIME. Hooks are guarded by ro.kyf37.keypad_navigation and cancel cursor drag on sleep/lid closure. Not yet compiled in a ROM.

Created device/kyocera/kyf37 and candidate vendor/kyocera/kyf37 trees via prepare-kyf37-lineage.py. Host copy is kyf37-rom/device. Uses own prebuilt kernel + pruned stock DT, real partition geometry, original boot animation, stock model keylayout with F3 mapped HOME, original vendor ramdisk RC/scripts (excluding stock generic init/env/USB/ueventd files and boot classpath), stock fstab with unsupported vendor-only flag removed. Userdata is currently unencrypted and the proposed fstab does not force encryption. Reuses 102 candidate original native/config files; inclusion and ABI audit remain unfinished. Conflicts with AOSP libtinyalsa/libtinycompress/libspeexresampler and other generic libraries must be resolved before flashing. Many stock daemons/firmware/media properties may still be missing. Do not call this vendor tree complete.

Product lunch lineage_kyf37-userdebug succeeds and identifies Android7.1.2. Initial host compilation needed legacy ncurses/tinfo5; official Ubuntu packages extracted privately to /home/pablo/kyf37-host-tools/legacy-libs with LD_LIBRARY_PATH in build-kyf37-lineage.sh. Used command make to bypass envsetup make wrapper argument splitting. Full build stops at missing out/target/product/kyf37/obj/KERNEL_OBJ/usr dependency for Qualcomm Bluetooth vendor headers. Build session73192 is terminal; log /home/pablo/kyf37-lineage-build.log. Kernel headers need a reproducible generation rule without silently replacing the verified stock kernel.

Started shallow clone of kernel source KYF37 branch57a11bec679273e797cbf3fcb3fc1488637b3fe6 into /home/pablo/kyf37-rom/kernel-source in exec session60528; log /home/pablo/kyf37-rom/kernel-source-clone.log. Model source is firmware105.0.2700 whereas phone104.0.2600: headers must be reviewed for ioctl ABI compatibility. Keep prebuilt boot kernel unchanged for initial bring-up. Before restarting clone/build, inspect terminal/live handles.

Previous goal turn is progress: reconstructed source files, repaired source checkout and launched real product build, whose specific missing headers determine next work. No ROM image has passed a complete build; no ROM flashed. Android8.1 Go remains evaluated but not downloaded/built. Need actual hardware/API compatibility evidence before final version decision and pre-flash summary.

## Header/build and runtime progress

Kernel source clone session60528 completed successfully at branch KYF37. build-kyf37-lineage.sh now generates ARM UAPI headers with headers_install into out/target/product/kyf37/obj/KERNEL_OBJ/usr, using a separate header build directory; the verified prebuilt kernel is unchanged. Header generation and missing-header dependency are resolved.

Build session18028 stopped at host aidl missing std::bad_typeid/bad_cast symbols. Diagnosed replacement of same-named typeinfo.o archive members: HOST_GLOBAL_ARFLAGS=crsD discarded paths and replaced libc++abi definitions when assembling libc++_static. Corrected to crsPD, patched host archive extraction to mkdir member parent paths and ar pP, and invalidated nine generated host archives using fix-lineage-host-archives.py. Avoid rerunning invalidation without a new reason. New build is exec session6005, log /home/pablo/kyf37-lineage-build.log; last confirmed running beyond 5% (1921/32616 actions), past aidl. Inspect live handle and latest log before restart.

New fallback Home source under navigation/home compiles and was installed on stock Android with IME test APKs. Launched org.kyf37.home/.Home, D-pad down and Center opened the Alarm app; screenshot home-stock-test.png proves rendering. Original stock launcher remains default. No ROM flashed. Current ROM build does NOT yet include Kyf37Home: integrate-kyf37-navigation.py and prepare-kyf37-lineage.py were updated to copy/package it for NEXT build after the current build is terminal. Do not restart live build just for this change.

IME installed and temporarily enabled/default-selected on stock Android for a separate transient input-probe app. Keys 2,2,pause,3 produced bd in EditText. Mode-switch/uppercase/delete/numeric/delete sequence returned the expected bd. UI hierarchy logs ime-runtime-test.txt and ime-modes-test.txt cover results. Original input method jp.co.omronsoft.iwnnime.ml/.standardcommon.IWnnLanguageSwitcher restored and verified; custom IME disabled, probe uninstalled. Home/IME test APKs remain installed but do not replace default launcher/input. Build sources use platform signing later; separate test APKs currently use AOSP testkey. Framework cursor extension is still untested until its system-server build and ROM boot.

The phone was rebooted from TWRP to stock Android for these reversible app tests and is currently on stock Android. Data and recovery not flashed/changed. Need finish build, add fallback home to product, continue stock app API porting and vendor ABI/ramdisk completeness audit, evaluate Android8.1 Go, prepare summary before any ROM flash, then actual boot/hardware tests.

## Native startup and launcher API audit

Current build session6005 was verified live at ninja PIDs9222/9223, beyond20% (6581/32616 actions), no newer failure observed. Do not restart while live. First build remains without fallback Home; stage integration and regenerate device/vendor tree only after terminal before the next incremental build.

Added audit-rom-init-services.py and stock-init-service-audit.json. It identifies missing candidate service executables, including model display/power, remote modem storage, thermal, audio, and camera daemons. Generic AOSP service replacements must be distinguished from vendor requirements; do not blindly copy all 217 stock service declarations. Expanded inventory-native-rom.py roots for essential hardware daemons, dynamically loaded Qualcomm RIL libraries and OMX codecs: candidate native closure now173 files, no missing stock dependencies. prepare-kyf37-lineage.py has not yet been rerun after this expansion: actual current build still uses prior102-file vendor candidate set. ABI conflicts/platform replacements and required firmware/config/module files remain unresolved.

Compiled Android7 framework classes.jar is available and copied here. Static AfpHome method-reference audit (audit-afphome-api.py) resolves inherited Java/XML interfaces with target SDK25 stubs: of1175 Android framework references, one stock-specific method absent, android.provider.Settings$SilentModeSettings.getSilentMode(Context). Fifteen external vendor helper references remain. Audit limitations exclude reflection/dynamic/native dependencies and resource compatibility.

Stock framework-classes2.dex contains jp.kyocera.kcfp helpers. Disassembled under /home/pablo/kyf37-rom/vendor-framework-smali. KCfpSoftkeyGuide calls modified Window.getSoftkeyGuide/getCurrentSoftkeys/getAttributSoftkeys, so copying the helper bytecode alone is insufficient. More Android Window/widget integration or a faithful helper replacement is required. SilentModeSettings is in framework.dex; decompiled getter reads Global silent_mode_type and returns null for null Context.

port-afphome-silentmode.py produces isolated source /home/pablo/kyf37-rom/afphome-port-smali from original disassembly, replacing the one getter invocation with an app-local org.kyf37.compat.SilentModeSettings that preserves that exact lookup/null behavior. Assembled successfully with SmaliEx into AfpHome-partial-port.dex (782732 bytes). Re-audit afphome-partial-port-api.json shows zero missing directly referenced Android methods and the same15 vendor dependencies. This is a partial port only; not packaged/installed or claimed functional. Need ROM updates of silent_mode_type for meaningful state, helper/resource compatibility, signing and runtime tests.

No custom ROM flashed. Original stock Android remains active; full objective and pre-flash summary remain incomplete.

## Native provider conflict resolution staging

Current build6005 still live, confirmed beyond22% (7462/32616). Do not restart solely to incorporate queued changes. audit-native-provider-conflicts.py identified35 install-path collisions and saved native-provider-conflicts.json. Updated prepare-kyf37-lineage.py to exclude stock5.1 platform daemons/runtimes (rild, wcnss_service, Android software GLES, Skia, audioutils/tinyalsa, common_time, keystore binder, RIL etc) from the next vendor copy list. Actual current build still has old copied providers; its images must not be flashed as final. Re-run generator after current terminal before incremental build to incorporate expanded173-file driver closure, provider exclusions and fallback Home. Some Qualcomm shared libs such as overlay/memalloc/qd* require deliberate provider and handle-ABI selection; current audit labels HAL/provider decisions incomplete. Missing firmware/modules/config and stock service completeness remain required.

No flash performed, goal active. Next independent work: runtime/link symbol audit against generated target libraries, exact resource/helper port feasibility, fallback input setup and phone hardware validation after complete build and pre-flash summary.

## Android 8.1 evaluation and hardware links

Build6005 remains live beyond38% (12583/32616), confirmed ninja PID9223. The reported support-library Java errors occur in cm-api-stubs droiddoc generation; org.cyanogenmod.platform itself compiled and produced classes.jar. Do not diagnose this as a failed runtime library or restart the live build solely for documentation output. Final terminal status remains required.

hardware-support-files.json inventories80 regular files (~6.1MB), five symlinks and six referenced but absent modules. prepare-kyf37-lineage.py now stages regular support files and generates device Android.mk image dependencies for all five symlinks, preserving Wi-Fi links to /data and /persist plus lib/modules/wlan.ko -> /system/lib/modules/pronto/pronto_wlan.ko. Generator remains queued until the current build finishes. Python syntax checks passed; resulting system-image symlinks still require verification after regeneration/build.

integrate-kyf37-navigation.py now also resets a held cursor drag on setCurrentUserLw, matching its stated user-switch behavior. Queued for the next integration, not yet compiled or runtime-tested.

Started separate Lineage15.1/Android8.1 source checkout under /home/pablo/kyf37-oreo using sync-kyf37-oreo.sh. First init session70187 failed due borrowed shallow manifest history; removed the reference option and restarted only after confirmed terminal. Current session84135, log /home/pablo/kyf37-oreo-sync.log. Verify live/terminal before restarting. This is candidate source acquisition, not a Go ROM build or proof of hardware compatibility. KYF37 kernel source defconfig enables SECCOMP_FILTER; TSYNC support and actual running-kernel config remain unverified. No ROM flashed; stock apps and hardware compatibility work remain incomplete.

Subsequent authoritative check: build6005 TERMINATED at12694/32616, Jack server setup failure. Missing first-launch PEM files make modern curl return2; jack-admin isServerRunning wrongly retries then aborts before launching the server which generates them. fix-jack-first-start.py adds an absent-certificate return1 (server not started); no TLS verification bypass. Re-ran integrate-kyf37-navigation.py and prepare-kyf37-lineage.py only after terminal: current source now includes Home, user-switch reset, expanded vendor closure/platform exclusions and five symlink rules, with231 regular stock file entries. New incremental build session23184, same build log. Final runtime/ABI verification still required. Oreo sync84135 initialized successfully and repo sync PID9070 confirmed live; keep polling exact handle/state before any restart.

Verified existing built system/framework/services.jar classes.dex (artifactmtime00:14; not yet currentfinalsystemimage) includes Kyf37Navigation and calls from allfive PhoneWindowManager hooks: init, interceptKeyBeforeDispatching, finishedGoingToSleep, notifyLidSwitchChanged, setCurrentUserLw. navigation-dex-verification.json records actualinstructions. services.core is staticJavajar, so noindividualclasses.dex there; verified combinedservicesJARinstead. This proves compiledintegrationonly; runtimecursor/physicalkeybehavioronnewROMstillpending. Latest55725 live31272at93%/1733; sourcecompatpatchesstillqueueduntilterminal.


Queued keypadIME android:isDefault boolresource true in hostnavigation sources. Model keyboard was installedprivileged but lacked defaultenabledIME declaration; actual InputMethodUtils consults InputMethodInfo.isDefault for defaultselection. This ensures eligibility, not proof of exclusive/defaultselectiononexistinguserdata; verify secureIMEsettings and actualkeyentryafterboot. Not copied into livebuild yet. 55725 latest live31272at97%/1798tasks, no systemimage yet.


Prepared standalone sign-rom-boot.py: existing enrolled ownerkey/publickey/keystore consistencychecks; fixed /boot target; preserves alignedbootbody; verifies RSA signature; output16MiB; refuses existingoutput andinputoverwrite. No keygeneration/keystoremutation. Syntaxcheckpassed; signer notyetexecuted oncandidate; actualphonekeystore and bootruntimeverificationstillrequired. Incremental49961 live4941recompiling5222tasks followingcryptoheaderchange.


Standalone ROM signer regressioncheck on originalOEMstockboot PASSED: signing-test-stock-boot.img SHA256466fd5ead33dabb54446ecf2f2132edc821e8d7da0c2f5d9f61fb08c45bcc3ed exactlymatches knownworkingboot-owner-signed.img. Proves signerreproducesestablishedsignatureandlayout forstockbody; doesnotprove customROMbootability. No flashperformed.


Recoverypreservation: currentbuildinit has startflash_recovery commented and noinstall-recovery.sh/recovery-from-boot.p found, but generatedetc/recovery-resource.dat exists. Queued TARGET_NO_RECOVERYtrue in generator to suppressrecoveryimage/patchconstruction. Prepared remove-generated-recovery-payload.py checksdeviceflagandnoactivebuild then deletesonlyfourexactgeneratedfileswithresolvedpathbounds. Unexecutedwhile70304live18869at78%/2662tasks. Mustrebuild/inspectfinalimageabsence beforeflash.


Build70304 terminalSUCCESSexit0, systemimage~568MBsparse/1612709888logical. Thenintegratedinitialsubdisplayserviceandpolicybootlidpublication+explicitstartonchanges, generatedproductwithouter_screenflag/packageandTARGET_NO_RECOVERYtrue. Exactgeneratedrecoverycleanup removedetc/recovery-resource.dat; workingTWRPpartitionuntouched. Rebuildstartednexttoolsession. Initialouterserviceclock/batteryonly, physicaltestnotdone, calls/notificationsstillpending. Firmware/appportobjectiveunfinished.


Build8001 terminalSUCCESSexit0: integratedinitialouterAPK/nativeJNI/lidpolicy, system~564MBsparse1612709888logicalwithno recoverypatchdependency. Queuedrestartfixanddedicatedsepolicythenappliedviaintegrate+generatorafterterminal; newbuild99923. Note datechangegenerated20261007versioncanincreaseincrementalJavaactions. Noflashperformed; finalimage/runtime/appportsremainunverified.

