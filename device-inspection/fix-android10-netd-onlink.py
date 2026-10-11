#!/usr/bin/env python3
"""Fix netd IPv4 route installation for Linux 3.10 kernel compatibility.
On Linux 3.10, adding a gateway route without RTNH_F_ONLINK triggers fib_lookup
with flowi4_iif = 0. Android's policy routing rules require iif == lo, so
gateway lookups fail with -ENETUNREACH (-101). Setting RTNH_F_ONLINK bypasses
this validation and installs default gateway routes cleanly.

Idempotent. Run in WSL:
    python3 /mnt/c/Users/pablo/Documents/ChatGPT/flipphone_roms/device-inspection/fix-android10-netd-onlink.py
"""
import sys
from pathlib import Path

ROUTE_CTRL = Path.home() / 'kyf37-android10/system/netd/server/RouteController.cpp'

if not ROUTE_CTRL.exists():
    print(f"Error: {ROUTE_CTRL} does not exist")
    sys.exit(1)

content = ROUTE_CTRL.read_text()

target = """    // Assemble a rtmsg and put it in an array of iovec structures.
    rtmsg route = {
        .rtm_protocol = RTPROT_STATIC,
        .rtm_type = type,
        .rtm_family = family,
        .rtm_dst_len = prefixLength,
        .rtm_scope = static_cast<uint8_t>(nexthop ? RT_SCOPE_UNIVERSE : RT_SCOPE_LINK),
    };"""

replacement = """    // Assemble a rtmsg and put it in an array of iovec structures.
    rtmsg route = {
        .rtm_protocol = RTPROT_STATIC,
        .rtm_type = type,
        .rtm_family = family,
        .rtm_dst_len = prefixLength,
        .rtm_scope = static_cast<uint8_t>(nexthop ? RT_SCOPE_UNIVERSE : RT_SCOPE_LINK),
        .rtm_flags = static_cast<unsigned int>((family == AF_INET && nexthop && interface != OIF_NONE) ? RTNH_F_ONLINK : 0),
    };"""

if target in content:
    content = content.replace(target, replacement)
    ROUTE_CTRL.write_text(content)
    print("Patched RouteController.cpp: added RTNH_F_ONLINK for IPv4 gateways")
elif replacement in content:
    print("RouteController.cpp already patched with RTNH_F_ONLINK")
else:
    print("Error: Target pattern not found in RouteController.cpp")
    sys.exit(1)
