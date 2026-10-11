# AfpHome framework resource compatibility

Actual compiled Android7 framework-res package-export.apk copied to android-7-framework-res-built.apk and checked by named ARSC lookup: none of the35 shared-resource names exist there either. This strengthens the SDK-baseline finding; original labels/icons/colors must be staged as source resources and compiled into framework overlay. Current existing selector overlay only covers its five-resource focus-highlight closure. No complete SharedResources support claim.

Shared helper integration: port-afphome-shared-resources.py moves the original KCfpSharedResources implementation app-locally, redirects all app references and saves35 original name/type aliases. It retains null/type/error/lookup semantics and HashMap initialization, not a stub. Partial DEX assembled successfully; audit1177 Android calls, zero missing,13 remaining external Kyocera methods. Alias audit resolves all35 against stock ARSC and inventories original locale/configuration data. All35 absent by named lookup in SDK25 baseline, but compare against actual final framework-res before concluding stock-platform names are missing. Requires porting appropriate resource closure/content; no functioning launcher claim.

Additional partial port: TransferAccessor is called only for MainMenuLayout.getColorId key rw_proximitysensor_colorvariation. Read stock Binder transaction transfer1 with that key: Parcel00000000/00000001/00000033 => string3. Saved stock-color-variant.json. port-afphome-variant.py redirects the app's single Transfer.get reference to app-local VariantSettings, which returns the captured ro.kyf37.color_variation property for that exact key; unknown/missing values throw IOException and retain existing app error handling. Generator queues property3 for this specific phone; no modem/NV writes. Partial DEX reassembled successfully. Re-run helper patches after any reset from base smali.

Updated verification: port-afphome-selector.py replaces the hard-coded selector ID with an app-local helper resolving android:drawable/kc_list_selector by name. Reassembled partial DEX successfully; method audit now1176 Android references, zero missing and15 Kyocera dependencies. Updated resource audit no longer finds the mismatched hard-coded ID (19 candidates/17 named).

decode-selector-ninepatch.py reconstructs source nine-patches from stock compiled stretch/padding metadata. Five-resource closure under selector-source/res compiles with aapt/API25; verify-selector-roundtrip.py confirms both recompiled nine-patches retain identical pixels, stretch regions and padding. prepare-kyf37-lineage.py now queues copying these resources into framework overlay for the next generation, not while build is live. This fixes a specific private-resource mismatch; not complete launcher/runtime verification. Running port-afphome-silentmode.py again resets source, so follow it with port-afphome-selector.py before assembling.

WSL recovered. Initial build still live at ninja11244 beyond11% (2421/20458 incremental actions). Separate Oreo source sync completed successfully, authoritative final log confirmed; full Android8.1 tree now /home/pablo/kyf37-oreo. Next: product/Go configuration and hardware ABI requirements. No ROM flashed.

Pulled original framework-res.apk and AfpHome APK from the connected stock phone. audit-afphome-resources.py inspects compiled XML references and DEX constant operands, resolves names against the original framework ARSC, and compares them to SDK25 ARSC. It found20 candidates,18 named resources,17 with unchanged ID/name. The two unnamed candidates may be non-resource integers.

Required fix: hard-coded0x01080551 is stock @drawable/kc_list_selector but SDK25 @drawable/perm_group_system_tools. The call in AFPHomeInfosignListItem.setup must use a ported selector's actual new resource ID (or dynamic lookup), not reuse the old private framework ID. Preserve selector states and dependent resources; do not silently replace it with an unrelated stock target drawable. Original decoded selector saved as kc-list-selector-stock.xml for follow-up dependency reconstruction.

Scope limits: SDK resources are a baseline, not final compiled ROM framework; XML attribute IDs, ARSC references, style inheritance and dynamic lookups are not fully audited. Fifteen vendor method dependencies and stock framework widget/softkey integration remain incomplete. No claim of functioning launcher or complete resource compatibility.

Current host observations: WSL new commands twice failed with Service/0x8007274c, while live build/source-sync handles64789/84135 have not reported terminal. Last successful independent process check confirmed ninja11244. Do not restart solely for observation failure. Windows total RAM~33GB/free~1.1GB; revalidate workload/resource state when WSL responds.

Stock outer display runtime evidence saved in stock-subdisplay-runtime.txt. Binder services subdisplay and sublcd both exist; fb1 is owned system:graphics. Its disp_stat sysfs node does not exist on the currently running stock kernel despite old init chown stanza. Preserve actual interfaces, not assumed sysfs files.

Shared resource closure now extracted (36 definitions, 52 configurations), compiled against API25, and all35 original helper aliases verified by ARSC name/type lookup. Added shared source resources to product framework overlay. Standalone resource checks do not establish launcher runtime compatibility; framework build/runtime verification remains pending.


Actual framework build rejected new resources: framework-res ignores PRODUCT_AAPT_FLAGS. Generator now emits explicit add-resource declarations for model selector/shared assets; restarted after session64064 terminal exit1 in session62706, live ninja confirmed. Previous shared resource standalone check is still valid only for compilation/name resolution, not framework inclusion.


Framework export APK rebuilt successfully with explicit additions. verify-shared-resource-names.py --framework verifies all35 original aliases in package android with framework package ID0x01; shared-resource-framework-verification.json records IDs. This proves actual framework inclusion, not app runtime. Build62706 terminal exit1 subsequently hit Qualcomm encoder constants absent from original kernel.

