# Offline app adapter continuation

The owner requested continuing all app ports offline. No phone operations were
performed in this pass. The earlier launcher-install attempt had backed up Home,
then failed when the device disconnected; it is not a successful installation.

InfoServer no longer calls the removed PackageManager package-size method. Its
adapter queries Android 10 StorageStatsManager for the original package, user and
storage UUID, asynchronously maps real application/data/cache bytes into
PackageStats, and invokes the original observer. Query failures notify failure;
they do not fabricate successful zero-byte results. PACKAGE_USAGE_STATS is now
declared. App-op approval, cross-user access and callback/provider execution remain
unverified on hardware.

Removed monthly billing-cycle APIs and cycleDay field access now use the real
NetworkPolicy.cycleRule. Monthly start day/timezone come from the actual rule.
Nonmonthly rules retain cycleDay=-1 and reject the old monthly boundary operation.
The calculation preserves strict previous/next boundary behavior and the old
short-month snap to the last day's 23:59:59. Sixteen JVM checks cover exact
boundaries, leap years, invalid days, Tokyo, fractional-second precision and both Spanish DST transitions.

IrDATransfer profile lookup now reproduces the OEM contract using Android contact
provider APIs: query the profile, create an empty local profile if absent, close
the cursor, and obtain its actual lookup URI. Denied/unavailable operations return
null, as the original wrapper did. Its separate custom-vCard provider format and
FeliCa/IrDA UART coexistence remain unfinished.

Reflection signatures for these new adapters were verified against eleven actual
compiled Android classes. This does not establish runtime permission, app-op,
provider, filesystem or reflection behavior. The original MediaContainer binding
and directory/filesystem measurement backend in InfoServer still need migration;
that app remains an optional, disabled candidate.

Reproduce with port-remaining-stock-apps-android10.py --modules InfoServer
IrDATransfer, test-stock-monthly-cycles.py, verify-stock-adapter-contracts.py,
build-remaining-stock-candidates.py, audit-remaining-stock-apis.py,
verify-remaining-stock-signatures.py and report-all-stock-port-status.py.
All scripts are in device-inspection. Current results are in cycle-tests.json,
adapter-contracts.json, api-audits.json, signature-verification.json and readiness.md.

All 53 signed optional candidates rebuilt. PRODUCT_PACKAGES remains unchanged;
no stock payment, carrier, updater, setup or MDM service was enabled.

The final Ninja invocation completed successfully in 9:01, but its wrapper then
reported a syntax error after another session changed the running shell file.
The current wrapper passes bash -n. This is not recorded as a clean wrapper build.
Existing signed intermediates were collected with --collect-existing, then checked
against current source payloads and the Android API-29/platform-certificate verifier.
artifact-collection.json records that no successful wrapper exit was certified.
Avoid editing an executing shell wrapper; its byte offset can resume inside a new
statement. A future wrapper fix must be made when no session is executing it.
