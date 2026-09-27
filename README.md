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

Phase 0 — Foundations (both of you, Day 1)

┌─────┬───────────────────────────────────────────────────┬───────┬────────────────────────────────────────────┐
│  #  │                       Skill                       │ Owner │                  Have it?                  │
├─────┼───────────────────────────────────────────────────┼───────┼────────────────────────────────────────────┤
│ 1   │ Git/GitHub (clone, branch, commit, push, PR)      │ Both  │ Check — needed to collaborate on this repo │
├─────┼───────────────────────────────────────────────────┼───────┼────────────────────────────────────────────┤
│ 2   │ Python basics (dicts, lists, functions, file I/O) │ Both  │ Have (Intro Python)                        │
├─────┼───────────────────────────────────────────────────┼───────┼────────────────────────────────────────────┤
│ 3   │ Reading/writing YAML                              │ Both  │ New, but 15 minutes                        │
├─────┼───────────────────────────────────────────────────┼───────┼────────────────────────────────────────────┤
│ 4   │ REST API concepts (GET/POST, JSON, status codes)  │ Both  │ You have this from NetOps Gateway          │
└─────┴───────────────────────────────────────────────────┴───────┴────────────────────────────────────────────┘

Phase 1 — Power domain (partner)

┌─────┬───────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────┐
│  #  │                                   Skill                                   │                  Have it?                  │
├─────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ 5   │ Ohm's law, P = VI, P = I²R                                                │ Have (Physics 2)                           │
├─────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ 6   │ Series/parallel circuit analysis                                          │ Have (Physics 2 lab)                       │
├─────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ 7   │ Kirchhoff's current/voltage laws                                          │ Have                                       │
├─────┼────
├─────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ 10  │ Energy vs. power (E = ∫P dt) for UPS runtime                              │ Have the math (Calc 2)                     │
├─────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ 11  │ AC power factor, real vs. apparent power (kW vs. kVA)                     │ New                                        │
├─────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ 12  │ Three-phase power                                                         │ New, small addition once #11 lands         │
├─────┼───────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────┤
│ 13  │ (stretch) Battery discharge as a first-order ODE, solved numerically in   │ Have the math (Diff Eq); new to apply it   │
│     │ Python                                                                    │ here                                       │
└─────┴───────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────┘

Phase 2 — Networking / CCNA foundation (you)

┌─────┬────────────────────────────────────────┬──────────┐
│  #  │                 Skill                  │ CCNA ch. │
├─────┼────────────────────────────────────────┼──────────┤
│ 14  │ OSI model & TCP/IP                     │ 3        │
├─────┼────────────────────────────────────────┼──────────┤
│ 15  │ Subnetting & VLSM                      │ 13–15    │
├─────┼────────────────────────────────────────┼──────────┤
│ 16  │ VLANs & trunking                       │ 16–18    │
├─────┼────────────────────────────────────────┼──────────┤
│ 17  │ Spanning Tree & EtherChannel           │ 20–23    │
├─────┼─────
│ 19  │ HSRP / FHRP                            │ 29       │
├─────┼────────────────────────────────────────┼──────────┤
│ 20  │ ACLs                                   │ 34–35    │
├─────┼────────────────────────────────────────┼──────────┤
│ 21  │ DHCP, NTP, SNMP, Syslog, SSH           │ 37–42    │
├─────┼────────────────────────────────────────┼──────────┤
│ 22  │ Building the topology in Packet Tracer │ —        │
└─────┴────────────────────────────────────────┴──────────┘

Phase 3 — Network automation & ACI (you)

┌─────┬──────────────────────────────────────────────────────────────────────────────┐
│  #  │                                    Skill                                     │
├─────┼──────────────────────────────────────────────────────────────────────────────┤
│ 23  │ Parsing Cisco configs in Python (regex, or ciscoconfparse)                   │
├─────┼──────────────────────────────────────────────────────────────────────────────┤
│ 24  │ Writing the golden-config diff logic (live config vs. golden_config.yaml)    │
├─────┼──────────────────────────────────────────────────────────────────────────────┤
│ 25  │ ACI fundamentals: tenant, VRF, BD, EPG, contract                             │
├─────┼──────────────────────────────────────────────────────────────────────────────┤
│ 26  │ Authenticating to APIC / DevNet ACI sandbox                                  │
├─────┼──────────────────────────────────────────────────────────────────────────────┤
│ 27  │ Mapping CCNA constructs to ACI constructs, and generating the blueprint YAML │
└─────┴──────
┌─────┬───────────────────────────────────────────────────────────────────┬───────────────────────────────────────┐
│  #  │                               Skill                               │                 Owner                 │
├─────┼───────────────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ 28  │ FastAPI (routes, dependencies, auth header)                       │ Both — already migrated in the repo   │
├─────┼───────────────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ 29  │ pytest (writing and running tests)                                │ Both                                  │
├─────┼───────────────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ 30  │ Designing the shared inventory.yaml schema together               │ Both                                  │
├─────┼───────────────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ 31  │ Cross-domain risk logic (network redundancy vs. power redundancy) │ Both — risk.py is the working example │
├─────┼───────────────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ 32  │ Azure basics (App Service, Key Vault) for the hybrid link         │ You (stretch)                         │
├─────┼───────────────────────────────────────────────────────────────────┼───────────────────────────────────────┤
│ 33  │ CI basics (GitHub Actions running pytest on push)                 │ Either (stretch)                      │
└─────┴───────────────────────────────────────────────────────────────────┴───────────────────────────────────────┘

Phase 5 — Close it out (both)

┌─────┬──────────────────────────────────────────────────────────────────────────────────────────────────┐
│  #  │                                              Skill                                               │
├─────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 34  │ Writing docs/README so status is always honest (done vs. planned)                                │
├─────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 35  │ A MOP-style change document (steps + rollback) if you add the deploy layer                       │
├─────┼──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 36  │ The consulting narrative: business problem → design → demo → value, for slides and the interview │
└─────┴──────────────────────────────────────────────────────────────────────────────────────────────────┘

## Authors

Zaheen Rahman (network/ACI side) + power/electrical engineering partner Anas Shah
