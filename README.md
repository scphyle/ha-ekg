# EKG Device Monitor — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

Home Assistant integration for [EKG](https://git.tazhome.net/Chas/ekg) — a daemon that runs on Ubuntu devices (desktops, servers, laptops, wall tablets) and reports system health metrics to Home Assistant.

> **This repo is a mirror.** Source of truth and issue tracker: [git.tazhome.net/Chas/ekg](https://git.tazhome.net/Chas/ekg)

## What it does

Once installed, each device running the `ha-heartbeat` daemon appears in Home Assistant as a device with:

- CPU, memory, and disk usage sensors (per mount point)
- Network I/O rates per interface
- Hardware temperature sensors
- System uptime and version
- A **command dropdown** to send actions to the device

## Supported commands

| Command | Action |
|---------|--------|
| `reboot` | Reboot the device |
| `shutdown` | Power off |
| `suspend` | Sleep / suspend |
| `lock` | Lock the screen |
| `update` | Install the latest `ha-heartbeat` package via apt |
| `script:<name>` | Run a custom script on the device |

## Requirements

- Each device must have `ha-heartbeat` installed and running
- HA and the device must be on the same network (mDNS/local polling)

## Install via HACS

1. In HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/scphyle/ha-ekg` — category: **Integration**
3. Install **EKG Device Monitor** and restart Home Assistant
4. Devices are discovered automatically — check **Settings → Notifications**

## Install ha-heartbeat on a device

```bash
curl -fsSL http://git.tazhome.net/Chas/ekg/raw/branch/main/setup.sh | sudo bash
```

## Links

- **Main repo & source code**: [git.tazhome.net/Chas/ekg](https://git.tazhome.net/Chas/ekg)
- **Issues & contributions**: open issues on the main repo
