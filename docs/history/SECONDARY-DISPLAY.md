# KYF37 outer display bring-up

Read-only inspection on stock Android confirms /sys/class/graphics/fb1/name is subdisplay, virtual_size is 128,72 and bits_per_pixel is16. Android dumpsys display exposes only the main480x854 display: the outer panel is not a standard Android logical display.

Model kernel source provides drivers/video/msm/mdss/disp_ext_sub_ctrl.c (SUBDISP_DEVICE_ID subdisplay). Initial ROM uses the original kernel, retaining the kernel-side driver. Userspace is still required: original vendor framework has jp.kyocera.android.subdisplay.SubDisplayService, ISubDisplayService, and framebuffer-info classes; base framework Context/ContextImpl contain custom service registration. Need inspect corresponding system-server service implementation and JNI/hardware dependencies before porting. Do not claim working outer clock/caller/notification behavior yet.

kflcd was inspected and is a FeliCa/NFC daemon, not evidence of outer-screen control; avoid confusing its name with LCD support.

Retaining the driver alone is insufficient. Port the original userspace implementation where compatible, or implement a small outer-display service with clock/battery/caller/notification and lid behavior, then verify on the physical panel after ROM boot.

Reconstructed stock services.odex with SmaliEx successfully and disassembled into /home/pablo/kyf37-rom/services-smali. Actual controller is com.android.server.subdisplay.SubDisplayController, with nativeAttach/Commit/Enable/GetFixInfo/GetVarInfo/MapAshmem/SetDisplayMode/WaitSync. Original presentation/status logic lives in jp.kyocera.server.sublcd, including DeviceStatus and notification/telecom adapters. JNI implementation and system-server integration require porting; cannot copy stock libandroid_servers.so over a newer Android platform library.

Confirmed libandroid_servers.so exports register_android_server_SubDisplayController. The stock sublcd presentation package contains76 smali files. Last authoritative live check still shows ninja PID11244 and resource compilation output. One additional WSL observation command failed with Wsl/Service/0x8007274c; this is an observation failure, not proof either long-running job stopped. Revalidate sessions64789 and84135 before changing running jobs. Host vmmemWSL working set was ~16.8GB; avoid adding concurrent heavy builds until resource state is checked.

Latest build checkpoint supersedes prior handles: session2950 terminated with TLS handshake error35. Inspected JackHttpServer bytecode: it selects SSLv3 SSLContext, incompatible with the current JDK defaults. fix-jack-tls.py changes that constant to TLSv1.2 in source/installed Jack JARs with original backups; certificate validation remains enabled. Stopped only the verified Jack PID23206 and restarted terminal build in session64789. New ninja PID11244 confirmed live, beyond108/20574 incremental actions; authenticated curl to Jack succeeds. Firmware provider audit also exposed stock libsqlite/libxml2 collisions; excluded both in queued generator change, not yet regenerated while live.

Build checkpoint: session23184 terminated at Jack startup race; fix-jack-first-start.py now waits for PEM generation before connection probing as well as treating missing certificates as server-not-running. Incremental build restarted in session2950, log /home/pablo/kyf37-lineage-build.log. Jack server PID23206 was observed live and had generated PEM files/listening ports. Android8.1 source sync session84135/repo PID9070 remains live. Revalidate before restart. No ROM flashed.

Driver interface revalidated for userspace implementation: fb1 supports mmap then FBIOPAN_DISPLAY; nofb_write. mmap validates PAGE_ALIGN(smemstart+smemlen), mapswritecombine. FBIOBLANK accepts onlyFB_BLANK_UNBLANK(0) andFB_BLANK_NORMAL(1); standardPOWERDOWN(4) isrejected. Displaywriter must obtainfix/varinfo, respectstride/yoffset/mappedbounds, preserveexistingcontentduringprobe, useNORMALforoff and avoidcompetingstockservice. Confirmedkernelpathsdisp_ext_sub.c106-139/ctrl57-128. No outerpaneldrawingtestyet.


Implemented initial nativeframebufferwriter navigation/subdisplay/framebuffer.c (notbuilt/integrated/runyet): exact128x72monochromepixels; translatesonbitto0x0010 becausekernelusesmask0x0010shift4; validatesfbid/bpp/stride/xoffset/yoffset/mappedbounds/pixelvalues beforewrite; mmap+PANcommit. Modelkernelconversion readscontiguouspixels ignoringrowpadding, thereforewriterrejectsnon256stride. Caller mustexclusiveownpanel andmanagepower/lidevents; no service/rendering/callnotificationsyet. This ispartialouterdisplayimplementationonly.


Framebufferwriter compiledcleanly onhostandARM EABI5 via build-subdisplay-writer.sh (-Wall-Wextra-Werror). Added allocationfree128x72clock/batteryrenderer render.c with validatedtime/percent inputs, 24hourclock, batteryicon/numericpercent. Hostcompilepassed. NeithercomponentintegratedasROMserviceorphysicalpaneltested; lid/notification/call/powerbehaviorstillrequired. Current70304verifiedlive18869at94%/3095of3280tasks.


