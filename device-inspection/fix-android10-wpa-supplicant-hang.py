#!/usr/bin/env python3
"""Fix wpa_supplicant netlink error handling and roaming hang for KYF37 prima Wi-Fi.
Idempotent. Run in WSL:
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-wpa-supplicant-hang.py
"""
import sys
from pathlib import Path

WPAS_ROOT = Path.home() / 'kyf37-android10/external/wpa_supplicant_8'
DRV_NL = WPAS_ROOT / 'src/drivers/driver_nl80211.c'
DRV_CAPA = WPAS_ROOT / 'src/drivers/driver_nl80211_capa.c'

if not DRV_NL.exists() or not DRV_CAPA.exists():
    print(f"Error: Could not find {DRV_NL} or {DRV_CAPA}")
    sys.exit(1)

# 1. Patch driver_nl80211_capa.c: disable roaming_vendor_cmd_avail
capa_content = DRV_CAPA.read_text()
old_capa_target = """#ifdef CONFIG_DRIVER_NL80211_QCA
				case QCA_NL80211_VENDOR_SUBCMD_ROAMING:
					drv->roaming_vendor_cmd_avail = 1;
					break;"""

new_capa_replacement = """#ifdef CONFIG_DRIVER_NL80211_QCA
				case QCA_NL80211_VENDOR_SUBCMD_ROAMING:
					/* Prima (wlan.ko) does not support vendor roaming policy offload;
					 * attempting it fails and deadlocks the supplicant. */
					drv->roaming_vendor_cmd_avail = 0;
					break;"""

if old_capa_target in capa_content:
    capa_content = capa_content.replace(old_capa_target, new_capa_replacement)
    DRV_CAPA.write_text(capa_content)
    print("Patched driver_nl80211_capa.c: disabled roaming_vendor_cmd_avail")
elif new_capa_replacement in capa_content:
    print("driver_nl80211_capa.c already patched")
else:
    print("Warning: Target block not found in driver_nl80211_capa.c")

# 2. Patch driver_nl80211.c: error_handler, roaming ACK, and connect logging
drv_content = DRV_NL.read_text()

old_err_target = """\t*ret = err->error;

\tif (!(nlh->nlmsg_flags & NLM_F_ACK_TLVS))
\t\treturn NL_SKIP;"""

new_err_replacement = """\t*ret = err->error;
\tif (*ret > 0)
\t\t*ret = -*ret;
\tif (*ret == 0)
\t\t*ret = -1;

\tif (!(nlh->nlmsg_flags & NLM_F_ACK_TLVS))
\t\treturn NL_STOP;"""

if old_err_target in drv_content:
    drv_content = drv_content.replace(old_err_target, new_err_replacement)
    print("Patched driver_nl80211.c: error_handler returns NL_STOP and enforces negative error")

old_err_end = """\t\twpa_printf(MSG_ERROR, "nl80211: kernel reports: %*s",
\t\t\t   len, (char *) nla_data(tb[NLMSGERR_ATTR_MSG]));
\t}

\treturn NL_SKIP;
}"""

new_err_end = """\t\twpa_printf(MSG_ERROR, "nl80211: kernel reports: %*s",
\t\t\t   len, (char *) nla_data(tb[NLMSGERR_ATTR_MSG]));
\t}

\treturn NL_STOP;
}"""

if old_err_end in drv_content:
    drv_content = drv_content.replace(old_err_end, new_err_end)
    print("Patched driver_nl80211.c: error_handler end returns NL_STOP")

old_roam_msg = "if (!(msg = nl80211_drv_msg(drv, 0, NL80211_CMD_VENDOR)) ||"
new_roam_msg = "if (!(msg = nl80211_drv_msg(drv, NLM_F_ACK, NL80211_CMD_VENDOR)) ||"

if old_roam_msg in drv_content:
    drv_content = drv_content.replace(old_roam_msg, new_roam_msg)
    print("Patched driver_nl80211.c: nl80211_roaming passes NLM_F_ACK")

# Diagnostic logs for associate and connect
assoc_target = """static int wpa_driver_nl80211_associate(
\tvoid *priv, struct wpa_driver_associate_params *params)
{
\tstruct i802_bss *bss = priv;
\tstruct wpa_driver_nl80211_data *drv = bss->drv;
\tint ret = -1;
\tstruct nl_msg *msg;"""

