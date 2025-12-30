# Homelab Hardware Inventory

## Overview

| Role | Device | CPU | RAM | Primary Use |
|------|--------|-----|-----|-------------|
| Main Workstation | Alienware Aurora R15 | Ryzen 9 7900X | 32GB DDR5 | ML/Dev/Gaming |
| Travel Laptop | Dell Latitude 5430 Rugged | i5-1135G7 | 32GB DDR4 | Mobile Dev |
| Compute Node 1 | Beelink EQR6 | Ryzen 7 6800U | 32GB LPDDR5 | VM Host/Docker |
| Compute Node 2 | Beelink Mini PC | Ryzen 5 6600U | 24GB LPDDR5 | Services |
| Light Server 1 | KAMRUI Pinova P1 | Ryzen 3 3300U | 16GB DDR4 | Containers |
| Light Server 2 | KAMRUI Mini PC | Intel N97 | 16GB DDR4 | Low-power services |
| Edge AI 1 | ASUS Tinker Edge R | RK3399Pro | 4GB | NPU inference |
| Edge AI 2 | Jetson Nano (P3450) | ARM A57 | 4GB | CUDA inference |
| IoT Controller 1 | Raspberry Pi 4B | BCM2711 | 2-8GB | Bed automation |
| IoT Controller 2 | Raspberry Pi 4B | BCM2711 | 2-8GB | Bedroom TV |
| Legacy/NAS | HP Pavilion p6617c | Athlon II X4 630 | 8GB DDR3 | Storage/backup |

---

## Tier 1: Primary Workstations

### Alienware Aurora R15 (Main Desktop)

| Spec | Value |
|------|-------|
| **CPU** | AMD Ryzen 9 7900X |
| Cores/Threads | 12C / 24T |
| Base/Boost | 4.7 / 5.6 GHz |
| TDP | 170W |
| **GPU** | NVIDIA RTX 4080 |
| VRAM | 16GB GDDR6X |
| CUDA Cores | 9,728 |
| Tensor Cores | 304 (4th Gen) |
| **RAM** | 32GB DDR5 |
| **Storage** | 1TB NVMe SSD + 2TB HDD |
| **Network** | 1x 2.5GbE, WiFi 6E |
| **Power** | ~750W PSU |

**Homelab Role:** ML training, CUDA compute, heavy development, GPU passthrough host

---

### Dell Latitude 5430 Rugged (Travel Laptop)

| Spec | Value |
|------|-------|
| **CPU** | Intel Core i5-1135G7 |
| Cores/Threads | 4C / 8T |
| Base/Boost | 2.4 / 4.2 GHz |
| TDP | 28W |
| **GPU** | Intel Iris Xe (80 EU) |
| **RAM** | 32GB DDR4-3200 |
| **Storage** | 2TB NVMe PCIe Gen3 |
| **Network** | Intel AX210 (WiFi 6E), 1x GbE |
| **Display** | 14" FHD 400nit |
| **Rugged Rating** | MIL-STD-810H |
| **Battery** | 53.5 Whr |

**Homelab Role:** Mobile SSH terminal, portable dev environment, field diagnostics

---

## Tier 2: Mini PC Compute Nodes

### Beelink EQR6 (Primary Mini Server)

| Spec | Value |
|------|-------|
| **CPU** | AMD Ryzen 7 6800U |
| Cores/Threads | 8C / 16T |
| Base/Boost | 2.7 / 4.7 GHz |
| TDP | 15-28W |
| **GPU** | AMD Radeon 680M (12 CU) |
| **RAM** | 32GB LPDDR5-6400 |
| **Storage** | 1TB NVMe PCIe 4.0 |
| **Network** | 2x 2.5GbE, WiFi 6, BT 5.2 |
| **Ports** | 2x USB 3.2, USB-C, 2x HDMI |
| **Idle Power** | ~8W |
| **Load Power** | ~45W |

**Homelab Role:** Proxmox/Docker host, always-on services, dual-NIC for routing/firewall

---

### Beelink Mini PC (Secondary Mini Server)

