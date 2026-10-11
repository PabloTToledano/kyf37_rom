# Vendor ABI bring-up

Initial build64789 terminated at97%/19846 actions with CAF audio_extn/utils.c referencing SND_AUDIOCODEC_ALAC and SND_AUDIOCODEC_APE absent from actual stock kernel UAPI. fix-audio-codec-header-compat.py guards those codec cases on the actual header definitions, retaining unsupported result0/default logging rather than fabricating codec IDs. Confirm offload advertisement/software fallback behavior before runtime claims. After authoritative terminal check, regenerated initial device/vendor tree with230 latest files, Bluetooth/SQLite/XML exclusions, vendor controller candidates, codec correction, color property and selector overlay. Restarted incremental build in session83312, same log. Initial prior session64789 is terminal; new live handle must be checked. Kernel50037 still running at last observation (>1138 objects), no complete zImage yet.

Static codec correction completed: patch-ittiam-mapper.py locates only ELF32 ARM .dynstr, retargets GraphicBufferMapper::lock int usage mangling to uint32_t usage, asserts exactly one changed byte and verifies new/absent old dynamic import with readelf. Both Android7/8 headers expose the same target signature; ARM32 bitmask width and other arguments unchanged. Original stock library remains untouched; candidate saved patched-vendor/libOmxIttiamVdec.so with original/patched hashes and offset provenance. Generator validates both hashes before copying candidate. Codec/buffer runtime ABI is still unverified.

Native root inventory now175 files, zero missing stock dependencies, includes dynamically loaded libbt-vendor.so/libbtnv.so. Controller vendor library depends only on btnv and C/cutils/log/m/stdC runtime, while newer Android supplies Bluetooth framework/default stack. Actual vendor callback interface still needs testing; no pairing claim.

audit-vendor-symbols.py inspects DT_NEEDED closure and strong dynamic symbol names in stock candidate ELFs against current initial Android7 build providers. It prefers actual linked modern platform libraries over installed/stale stock copies. First audit covers162 ELF files. Many missing providers are not installed until final image assembly; do not treat all unresolved symbols as real incompatibility before provider closure is present. Symbol versions, loader namespaces/caller globals, dynamic loading, layouts and ioctl contracts remain outside this check.

Confirmed mismatch with complete available provider closure: original lib/hw/bluetooth.default.so imports old android::AudioTrack constructor no longer exported by target libmedia. Android Bluetooth stack must match its Java/framework version; generator now excludes old default Bluetooth library, leaving target-built stack. Separate vendor controller interface is dynamically loaded libbt-vendor.so; expanded native inventory roots to retain original controller integration dependency candidates. Vendor callback/API compatibility and hardware pairing still require review/testing. Generator update queued for live initial build; don't mutate/restart it while running.

Additional complete-closure mismatch: vendor/lib/libOmxIttiamVdec.so imports GraphicBufferMapper::lock(native_handle const*, int, Rect const&,void**), absent from target. Need verify target replacement signature and compatible shim or modern codec provider. Old libsqlite/libxml2 depend on ICU53 symbols; already queued exclusions retain target platform replacements. Other graphics/camera/audio/modem ABI findings remain pending after dependency closure completion.

Current checkpoints: initial ROM build64789/ninja11244 remains live beyond80% (16432/20458). Kernel full build50037 remains live,336 compiled objects observed, no zImage yet; do not infer success from Binder object compilation. No ROM or updated kernel flashed.

Actual ninja query showed system/lib/libOmxVenc.so depended on BOTH stock copy and rebuilt encoder: copy recipe overrides source install but source prerequisites remain. select-stock-video-codecs.py gates msm8916 mm-video-v4l2 source definitions only when KYF37_USE_STOCK_VIDEO_CODECS=true (set by device generator), preserving stock Venc/Vdec already in product. Stagefright plugin remains modern. Stock codec symbol and runtime compatibility remain required; this is provider conflict removal, not proof codecs work. Build session47133 restarted after62706 terminal failure. Future build output now captured by tee with pipefail in kyf37-lineage-build.log.


Provider audit now uses staged proprietary payload (including Ittiam patch), honors explicit product-copy providers over LINKED modules, and indexes EGL dependency libraries. Added stock libstlport.so omitted by platform-name filtering but absent Android7 platform; only DT_NEEDED libc/libm/libstdc++. Stock rmnet selected with scoped source guard because source controls CKSUMV3/V4 are absent model kernel and existing copy rule already installs stock librmnetctl.so. Build47133 terminal exit1; restarted55725. Remaining Adreno RSA_verify_PKCS1_PSS and FileMux androidGetTid ABI gaps need real compatibility implementations, not stub success.