Added initialJNIcontroller+libkyf37subdisplay Android.mk forfutureOuterScreenService: serializedupdates, fixedfb1path, clockrender, UNBLANKonlywhenbecomingvisible, NORMALoffandclosewhenhidden, errno propagation. Sourceonlynotintegrated/builtyet. Revalidateddriverrelease is NO-OP (earlierconcernaboutreleasepoweroffisnottrue); explicitNORMALneeded. Open powerspanelonlyifPWR_OFF. NextJava service/policylidnotification,compileandphysicallidteststillrequired.


Added initial platform-signedsystemUID Kyf37OuterScreen service/boot+alarmreceiver andJNIpackaging: clock+batteryrefresh, exactminutealarmswhileclosed, timeoutboundedwakelock, cancelwhenopen, signaturepermissiononlidreceiver. Reads sys.kyf37.lid_open defaulttrue; policypublication/broadcastnotyetwired. Service/sourceonlyuncompiledunintegrated; incomingcall/notificationdisplaynotimplemented. Batteryinitial0untilstickybatteryevent; nativewritesmainthreadserialized. MinutealarmbatterycostandDozebehaviorneedphysicalevaluation. Current70304stilllive18869at98%/3215tasks.


Rendererpreviewcompiled/executedwithinputrejectionandbufferendcanarychecks; generatedouter-screen-preview.png128x72 andvisuallyinspected14:37+72%battery. Hostchecks pass; physicalcontrast/polaritynotverified. Queuedcontrollerrestartfix inhostsource: hiddenupdateopens+validatespanelthenNORMALblank, so newlyrestartedprocesscanblankpanelleftonbypredecessor. Notcopiedtolivebuild8001yet; mustreintegrateafterterminal. AlarmsetExactcanbedelayedinDoze; minuteaccuracy/batterydrawneedruntimevalidationandpolicydecision.


Current8001 live26729at32%/510of1573; libkyf37subdisplay.so built13932B, JavaAPKnotyetbuilt. ReviewedSELinux: sys. propertymapsystem_prop alreadywritablebysystem_server; system_appdoesnotgetgraphicschraccess. Queueddedicatedkyf37_outer_screenappdomain selectedbyseappname+platform+systemUID, exactfb1customdevicelabel andrwchrpermission/searchgraphicsdir/getsystemprops. Notregeneratedduringlivebuild; policycompileandseapp/filecontextresolutionneedverificationbeforeflash. AvoidgrantingallSystemUIDapps framebufferaccess.


ValidatedcustomsystemUIDdomain againstactualAndroid7 seappneverallows: rules forbidnon-systemUID using system_app/system_app_data_file; customdomainforuser=systemisallowed. app_domain onlygrantsgenericapp_data_fileaccess, soqueuedexplicit system_app_data_filedir/file/lnkperms forouterdomain. Noextendedgraphicspermissionsoutsidefb1. Build8001verifiedlive26729at36%/570of1541tasks; WSL92954servicefailurewasobservationtimeoutonly.


Build99923 live26093at26%/420tasks. Compiledrootsepolicycontainskyf37_outer_screeninappdomain; compiledseapp_contextsselectsexactsystem/platform/package domain. verify-panel-context.c linkedagainstAndroidhostlibselinux/pcre andusedactualbinaryfile_contexts: fb0graphics_device, fb1kyf37_subdisplay_device correct (tooloutputverificationrequired). Policycompile/labelsnotproofruntimepermissionsorouterpanelbehavior. NoROMflash.


AuthoritativeAPKinspectionfoundpriorouterAPKclasses.dex140B EMPTY; servicesourcemanifestandJNIbuiltbutJavaimplementationabsent. classes.jackalsoonlymetafiles despitejava-source-listbothfiles. Thiscontradictsfunctionalservicepackagingclaim; priorbuildsuccessonlyprovedcontainer/nativebuild. QueuedLOCAL_PROGUARD_ENABLEDdisabled plusverify-outer-apk.py checksactualservice/receiverclassesandnative(ZIII)I. NeeddiagnoseJack/rulesandrerunafter99923terminal; noflashperformed.


ExactninjaJackcommanddiagnosesemptyDEX: --config-proguardclasses.dex.flags usesbuild/core/proguard.flags butnoaaptgeneratedmanifestkeepfile; resource-freeappcompiledwithshrinkingandmanifestcomponentsremoved. Disablingshrinkingfor2-classouterservice isthereforeevidence-backedfix, notjustguess. QueuedLOCAL_PROGUARD_ENABLEDdisabledunchanged;99923live26093at75%/965of1279tasks. WaitterminalthenreintegrateandrebuildactualAPKverifier.

