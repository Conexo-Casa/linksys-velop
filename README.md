# Linksys Velop — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A HACS-compatible Home Assistant custom integration for the **Linksys Velop MX4000** (and compatible MX-series) mesh Wi-Fi system. Communicates locally over the JNAP HTTP API — no cloud dependency.

---

## Features

| Platform | Entity | Description |
|---|---|---|
| `sensor` | WAN IP Address | Current public IP from the WAN port |
| `sensor` | WAN Connection Status | `Connected` / `Disconnected` |
| `sensor` | Connected Devices | Count of active DHCP leases |
| `sensor` | LAN IP Address | Router LAN IP |
| `sensor` | Firmware Version | Installed firmware string |
| `binary_sensor` | WAN Connected | `on` when internet is reachable |
| `binary_sensor` | Firmware Update Available | `on` when a newer firmware exists |
| `button` | Reboot Router | Sends a reboot command to the primary node |
| `device_tracker` | One per DHCP lease | Network-presence tracking per device |

---

## Requirements

- Home Assistant 2023.1 or later
- Linksys Velop MX4000 (or any MX-series node with JNAP API support)
- Router admin password
- HA must be on the same LAN as the primary Velop node (local API)

---

## Installation via HACS

1. Open **HACS** → **Integrations**
2. Click the three-dot menu → **Custom repositories**
3. Add `https://github.com/Conexo-Casa/linksys-velop` with category **Integration**
4. Search for **Linksys Velop** and click **Download**
5. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Linksys Velop**
3. Enter:
   - **Router IP Address** — typically `192.168.1.1`
   - **Admin Password** — the password you use for the router admin interface
   - **Port** — leave as `80` unless you have changed it

---

## Entities in Detail

### Sensors

**Connected Devices** includes an `extra_state_attributes` list of all current leases:

```yaml
devices:
  - hostname: my-laptop
    ip: 192.168.1.42
    mac: aa:bb:cc:dd:ee:ff
```

### Device Trackers

Each device seen in the DHCP lease table gets a `device_tracker` entity. This updates every 30 seconds. You can use these in automations for home/away detection:

```yaml
automation:
  - alias: "Arrive home"
    trigger:
      platform: state
      entity_id: device_tracker.my_phone
      to: "home"
    action:
      service: light.turn_on
      target:
        entity_id: light.hallway
```

### Reboot Button

The **Reboot Router** button calls the JNAP `core/Reboot` action on the primary node. Use with caution — it will briefly drop all network connectivity.

---

## Troubleshooting

**Cannot connect**
- Confirm the router IP in your browser (`http://192.168.1.1`)
- Ensure HA is on the same subnet as the router
- Check that port 80 is not blocked by a firewall

**Invalid auth**
- Use the **admin** password (the same one used in the Linksys app or web UI)

**Enable debug logging**

```yaml
logger:
  default: warning
  logs:
    custom_components.linksys_velop: debug
```

---

## Compatibility

Tested model: **MX4200** (MX4000 series). The JNAP API is consistent across the MX-series and WHW-series, so other Velop models should work. Open an issue if you find differences.

---

## License

MIT — see [LICENSE](LICENSE)

## About Conexo-Casa

[Conexo-Casa](https://github.com/Conexo-Casa) is a 501(c)(3) non-profit building accessible home automation tools for people with neurocognitive impairments and the elderly.
