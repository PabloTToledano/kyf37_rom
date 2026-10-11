#!/system/bin/sh
echo 'App identity before requesting root:'
id
echo 'Identity granted by su:'
/system/xbin/su -c id
