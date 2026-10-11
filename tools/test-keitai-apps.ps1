<#
  Keypad walk-through of the KYF37 keitai Phone / Messages / Contacts apps (see KEITAI-APPS.md).
  Needs the phone lock:   .\tools\phone-lock.ps1 acquire <name> 60   ... release when done.

  .\tools\test-keitai-apps.ps1 -Action install    # adb install -r -d the three APKs, grant runtime permissions, take the roles
  .\tools\test-keitai-apps.ps1 -Action seed       # 6 contacts, 8 call log rows, 4 received texts (debug hook)
  .\tools\test-keitai-apps.ps1 -Action walk       # every screen: keys -> screenshot + uiautomator dump into -Out
  .\tools\test-keitai-apps.ps1 -Action incall     # fake incoming / outgoing calls through the debug test line
  .\tools\test-keitai-apps.ps1 -Action clean      # remove the seed data (keeps the APKs)
  .\tools\test-keitai-apps.ps1 -Action hashes     # sha256 of the installed APK files on the phone

  Real calls, SMS, MMS and emergency dialling need a working radio and are NOT exercised here.
#>
param(
    [ValidateSet('install','seed','walk','incall','clean','hashes','all')][string]$Action = 'all',
    [string]$Out = "$PSScriptRoot\..\kyf37-rom\keitai-apps\walk",
    [string]$Apks = "$PSScriptRoot\..\kyf37-rom\keitai-apps"
)
$ErrorActionPreference = 'Continue'
$env:MSYS_NO_PATHCONV = '1'
$adb = 'C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial = '981108631314'
New-Item -ItemType Directory -Force $Out | Out-Null

function A { param([Parameter(ValueFromRemainingArguments)]$a) & $adb -s $serial @a 2>&1 }
function Sh { param([string]$c) & $adb -s $serial shell $c 2>&1 }
function Key { param([string[]]$k, [int]$ms = 500) foreach ($x in $k) { Sh "input keyevent $x" | Out-Null; Start-Sleep -Milliseconds $ms } }
function Digits { param([string]$s) foreach ($ch in $s.ToCharArray()) { Key @("KEYCODE_$ch") 250 } }
function Shot {
    param([string]$name)
    Start-Sleep -Milliseconds 700
    Sh "screencap -p /sdcard/kt.png" | Out-Null
    A pull /sdcard/kt.png "$Out\$name.png" | Out-Null
    Sh "uiautomator dump /sdcard/kt.xml" | Out-Null
    A pull /sdcard/kt.xml "$Out\$name.xml" | Out-Null
    $focus = (Sh "dumpsys window | grep mCurrentFocus") -join ' '
    "{0,-34} {1}" -f $name, $focus.Trim()
}
function Selected { param([string]$name)
    $x = Get-Content "$Out\$name.xml" -Raw -ErrorAction SilentlyContinue
    if (-not $x) { return }
    $m = [regex]::Matches($x, '<node[^>]*?text="([^"]*)"[^>]*?(selected|focused)="true"')
    ($m | ForEach-Object { $_.Groups[1].Value } | Where-Object { $_ } | Select-Object -First 3) -join ' | '
}
function Start-App { param([string]$comp) Sh "am start -n $comp" | Out-Null; Start-Sleep -Seconds 2 }

$perms = @{
  'org.kyf37.dialer'   = 'CALL_PHONE READ_PHONE_STATE ANSWER_PHONE_CALLS READ_CALL_LOG WRITE_CALL_LOG READ_CONTACTS'
  'org.kyf37.messages' = 'SEND_SMS RECEIVE_SMS READ_SMS RECEIVE_MMS RECEIVE_WAP_PUSH READ_CONTACTS CALL_PHONE READ_PHONE_STATE'
  'org.kyf37.contacts' = 'READ_CONTACTS WRITE_CONTACTS GET_ACCOUNTS CALL_PHONE READ_EXTERNAL_STORAGE WRITE_EXTERNAL_STORAGE'
}

