$ErrorActionPreference='Stop'
$adb='C:/Users/pablo/Downloads/platform-tools-latest-windows/platform-tools/adb.exe'
$serial='981108631314'
$folder=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../kyf37-rom/appearance-switch'))
$apps=@(
    @{Package='org.kyf37.home'; Name='Kyf37Home'},
    @{Package='org.kyf37.phonesettings'; Name='Kyf37PhoneSettings'},
    @{Package='com.android.settings'; Name='Settings'}
)
foreach($app in $apps){
    if(-not(Test-Path -LiteralPath (Join-Path $folder ($app.Name+'.apk')))){throw "Missing $($app.Name).apk"}
}
& (Join-Path $PSScriptRoot 'phone-lock.ps1') acquire appearance-switch 10
try{
    foreach($app in $apps){
        $backup=Join-Path $folder ($app.Name+'-before-appearance.apk')
        if(-not(Test-Path -LiteralPath $backup)){
            $paths=& $adb -s $serial shell pm path $app.Package
            if($LASTEXITCODE -ne 0){throw 'Cannot locate existing app'}
            $old=($paths | Select-Object -First 1).Replace('package:','').Trim()
            & $adb -s $serial pull $old $backup
            if($LASTEXITCODE -ne 0){throw 'Backup failed'}
        }
        & $adb -s $serial install -r (Join-Path $folder ($app.Name+'.apk'))
        if($LASTEXITCODE -ne 0){throw "Installation failed for $($app.Package)"}
    }
    & $adb -s $serial shell pm grant org.kyf37.home android.permission.READ_EXTERNAL_STORAGE
    if($LASTEXITCODE -ne 0){throw 'Wallpaper sampling permission grant failed'}
    & $adb -s $serial shell am force-stop org.kyf37.home
    & $adb -s $serial shell input keyevent 224
    & $adb -s $serial shell wm dismiss-keyguard
    & $adb -s $serial shell am start -n org.kyf37.home/.Home
    Start-Sleep -Seconds 2
    & $adb -s $serial shell screencap -p /data/local/tmp/appearance-home.png
    & $adb -s $serial pull /data/local/tmp/appearance-home.png (Join-Path $folder 'home-initial.png')
    if($LASTEXITCODE -ne 0){throw 'Screenshot failed'}
}finally{
    & (Join-Path $PSScriptRoot 'phone-lock.ps1') release appearance-switch
}
