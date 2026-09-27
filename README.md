# datacenter-aci-blueprint

**Legacy-to-ACI Migration Assessment** — build a traditional three-tier data center network, assess its configuration with Python, and map it to a Cisco ACI policy design.

> **Status: in progress.** Items below are marked `[ ]` (planned) or `[x]` (done). Update this as the project moves.

---

## The problem

A client runs a traditional data center network: VLANs, trunks, STP, OSPF, ACLs, and per-switch CLI configuration. They want to move to Cisco ACI, but first they need to know *what they have* and *what it becomes* in ACI. Doing this by hand across many devices is slow and error-prone.

## What this project does

1. **Builds** a traditional core / distribution / access network in Cisco Packet Tracer using CCNA-level features.
2. **Assesses** the exported device configs with Python and reports an inventory plus findings.
3. **Maps** each traditional construct to its ACI equivalent and writes the proposed design as a YAML blueprint.
4. **Checks** the blueprint's structure against a real APIC (read-only) using the Cisco DevNet ACI sandbox.

```
Packet Tracer topology ──► exported configs ──► Python assessor ──► findings report
                                                       │
                                                       ▼
                                             ACI blueprint (YAML)
                                                       │
                                                       ▼
                                     read-only comparison with APIC sandbox
```

## Traditional → ACI mapping

| Traditional network | ACI equivalent |
|---|---|
| VLAN | EPG (with a Bridge Domain) |
| SVI (gateway IP) | Bridge Domain subnet |
| VRF / global routing table | VRF |
| ACL between VLANs | Contract + filter |
| OSPF to the outside | L3Out |
| STP, EtherChannel, HSRP | Handled by the fabric (spine-leaf, vPC, anycast gateway) |
| Per-switch CLI | APIC policy (REST / GUI) |

## CCNA coverage

| CCNA 200-301 domain | Where it appears |
|---|---|
| Network Fundamentals | Three-tier topology, cabling, subnetting plan with VLSM |
| Network Access | VLANs, trunks, STP, EtherChannel |
| IP Connectivity | OSPF, static routes, inter-VLAN routing |
| IP Services | DHCP, NTP, NAT, SNMP, Syslog |
| Security Fundamentals | ACLs, port security, DHCP snooping, SSH |
| Automation and Programmability | Python config parser, YAML, JSON, REST calls to APIC |

## Repository layout (planned)

```
datacenter-aci-blueprint/
├── README.md
├── topology/          # Packet Tracer file, diagram, addressing + VLAN plan
├── configs/           # exported running-configs, one file per device
├── assessor/          # Python parser and findings rules
├── blueprint/         # generated ACI blueprint YAML
├── apic/              # read-only APIC sandbox client and comparison
├── reports/           # sample findings report
└── docs/              # design notes, slides
```

## Findings the assessor will report (planned)

- ACL that permits any traffic between tiers
- VLAN with no gateway (SVI) defined
- No STP root explicitly configured
- SSH not enabled / Telnet allowed on VTY lines
- No NTP or Syslog server configured
- Trunk allowing all VLANs
- OSPF interface not passive where it should be

## Getting started

**Requirements**
- Python 3.10+
- Cisco Packet Tracer (to open the topology)
- A Cisco DevNet account for the ACI sandbox (read-only part)

**Setup**
```bash
git clone <repo-url>
cd datacenter-aci-blueprint
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**Run the assessor** *(once implemented)*
```bash
python -m assessor configs/ --report reports/findings.md
python -m assessor configs/ --blueprint blueprint/aci_blueprint.yaml
```

**Secrets:** never commit credentials. Sandbox credentials go in environment variables (`APIC_URL`, `APIC_USER`, `APIC_PASSWORD`) or a local `.env` file that is listed in `.gitignore`.

## Roadmap

- [ ] Learn ACI basics (tenant, VRF, BD, EPG, contract)
- [ ] Addressing and VLAN plan
- [ ] Packet Tracer topology: VLANs, trunks, inter-VLAN routing
- [ ] OSPF, HSRP, EtherChannel, STP
- [ ] ACLs, DHCP, NTP, Syslog, SSH, port security
- [ ] Export configs
- [ ] Python parser and findings report
- [ ] ACI blueprint YAML generator
- [ ] Read-only APIC sandbox comparison
- [ ] Slides and demo rehearsal

## Limitations

- The traditional network is a Packet Tracer simulation, not production hardware.
- The APIC sandbox is used **read-only**; the tool does not push configuration.
- The mapping covers the common constructs listed above, not every ACI feature.

## Related work

**NetOps Gateway** — a separate project: a Flask REST API over the Cisco Meraki API for network health and compliance checks. This project is the design and migration side; NetOps Gateway is the monitoring side.

## Author

Zaheen Rahman