assoc_repl = """static int wpa_driver_nl80211_associate(
\tvoid *priv, struct wpa_driver_associate_params *params)
{
\tstruct i802_bss *bss = priv;
\tstruct wpa_driver_nl80211_data *drv = bss->drv;
\tint ret = -1;
\tstruct nl_msg *msg;

\twpa_printf(MSG_ERROR, "nl80211: associate enter mode=%d sme=%d",
\t\t   params->mode, !!(drv->capa.flags & WPA_DRIVER_FLAGS_SME));"""

if assoc_target in drv_content:
    drv_content = drv_content.replace(assoc_target, assoc_repl)
    print("Added MSG_ERROR to wpa_driver_nl80211_associate")

conn_target = """\tret = nl80211_connect_common(drv, params, msg);
\tif (ret)
\t\tgoto fail;"""

conn_repl = """\tret = nl80211_connect_common(drv, params, msg);
\tif (ret) {
\t\twpa_printf(MSG_ERROR, "nl80211: connect_common failed ret=%d", ret);
\t\tgoto fail;
\t}"""

if conn_target in drv_content:
    drv_content = drv_content.replace(conn_target, conn_repl)
    print("Added MSG_ERROR to connect_common check")

conn_send_target = """\tif (nl_connect)
\t\tret = send_and_recv(drv->global, nl_connect, msg,
\t\t\t\t    NULL, (void *) -1);
\telse
\t\tret = send_and_recv_msgs(drv, msg, NULL, (void *) -1);

\tmsg = NULL;
\tif (ret) {
\t\twpa_printf(MSG_DEBUG, "nl80211: MLME connect failed: ret=%d "
\t\t\t   "(%s)", ret, strerror(-ret));
\t} else {
\t\twpa_printf(MSG_DEBUG,
\t\t\t   "nl80211: Connect request send successfully");
\t}"""

conn_send_repl = """\twpa_printf(MSG_ERROR, "nl80211: sending connect msg");
\tif (nl_connect)
\t\tret = send_and_recv(drv->global, nl_connect, msg,
\t\t\t\t    NULL, (void *) -1);
\telse
\t\tret = send_and_recv_msgs(drv, msg, NULL, (void *) -1);

\tmsg = NULL;
\tif (ret) {
\t\twpa_printf(MSG_ERROR, "nl80211: MLME connect failed: ret=%d "
\t\t\t   "(%s)", ret, strerror(-ret));
\t} else {
\t\twpa_printf(MSG_ERROR,
\t\t\t   "nl80211: Connect request send successfully");
\t}"""

# 3. Patch driver_nl80211.c: disable NL80211_ATTR_IFACE_SOCKET_OWNER for Linux 3.10 compatibility
# In 3.10 kernel attr 204 is NL80211_ATTR_AUTHORIZATION_STATUS (NLA_U8).
# Userspace sending flag (len 0) causes kernel validate_nla to return -ERANGE (34).
old_socket_owner = """static int nl80211_connect_common(struct wpa_driver_nl80211_data *drv,
\t\t\t\t  struct wpa_driver_associate_params *params,
\t\t\t\t  struct nl_msg *msg)
{
\tif (nla_put_flag(msg, NL80211_ATTR_IFACE_SOCKET_OWNER))
\t\treturn -1;"""

new_socket_owner = """static int nl80211_connect_common(struct wpa_driver_nl80211_data *drv,
\t\t\t\t  struct wpa_driver_associate_params *params,
\t\t\t\t  struct nl_msg *msg)
{
\t/* Disabled for Linux 3.10 kernel compatibility: in 3.10 attr 204 is
\t * NL80211_ATTR_AUTHORIZATION_STATUS (NLA_U8), sending flag (len 0)
\t * fails validation with -ERANGE. */
\t/* if (nla_put_flag(msg, NL80211_ATTR_IFACE_SOCKET_OWNER)) return -1; */"""

if old_socket_owner in drv_content:
    drv_content = drv_content.replace(old_socket_owner, new_socket_owner)
    print("Patched driver_nl80211.c: disabled NL80211_ATTR_IFACE_SOCKET_OWNER")
elif new_socket_owner in drv_content:
    print("driver_nl80211.c already has IFACE_SOCKET_OWNER disabled")

DRV_NL.write_text(drv_content)
print("Fix script completed successfully.")

