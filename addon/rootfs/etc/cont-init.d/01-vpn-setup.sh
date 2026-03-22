#!/usr/bin/with-contenv bashio
# ExpressVPN (OpenVPN) setup — only runs if enabled in addon config

vpn_enabled=$(bashio::config 'expressvpn_enabled' 'false')
if [ "$vpn_enabled" != "true" ]; then
    bashio::log.info "ExpressVPN disabled — skipping VPN setup"
    exit 0
fi

vpn_user=$(bashio::config 'expressvpn_username' '')
vpn_pass=$(bashio::config 'expressvpn_password' '')
vpn_config=$(bashio::config 'expressvpn_config' '')

# ---------------------------------------------------------------------------
# Validate required fields
# ---------------------------------------------------------------------------
if [ -z "$vpn_user" ] || [ -z "$vpn_pass" ]; then
    bashio::log.error "ExpressVPN enabled but username/password not set — skipping VPN"
    exit 0
fi

# ---------------------------------------------------------------------------
# Resolve the .ovpn config file
# ---------------------------------------------------------------------------
ovpn_file=""
if [ -n "$vpn_config" ]; then
    # User specified a filename — look in /config/expressvpn/
    ovpn_file="/config/expressvpn/${vpn_config}"
else
    # Pick the first .ovpn file found
    ovpn_file=$(find /config/expressvpn -name '*.ovpn' -type f 2>/dev/null | head -1)
fi

if [ -z "$ovpn_file" ] || [ ! -f "$ovpn_file" ]; then
    bashio::log.error "No .ovpn config found in /config/expressvpn/ — skipping VPN"
    bashio::log.error "Download .ovpn files from https://www.expressvpn.com/setup#manual"
    exit 0
fi

bashio::log.info "Using VPN config: ${ovpn_file}"

# ---------------------------------------------------------------------------
# Write auth credentials file
# ---------------------------------------------------------------------------
mkdir -p /run/openvpn
cat > /run/openvpn/auth.txt <<EOF
${vpn_user}
${vpn_pass}
EOF
chmod 600 /run/openvpn/auth.txt

# ---------------------------------------------------------------------------
# Create tun device if missing
# ---------------------------------------------------------------------------
if [ ! -c /dev/net/tun ]; then
    mkdir -p /dev/net
    mknod /dev/net/tun c 10 200
    chmod 600 /dev/net/tun
fi

# Store the resolved config path for the s6 service
echo "$ovpn_file" > /run/openvpn/config_path

bashio::log.info "ExpressVPN setup complete — VPN service will start"