function Do-Install {
    A root | Out-Null; Start-Sleep -Seconds 4
    foreach ($p in 'Dialer','Messages','Contacts') {
        "install Kyf37$p : " + ((A install -r -d "$Apks\Kyf37$p.apk") -join ' ')
    }
    foreach ($kv in $perms.GetEnumerator()) {
        foreach ($pm in $kv.Value.Split(' ')) { Sh "pm grant $($kv.Key) android.permission.$pm" | Out-Null }
    }
    Sh "appops set org.kyf37.messages WRITE_SMS allow" | Out-Null
    # roles (RoleBoot does this on a real ROM boot; here we drive it by hand)
    Sh "cmd role add-role-holder --user 0 android.app.role.DIALER org.kyf37.dialer" | Out-Null
    Sh "cmd role add-role-holder --user 0 android.app.role.SMS org.kyf37.messages" | Out-Null
    Sh "dumpsys role | grep -A2 -E 'DIALER|SMS'"
    Sh "dumpsys telecom | grep -i 'default dialer\|mDefaultDialer' | head -3"
}

function Add-Contact { param([string]$name, [string]$mobile, [string]$email = '')
    Sh "content insert --uri content://com.android.contacts/raw_contacts --bind account_type:n: --bind account_name:n:" | Out-Null
    $row = (Sh "content query --uri content://com.android.contacts/raw_contacts --projection _id --sort '_id DESC'") | Select-Object -First 1
    $id = ([regex]::Match($row, '_id=(\d+)')).Groups[1].Value
    Sh "content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$id --bind mimetype:s:vnd.android.cursor.item/name --bind data1:s:'$name'" | Out-Null
    Sh "content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$id --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:$mobile --bind data2:i:2" | Out-Null
    if ($email) { Sh "content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$id --bind mimetype:s:vnd.android.cursor.item/email_v2 --bind data1:s:$email --bind data2:i:1" | Out-Null }
}

function Do-Seed {
    Add-Contact 'Alice Adams'   '600111001' 'alice@example.com'
    Add-Contact 'Bob Brown'     '600111002'
    Add-Contact 'Carla Cruz'    '600111003'
    Add-Contact 'David Duran'   '600111004' 'david@example.com'
    Add-Contact 'Elena Estevez' '600111005'
    Add-Contact 'Zoe Zamora'    '600111026'
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $types = @(1,2,3,1,2,1,3,2)   # 1 incoming 2 outgoing 3 missed
    $nums  = @('600111001','600111002','600111003','600111001','600111004','600111999','600111005','600111001')
    for ($i = 0; $i -lt 8; $i++) {
        $d = $now - ($i * 3600000)
        Sh "content insert --uri content://call_log/calls --bind number:s:$($nums[$i]) --bind type:i:$($types[$i]) --bind date:l:$d --bind duration:i:$(30 + 17*$i) --bind new:i:0 --bind is_read:i:1" | Out-Null
    }
    $texts = @(@('600111001','Hello from Alice - are we still on for lunch?'),
               @('600111002','Bob here. The long message test: ' + ('lorem ipsum ' * 12)),
               @('600111003','Short one'),
               @('600111001','Second text from Alice'))
    foreach ($t in $texts) {
        Sh "am broadcast -n org.kyf37.messages/.StatusReceiver\`$Debug -a org.kyf37.messages.DEBUG_RECEIVE --es from $($t[0]) --es body '$($t[1])'" | Out-Null
        Start-Sleep -Milliseconds 600
    }
    "seeded: contacts=" + ((Sh "content query --uri content://com.android.contacts/contacts --projection _id") | Measure-Object).Count
}

function Do-Clean {
    Sh "content delete --uri content://call_log/calls" | Out-Null
    Sh "content delete --uri content://sms" | Out-Null
    Sh "content delete --uri content://com.android.contacts/raw_contacts" | Out-Null
    'cleaned'
}