Prepared restore-rsa-pss-compat.py, not applied during live build55725. Original OpenSSL legacy RSA_verify_PKCS1_PSS delegates to mgf1 verifier with NULL MGF digest (https://raw.githubusercontent.com/openssl/openssl/OpenSSL_1_0_2-stable/crypto/rsa/rsa_pss.c). Local BoringSSL mgf1 explicitly uses message digest when NULL. Proposed wrapper preserves real validation; requires compilation/export check and valid/invalid signature tests before use. WSL observation53312 recovered and confirmed live ninja31272; earlier70823 failure was WSL service timeout, not build terminal. Build reached43% incremental output.


Prepared isolated ARM rsa-pss-compat-test.c and build-rsa-pss-test.sh: generates ephemeral RSA2048 key and PSS encoding, requires valid acceptance and wrong digest/salt/corrupted trailer rejection against actual target libcrypto. No key exported. Cross-build submitted session46175 still pending WSL; no test result yet. FullROM55725 latest verified live ninja31272 at47%/904 actions. Wrapper still unapplied pending build terminal; stockphone unchanged.


On-phone ARM PSS delegation test PASSED against actual Android7 target libcrypto in isolated /data/local/tmp/kyf37-crypto-test: valid=1 wrong_digest=0 wrong_salt=0 corrupted=0, result0. Initial Android7 crtbegin failed on stock5.1 __register_atfork; rebuilt only test startup with NDK API21 crtbegin/crtend. Probe key ephemeral, no partition modification. Tests wrapper compiled into probe; pending restore script must still be applied between builds and export validated in rebuilt libcrypto. This does not prove Adreno runtime/whole-ROM compatibility.


Updated staged-provider audit now162ELFs: legacy STL+EGL dependency closure resolved. Seven remaining affected files: qcom-system-daemon/RIL missing modern libxml2 (shared module exists but not requested), hwcomposer eglGpuPerfHintQCOM, Adreno RSA wrapper, FileMux androidGetTid. Queued PRODUCT_PACKAGES libxml2 in generator; not regenerated during live55725. Live build reached86%/1599 actions. androidGetTid export confirmed in original libutils, requiring exact compatibility forwarding review.


Prepared restore-thread-id-compat.py (unapplied during live55725) restoring C androidGetTid in libutils as pid_t forwarding gettid. Original stock function four-byte tail branch; stock libc gettid jump-slot confirmed, official historical implementation https://raw.githubusercontent.com/aosp-mirror/platform_system_core/android-4.4.4_r1/libutils/Threads.cpp documents same Linux behavior. Need rebuilt export and thread-specific runtime test. Current fullbuild still live31272 at88%/1641 actions.


Prepared restore-egl-perfhint-compat.py, unapplied while full buildlive. StocklibEGL eglGpuPerfHintQCOM disassembly validates display/context and forwards implementation handles; stockAdreno exports actual function. Proposed modern wrapper validates/refholds model context, obtains raw extension from driver connection (not GL extension trampoline), translates display/context and returns driver result. Missingextension returnsfalse, not fabricatedsuccess. Still requirescompile/exportandactualEGL/HWCtest. Build55725 reached92%/1708actions.


Build49961 terminalfailed solely observed EGL constpointer mismatch; libutils androidGetTid GLOBAL PROTECTED export alreadyconfirmed. Corrected wrapper connectionpointerconst in idempotent script and actualtree, restarted70304. RSA export was stilloldprovider atcheck; needsrecheckafterrelink.


Current70304 live18869 at5%/214 of3729tasks; rebuiltlibEGL eglGpuPerfHintQCOM GLOBAL DEFAULT exportconfirmed. Audit162ELFs now reports onlymodernlibxml2missing forqcom-system-daemon/RIL; stillinflightbuild. Prepared --exported PSS testmode removingtestlocalwrapper andrequiringactualrebuiltlibcryptoexport. WSLobservation44519/7445pending; don'trestartbuildonobservationtimeout.


Actual rebuiltlibcrypto now exports RSA_verify_PKCS1_PSS GLOBALDEFAULT (22-byteARMfunction). Direct exportedfunction testonphonePASSED valid1/wrongdigest0/wrongsalt0/corrupted0/exit0. Probe containsno localwrapperinexportmode; linksactualrebuiltlibcrypto. rsa-export-runtime-verification.json recordspayloadhashesandscopelimits. NoROMflash.70304 latestlive18869.


Updated nativeaudit39025 completed: Checked162vendorELFfiles withzero missing DT_NEEDED providers andzero unresolved strongsymbols against currentstaged/linkedproviders, includingmodernlibxml2. This remains symbol-name/closurecheckonly: no ELFversion/globalnamespace, structure/ioctlABI, dlopenorhardwarecoverage. Currentbuild70304 live18869 reached72%/2561 of3535remainingactions. Build constructsrecovery-from-bootpatch; mustdisableautomaticrecoveryreplacement beforefinalflash to preserveowner-signedkeypadTWRP.

