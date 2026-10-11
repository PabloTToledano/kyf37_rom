#!/system/bin/sh
# Module is built and ABI checked for the currently installed kernel #17 only.
case "$(uname -v)" in
 '#17 SMP PREEMPT Fri Oct 9 10:04:32 CEST 2026') ;;
 *) log -t Kyf37IR 'Kernel changed; rebuild and ABI-check IR module'; exit 1 ;;
esac
if [ ! -e /dev/kyf37_ir ]; then
 /system/bin/insmod /system/lib/modules/kyf37_ir_module.ko || exit 1
fi
exec /system/bin/kyf37_ir_service /system/bin/kyf37_ir_tx
