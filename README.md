# Linksys Velop — Home Assistant Integration

[![Home Assistant Marketplace](https://img.shields.io/badge/HA%20Marketplace-custom%20repository-41BDF5.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Conexo-Casa&repository=linksys-velop&category=integration)

A Home Assistant custom integration for the **Linksys Velop MX4000** (and compatible MX-series) mesh Wi-Fi system. Communicates locally over the JNAP HTTP API — no cloud dependency.

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

## Installation

### Marketplace (Home Assistant 2026.11 and newer)

[![Open your Home Assistant instance and show this repository in the Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Conexo-Casa&repository=linksys-velop&category=integration)

Or by hand:

1. Go to **Settings → Marketplace**.
2. Select **Add from link** (top right) and enter `Conexo-Casa/linksys-velop`.
   The first time, Home Assistant asks you to connect GitHub. That is a one-time,
   read-only sign-in on github.com.
3. Open **Linksys Velop** and select **Install**. The setup screen opens right away; a first
   install doesn't need a restart.

Updates show up under **Settings → Updates**. After an update, Home Assistant shows a
repair that offers to restart.

### HACS (Home Assistant 2026.10 and older)

1. HACS → **Integrations** → **⋮** → **Custom repositories**.
2. Add `https://github.com/Conexo-Casa/linksys-velop`, category **Integration**.
3. Download **Linksys Velop**, then restart Home Assistant.

An existing HACS install moves to the Marketplace by itself when you upgrade to 2026.11.

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