| Spec | Value |
|------|-------|
| **CPU** | AMD Ryzen 5 6600U |
| Cores/Threads | 6C / 12T |
| Base/Boost | 2.9 / 4.5 GHz |
| TDP | 15-28W |
| **GPU** | AMD Radeon 660M (6 CU) |
| **RAM** | 24GB LPDDR5-6400 |
| **Storage** | 500GB NVMe PCIe 4.0 |
| **Network** | 2x 2.5GbE, WiFi 6, BT 5.2 |
| **Idle Power** | ~6W |
| **Load Power** | ~35W |

**Homelab Role:** Secondary Docker host, Home Assistant, media services

---

### KAMRUI Pinova P1

| Spec | Value |
|------|-------|
| **CPU** | AMD Ryzen 3 3300U |
| Cores/Threads | 4C / 8T |
| Base/Boost | 2.1 / 3.5 GHz |
| TDP | 15W |
| **GPU** | Radeon Vega 6 |
| **RAM** | 16GB DDR4 |
| **Storage** | 256GB NVMe |
| **Network** | 1x GbE, WiFi 5, BT |
| **Display** | Triple 4K support |
| **Idle Power** | ~5W |

**Homelab Role:** Lightweight containers, Pi-hole, DNS, reverse proxy

---

### KAMRUI Mini PC (Intel N97)

| Spec | Value |
|------|-------|
| **CPU** | Intel N97 (Alder Lake-N) |
| Cores/Threads | 4C / 4T (E-cores only) |
| Base/Boost | 1.0 / 3.6 GHz |
| TDP | 12W |
| **GPU** | Intel UHD Graphics |
| **RAM** | 16GB DDR4 |
| **Storage** | 256GB NVMe |
| **Network** | 1x GbE, WiFi, BT |
| **Idle Power** | ~4W |
| **Load Power** | ~15W |

**Homelab Role:** Ultra-low-power 24/7 services, monitoring, MQTT broker

---

## Tier 3: Edge AI & SBCs

### ASUS Tinker Edge R

| Spec | Value |
|------|-------|
| **SoC** | Rockchip RK3399Pro |
| **CPU** | 2x A72 + 4x A53 |
| Clock | 1.8 GHz / 1.4 GHz |
| **NPU** | 3.0 TOPS INT8 |
| **GPU** | Mali-T860 MP4 |
| **RAM** | 4GB LPDDR4 |
| **Storage** | eMMC + MicroSD |
| **Network** | 1x GbE |
| **Video** | 4K60 decode, 1080p60 encode |
| **Power** | ~10W |

**Homelab Role:** Edge AI inference, computer vision, dedicated NPU workloads

---

### NVIDIA Jetson Nano (P3450)

| Spec | Value |
|------|-------|
| **SoC** | Tegra X1 |
| **CPU** | 4x ARM Cortex-A57 |
| Clock | 1.43 GHz |
| **GPU** | 128 Maxwell CUDA cores |
| FP16 | 472 GFLOPS |
| **RAM** | 4GB LPDDR4 (25.6 GB/s) |
| **Storage** | MicroSD / NVMe (carrier) |
| **Network** | 1x GbE |
| **CSI** | 2x MIPI lanes |
| **Power** | 5W / 10W modes |

**Homelab Role:** CUDA inference, TensorRT, camera AI, robotics prototyping

---

### Raspberry Pi 4 Model B (x2)

| Spec | Value |
|------|-------|
| **SoC** | Broadcom BCM2711 |
| **CPU** | 4x Cortex-A72 @ 1.8 GHz |
| **GPU** | VideoCore VI |
| **RAM** | 2GB / 4GB / 8GB |
| **Storage** | MicroSD / USB SSD |
| **Network** | 1x GbE (USB 3.0 bus), WiFi 5, BT 5.0 |
| **GPIO** | 40-pin header |
| **Power** | 3-7W |

| Unit | Assignment |
|------|------------|
| Pi 4B #1 | Bed automation controller |
| Pi 4B #2 | Bedroom TV (Kodi/media) |

---

## Tier 4: Legacy Hardware

### HP Pavilion p6617c

