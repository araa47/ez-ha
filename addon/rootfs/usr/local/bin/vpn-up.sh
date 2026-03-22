#!/bin/bash
# Called by OpenVPN after tunnel is established
# Logs the VPN IP so the user can verify connectivity
echo "[vpn-up] VPN tunnel established on ${dev}"
echo "[vpn-up] VPN local IP: ${ifconfig_local:-unknown}"