function Do-Walk {
    "--- Home tiles"
    Sh "input keyevent KEYCODE_HOME" | Out-Null; Start-Sleep 1
    Shot 'home'
    "--- Phone (dial pad)"
    Start-App 'org.kyf37.dialer/.DialerActivity'
    Shot 'dialer-empty'
    Key @('KEYCODE_DPAD_DOWN') ; Shot 'dialer-recents-down'
    Digits '60011'; Shot 'dialer-typing'
    Key @('KEYCODE_DEL') 400; Shot 'dialer-backspace'
    Key @('KEYCODE_MENU'); Shot 'dialer-menu'
    Key @('KEYCODE_BACK'); Key @('KEYCODE_BACK') 400
    "--- Recents"
    Start-App 'org.kyf37.dialer/.RecentsActivity'
    Shot 'recents-all'; Key @('KEYCODE_DPAD_RIGHT'); Shot 'recents-missed'; Key @('KEYCODE_DPAD_RIGHT'); Shot 'recents-dialed'
    Key @('KEYCODE_DPAD_RIGHT','KEYCODE_DPAD_RIGHT'); Shot 'recents-frequent'
    Key @('KEYCODE_DPAD_CENTER'); Shot 'recents-actions'; Key @('KEYCODE_BACK')
    "--- Speed dial"
    Start-App 'org.kyf37.dialer/.SpeedDialActivity'; Shot 'speeddial'
    "--- Contacts"
    Start-App 'org.kyf37.contacts/.ContactListActivity'; Shot 'contacts-list'
    Key @('KEYCODE_DPAD_DOWN'); Shot 'contacts-down'
    Key @('KEYCODE_2'); Shot 'contacts-jump-A'
    Key @('KEYCODE_3'); Shot 'contacts-jump-D'
    Key @('KEYCODE_DPAD_CENTER'); Shot 'contact-view'
    Key @('KEYCODE_DPAD_DOWN','KEYCODE_DPAD_DOWN','KEYCODE_DPAD_DOWN'); Shot 'contact-view-down'
    Key @('KEYCODE_BACK'); Key @('KEYCODE_MENU'); Shot 'contacts-menu'; Key @('KEYCODE_BACK')
    Sh "am start -n org.kyf37.contacts/.ContactEditActivity -a android.intent.action.INSERT" | Out-Null; Start-Sleep 2
    Shot 'contact-edit-empty'
    "--- Messages"
    Start-App 'org.kyf37.messages/.ConversationListActivity'; Shot 'messages-list'
    Key @('KEYCODE_DPAD_CENTER'); Shot 'thread'
    Key @('KEYCODE_DPAD_CENTER'); Shot 'thread-actions'; Key @('KEYCODE_BACK')
    Key @('KEYCODE_DPAD_DOWN'); Shot 'thread-compose'
    Key @('KEYCODE_BACK'); Key @('KEYCODE_MENU'); Shot 'messages-menu'; Key @('KEYCODE_BACK')
    Sh "input keyevent KEYCODE_HOME" | Out-Null
}

function Do-InCall {
    Sh "am broadcast -n org.kyf37.dialer/.TestConnectionService`$Debug -a org.kyf37.dialer.DEBUG_REMOTE_HANGUP" | Out-Null
    Sh "telecom set-phone-account-enabled org.kyf37.dialer/org.kyf37.dialer.TestConnectionService kyf37-test-line 0" | Out-Null
    Sh "am broadcast -n org.kyf37.dialer/.TestConnectionService\`$Debug -a org.kyf37.dialer.DEBUG_INCOMING --es number 600111001" | Out-Null
    Start-Sleep 3; Shot 'incall-incoming'
    Key @('KEYCODE_CALL') 1500; Shot 'incall-active'
    Key @('KEYCODE_5'); Key @('KEYCODE_DPAD_CENTER'); Shot 'incall-muted'
    Key @('KEYCODE_MENU'); Shot 'incall-menu'; Key @('KEYCODE_BACK')
    Key @('KEYCODE_ENDCALL') 1500; Shot 'incall-ended'
    Start-Sleep 2
    Sh "am broadcast -n org.kyf37.dialer/.TestConnectionService\`$Debug -a org.kyf37.dialer.DEBUG_OUTGOING --es number 600111002" | Out-Null
    Start-Sleep 3; Shot 'incall-outgoing'
    Sh "am broadcast -n org.kyf37.dialer/.TestConnectionService\`$Debug -a org.kyf37.dialer.DEBUG_REMOTE_HANGUP" | Out-Null
    Start-Sleep 3; Shot 'incall-remote-hangup'
}

function Do-Hashes {
    foreach ($p in 'Dialer','Messages','Contacts') {
        $path = ((Sh "pm path org.kyf37.$($p.ToLower())") -replace 'package:','').Trim()
        "{0}  {1}" -f ((Sh "sha256sum $path") -join ' '), $path
    }
}

switch ($Action) {
    'install' { Do-Install }
    'seed'    { Do-Seed }
    'walk'    { Do-Walk }
    'incall'  { Do-InCall }
    'clean'   { Do-Clean }
    'hashes'  { Do-Hashes }
    'all'     { Do-Install; Do-Seed; Do-Walk; Do-InCall; Do-Hashes }
}