| Spec | Value |
|------|-------|
| **CPU** | AMD Athlon II X4 630 |
| Cores/Threads | 4C / 4T |
| Clock | 2.8 GHz |
| TDP | 95W |
| **GPU** | Integrated (or discrete slot) |
| **RAM** | 8GB DDR3-1333 (upgradeable) |
| **Storage** | SATA II (upgrade to SSD) |
| **Network** | 1x GbE |
| **Power** | ~300W PSU |
| **Era** | ~2010 |

**Homelab Role:** NAS candidate, backup server, file shares, low-priority tasks

---

## Network Summary

| Device | LAN Ports | Speed | WiFi | Notes |
|--------|-----------|-------|------|-------|
| Aurora R15 | 1 | 2.5GbE | WiFi 6E | Primary workstation |
| Latitude 5430 | 1 | 1GbE | WiFi 6E (AX210) | Mobile |
| Beelink EQR6 | 2 | 2.5GbE | WiFi 6 | Router/firewall capable |
| Beelink 6600U | 2 | 2.5GbE | WiFi 6 | Dual-homed services |
| KAMRUI P1 | 1 | 1GbE | WiFi 5 | Standard |
| KAMRUI N97 | 1 | 1GbE | WiFi | Low-power |
| Tinker Edge R | 1 | 1GbE | - | Wired only |
| Jetson Nano | 1 | 1GbE | - | Wired only |
| Raspberry Pi 4B | 1 | 1GbE* | WiFi 5 | *Shared USB bus |
| HP p6617c | 1 | 1GbE | - | Legacy |

**Total Wired Ports:** 13 (need 16-port switch minimum)
**2.5GbE Devices:** 4 (Aurora, EQR6, Beelink 6600U)

---

## Power Budget (Estimated)

| Device | Idle | Typical | Max |
|--------|------|---------|-----|
| Aurora R15 | 80W | 250W | 600W |
| Latitude 5430 | 8W | 25W | 45W |
| Beelink EQR6 | 8W | 20W | 45W |
| Beelink 6600U | 6W | 15W | 35W |
| KAMRUI P1 | 5W | 12W | 25W |
| KAMRUI N97 | 4W | 8W | 15W |
| Tinker Edge R | 3W | 7W | 10W |
| Jetson Nano | 5W | 8W | 10W |
| Pi 4B (x2) | 6W | 10W | 14W |
| HP p6617c | 60W | 90W | 150W |
| **Total** | **185W** | **445W** | **949W** |

**24/7 Always-On (excl. Aurora/HP):** ~45W idle, ~100W typical

---

## Suggested Homelab Architecture

```
                    ┌─────────────────┐
                    │   Internet      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Router/Modem   │
                    └────────┬────────┘
                             │
              ┌──────────────▼──────────────┐
              │  Beelink EQR6 (OPNsense)    │
              │  WAN: eth0 | LAN: eth1      │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │  2.5GbE/1GbE Managed Switch │
              └──────────────┬──────────────┘
                             │
     ┌───────────┬───────────┼───────────┬───────────┐
     │           │           │           │           │
┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
│ Aurora  │ │ Beelink │ │ KAMRUI  │ │ Jetson  │ │  Pi 4B  │
│  R15    │ │ 6600U   │ │ N97/P1  │ │  Nano   │ │  (x2)   │
│ (Dev)   │ │(Docker) │ │(Infra)  │ │ (AI)    │ │ (IoT)   │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## Quick Reference: Compute Comparison

| Device | Geekbench 6 (est) | Use Case |
|--------|-------------------|----------|
| Ryzen 9 7900X | SC: 2800 / MC: 18000 | Heavy compute, ML training |
| Ryzen 7 6800U | SC: 2300 / MC: 9500 | VM host, containers |
| Ryzen 5 6600U | SC: 2200 / MC: 7500 | Docker services |
| i5-1135G7 | SC: 1800 / MC: 5500 | Mobile dev |
| Ryzen 3 3300U | SC: 1100 / MC: 3500 | Light services |
| Intel N97 | SC: 1000 / MC: 2800 | 24/7 low-power |
| Jetson Nano | SC: 250 / MC: 900 | Edge AI only |
| Pi 4B | SC: 350 / MC: 900 | IoT/automation |
