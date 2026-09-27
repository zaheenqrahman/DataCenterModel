# datacenter-aci-blueprint (PowerOps Gateway)

A **network + power** health and compliance API for a small Cisco data center lab, built with
FastAPI. Two domains, one shared model: the network side (fabric, golden-config, CCNA/ACI
mapping) and the power side (feeds, PDUs, redundancy risk) both read/write
`data/inventory.yaml`, so a finding on one side can be checked against the other — for
example, a device with network-level redundancy that still has a single power point of
failure.

**Headline check:** `/risk/scan` maps every device's PSU A/B to a power feed and flags
network-redundant devices that still share a single power point of failure.

## Who owns what

| Domain | Owner | Covers |
|---|---|---|
| **Power & electrical** | Anas(EE student) | Feed/UPS capacity, PDU telemetry model, rack power budget, redundancy math (`gateway/risk.py`, `power_sim/`, `data/inventory.yaml` wattages) |
| **Network / data center fabric** | Zaheen | CCNA baseline lab, fabric driver, golden-config compliance, CCNA→ACI construct mapping, Azure hybrid link |

`data/inventory.yaml` is the handoff point between the two — both sides edit it.

## Status (honest)

| Piece | State |
|---|---|
| Power/redundancy risk scan | Working, driven by `data/inventory.yaml` |
| PDU/UPS telemetry | **Simulated** (`power_sim/`), no real hardware |
| API framework | FastAPI + uvicorn (migrated from an earlier Flask version) |
| Fabric driver (NX-API/RESTCONF) | Not started (TODO) |
| Golden-config compliance engine | Template only (`golden/golden_config.yaml`), no comparison logic yet |
| CCNA baseline lab (Packet Tracer) | Not started |
| CCNA → ACI construct mapping | Not started (see below) |
| Azure hybrid link | Not started (TODO) |

Wattages in the inventory are placeholders until replaced with Cisco datasheet / Cisco Power
Calculator values.

## Architecture

```
                 ┌────────────────────┐
                 │ data/inventory.yaml│  ← shared model (both roles edit)
                 └─────────┬──────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                      ▼
  Power domain                          Network domain
  gateway/risk.py                       golden/golden_config.yaml
  power_sim/pdu_api.py (simulated PDU)  fabric driver (NX-API/RESTCONF) [TODO]
                                        CCNA lab → assessor → ACI mapping [TODO]
        │                                      │
        └──────────────┬───────────────────────┘
                        ▼
                 FastAPI app (application.py)
           /power/racks  /power/feeds  /risk/scan
           /fabric/devices  /fabric/devices/{name}/compliance  [planned]
```

## Networking side: CCNA baseline → ACI mapping (planned)

The network half of this project builds a traditional CCNA-level data center network,
checks its config against `golden/golden_config.yaml`, and maps it to Cisco ACI constructs —
the same way a real migration assessment would.

| Traditional network | ACI equivalent |
|---|---|
| VLAN | EPG (with a Bridge Domain) |
| SVI (gateway IP) | Bridge Domain subnet |
| VRF / global routing table | VRF |
| ACL between VLANs | Contract + filter |
| OSPF to the outside | L3Out |
| STP, EtherChannel, HSRP | Handled by the fabric (spine-leaf, vPC, anycast gateway) |
| Per-switch CLI | APIC policy (REST / GUI) |

| CCNA 200-301 domain | Where it lands in this project |
|---|---|
| Network Fundamentals | Topology, subnetting/VLSM plan |
| Network Access | VLANs, trunks, STP, EtherChannel |
| IP Connectivity | OSPF, static routes |
| IP Services | DHCP, NTP, SNMP, Syslog (already stubbed in `golden_config.yaml`) |
| Security Fundamentals | ACLs, port security, SSH |
| Automation and Programmability | Fabric driver, golden-config diff, ACI blueprint YAML |

The ACI comparison step will use the read-only Cisco DevNet ACI Always-On sandbox — no write
access assumed.

## Endpoints (all except `/` need header `X-API-Token: $GATEWAY_TOKEN`)

| Endpoint | Purpose | Status |
|---|---|---|
| `GET /` | Health | Working |
| `GET /power/racks` | Typical/peak kW per rack | Working |
| `GET /power/feeds` | Load per feed | Working |
| `GET /risk/scan` | Redundancy and capacity findings | Working |
| `GET /fabric/devices` | Device inventory from the fabric | Planned |
| `GET /fabric/devices/{name}/compliance` | Compare live config to `golden_config.yaml` | Planned |

## Run

```
py -m pip install -r requirements.txt
set GATEWAY_TOKEN=devtoken
uvicorn application:app --reload
py -m pytest tests -v
```

Interactive API docs (Swagger UI) are served at `/docs`. The simulated PDU API runs
separately: `uvicorn power_sim.pdu_api:app --port 5001`.

## Layout

`application.py` API · `gateway/risk.py` power/redundancy checks · `power_sim/` mock PDU API
· `golden/` fabric golden config · `data/` shared inventory (network + power) · `tests/` ·
`docs/`

## Secrets

Never commit credentials. `GATEWAY_TOKEN` and any future APIC/Azure credentials go in
environment variables or a local `.env` (already in `.gitignore`), never in
`data/inventory.yaml` or code.

## Authors

Zaheen Rahman (network/ACI side) + power/electrical engineering partner Anas Shah
