# Stock app port readiness

Every row is an offline candidate. Zero static failures does not establish runtime compatibility. Existing six selected ports, flashlight replacement, stock dialer and One Seg TV have separate status documents.

| Module | Classes | APIs | Resources | Signed | Remaining checks/blockers |
|---|---:|---:|---:|---|---|
| AfpHome | 0 | 2 | 0 | yes | legacy framework API contracts unresolved; original audio streams/routing need adaptation; offline candidate; not installed or hardware verified |
| BrowserMenu | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| Calculator | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| Charactercheck | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| DataFolder | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| DiagService | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| Ecomode | 0 | 1 | 0 | yes | legacy framework API contracts unresolved; offline candidate; not installed or hardware verified |
| Edy4FP | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| Effect | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| EmgBuzzApp | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| FPEmojiProvider | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| FakeIncoming | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| FeliCaInit | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| FeliCaInitApp | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| FeliCaLock | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| FeliCaLockSettingService | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| FeliCaUeventService | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| InfoChild | 0 | 0 | 0 | yes | legacy service/provider/carrier endpoint behavior unverified; offline candidate; not installed or hardware verified |
| InfoServer | 0 | 2 | 0 | yes | legacy framework API contracts unresolved; legacy DefaultContainerService absent; data-collection backend migration required; legacy service/provider/carrier endpoint behavior unverified; offline candidate; not installed or hardware verified |
| IrDATransfer | 0 | 1 | 0 | yes | legacy framework API contracts unresolved; custom vCard provider contract unresolved; UART ownership must coexist with FeliCa; offline candidate; not installed or hardware verified |
| KC_Infosign | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| KErrService | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| KdfsService | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| LocalCalendarPhoneAccount | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| LogCollectionTool | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| MobileFeliCaClient | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| MobileFeliCaSettingApp | 5 | 0 | 0 | yes | unresolved classes: org/simalliance/openmobileapi/Channel, org/simalliance/openmobileapi/Reader, org/simalliance/openmobileapi/SEService, org/simalliance/openmobileapi/SEService$CallBack, org/simalliance/openmobileapi/Session; FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| MobileFeliCaWebPlugin | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| MobileFeliCaWebPluginBoot | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| Mushroom | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| PairFunction | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| Pedometer | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| PermissionToAccessKCCameraEx | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| Readout | 0 | 1 | 0 | yes | legacy framework API contracts unresolved; original audio streams/routing need adaptation; offline candidate; not installed or hardware verified |
| Start_SetupWizard | 0 | 0 | 0 | yes | legacy service/provider/carrier endpoint behavior unverified; offline candidate; not installed or hardware verified |
| Sugumoji | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| SupportMDM | 0 | 0 | 0 | yes | legacy service/provider/carrier endpoint behavior unverified; offline candidate; not installed or hardware verified |
| TVConnect | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| Weather | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| WfdStateController | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| aumall | 0 | 0 | 0 | yes | legacy service/provider/carrier endpoint behavior unverified; offline candidate; not installed or hardware verified |
| autoassist | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| autoassist_manager | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| felicaservice | 0 | 0 | 0 | yes | FeliCa service, device access, trust/provisioning and secure-element behavior unverified; offline candidate; not installed or hardware verified |
| kc_communicate | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| lifesettings | 0 | 2 | 0 | yes | legacy framework API contracts unresolved; original audio streams/routing need adaptation; offline candidate; not installed or hardware verified |
| mbok | 0 | 0 | 0 | yes | legacy service/provider/carrier endpoint behavior unverified; offline candidate; not installed or hardware verified |
| news | 0 | 0 | 0 | yes | legacy service/provider/carrier endpoint behavior unverified; offline candidate; not installed or hardware verified |
| openshuffle | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| sysupdater | 0 | 0 | 0 | yes | original stock OTA updater must be replaced with owner-ROM update flow before activation; offline candidate; not installed or hardware verified |
| transfer | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| vBookmark | 0 | 0 | 0 | yes | offline candidate; not installed or hardware verified |
| weathernews | 0 | 0 | 0 | yes | legacy service/provider/carrier endpoint behavior unverified; offline candidate; not installed or hardware verified |
