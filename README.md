# DC-Resilience-Twin/Model

**A small tool that maps a data center's network and its power together, then simulates
"what if this one thing breaks?"**

> **Status: brand new, nothing built yet.** This README is the plan. Roadmap checkboxes
> say what's actually done.

## Scope, on purpose

This project is built for exactly where we are right now, not for an ideal team:

- **Zaheen** is studying for the **CCNA** and interviewing for a Cisco Data Center
  Consulting internship — so the networking side stays at CCNA level (no ACI, no
  advanced SDN). It's meant to show CCNA fundamentals applied, not a whole new platform.
- **The power/electrical side** is a sophomore who's taken **Physics 2 (+ lab), Calc 2,
  Calc 3, Diff Eq, and intro Python** — so that side stays at "Ohm's law and basic
  redundancy," not full power-systems engineering.
- **Azure** is included because Zaheen is studying for **AZ-900 / AZ-104** — deploying
  this project is real, graded practice for that, not an add-on.

Everything past that (three-phase power, ACI's tenant/VRF/EPG model, ODE-based battery
modeling) is listed as **stretch**, clearly separate from the core build. Do the core
first. It's still a real, working project without any of the stretch items.

## What it actually does (core version)

1. Describe a small data center in one YAML file: which switches connect to which
   (network side), and which devices plug into which power feed (power side).
2. Turn that into a simple graph: devices are dots, network cables and power cables are
   both lines connecting them.
3. Pick something to "break" — a switch, a feed, a link.
4. For every other device, check two things: **does it still reach the network?** and
   **does it still have power?**
5. Report the interesting case: a device that looked fully backed up (two network paths,
   two power feeds) but loses *both* at once, because its two "backups" secretly shared
   the same failure point.
6. Draw a simple before/after picture of the network, colored by what survived.

That's the whole core project. No ACI, no live hardware, no three-phase math required.

## Architecture

```
data/topology.yaml ──► build a graph (NetworkX) ──► two kinds of connection:
                                                      network links + power links
                                                              │
                                    pick a node/link to remove, recheck connectivity
                                                              │
                                    ┌─────────────────────────┴──────────────┐
                                    ▼                                        ▼
                         resilience report (text)                 before/after picture
                         - what's still fine                       (color-coded graph)
                         - what's degraded
                         - what went fully down
                                    │
                                    ▼
                      hosted as a tiny web page on Azure App Service (F1, free tier)
```

## Who works on what (core scope)

| | Networking (Zaheen, CCNA-level) | Power (Anas Shah, EE, sophomore-level) |
|---|---|---|
| **Knowledge needed** | Basic topology (core/distribution/access or spine-leaf, from CCNA ch. 52), what redundancy means (two uplinks), reading/writing YAML | Ohm's law (`P = VI`), series/parallel circuits, what "two power feeds" means for redundancy (all from Physics 2) |
| **New but small** | Plain-Python graph basics: adjacency list, remove a node, BFS/DFS to check if it's still connected | Redundancy models in plain terms: two feeds (2N) vs. one feed with a spare (N+1) |
| **Owns in this repo** | `network_links` in the YAML, the graph-building code, the CCNA talking points for the demo | `power` section in the YAML, realistic wattage numbers, *and* the power-side logic: capacity checks after a failure, N/N+1/2N classification |
| **Cert tie-in** | CCNA: two-tier core/access design; the deliberate second uplink is a real-world talking point for STP/EtherChannel; `core1`/`core2` redundancy maps to HSRP/VRRP first-hop redundancy (not implemented — just talking points for the interview) | Not cert-tracked — this is Physics 2 / circuits coursework, not a certification |
| **Stretch (optional, do the core first)** | Map nodes to ACI concepts (tenant/VRF/EPG) for the interview story | Power factor, three-phase power, or an ODE-based battery-discharge model |


## Tools for the power/electrical side

**Core (need these to do the actual work):**

| Tool | Why | Cost |
|---|---|---|
| VS Code | Editing `topology.yaml` and any Python they touch | Free |
| Python 3 + `pip` | Same environment as the rest of the project — no separate tool needed | Free |
| Git / GitHub Desktop | Committing their part of the shared repo | Free |
| [Cisco Power Calculator](https://cpc.cloudapps.cisco.com/cpc/) | Real device wattages instead of placeholders | Free |
| A device datasheet (search "[model] power specifications" on cisco.com) | Backs up the Power Calculator numbers with actual PSU ratings | Free |

That's everything required for the core scope: real wattages, understanding N/N+1/2N
redundancy, writing the `power` section of the YAML. No specialized software needed.

**Recommended, not required (builds intuition):**

| Tool | Why |
|---|---|
| Excel / Google Sheets | Sum rack wattages and feed loads by hand first, before encoding into YAML — catches mistakes early |


## Azure (AZ-900 / AZ-104 practice, built in, not bolted on)

The whole point of including Azure here is that deploying this *is* AZ-900/104 material,
not separate homework:

| Step | What you're actually practicing |
|---|---|
| Create a resource group | AZ-900: how Azure organizes resources |
| Deploy the report as a tiny web page on **Azure App Service (F1, free tier)** | AZ-900: PaaS vs. IaaS vs. SaaS — App Service is PaaS, no server to manage |
| Store `topology.yaml` in **Azure Blob Storage** instead of only locally | AZ-104: storage accounts, containers, basic access |
| Put any secret (if one ever exists) in **Azure Key Vault**, not in code | AZ-104: secrets management |
| Check the app's logs in **Azure Monitor / Log Stream** | AZ-104: monitoring basics |

One app service, resource group, storage account, front end is not needed

## Data model (planned: `data/topology.yaml`, will connect with power and network devices together)

```yaml
devices:
  - {name: core1, role: core}
  - {name: acc1,  role: access}
  - {name: srv1,  role: server}

network_links:
  - [acc1, core1]
  - [acc1, core2]        # the second uplink that's supposed to be a backup

power:
  feeds:
    A: {capacity_kw: 8.0}
    B: {capacity_kw: 8.0}
  psu_links:
    - {device: acc1, psu: A, feed: A}
    - {device: acc1, psu: B, feed: B}
```

Simple on purpose: a handful of devices, two feeds, a few links. Prove the idea works
small before making it bigger.

## Getting started (planned)

**Requirements:** Python 3.10+, `networkx`, `matplotlib`, `pyyaml`, `pytest`

```bash
git clone <repo-url>
cd dc-resilience-twin
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**Run a simulation** *(once implemented)*
```bash
python -m twin simulate --topology data/topology.yaml --remove feedA
python -m twin simulate --topology data/topology.yaml --remove core1 --draw
```

Day 1 — Environment + topology skeleton
- Repo scaffold: venv, requirements.txt (matplotlib, pyyaml, pytest) — Zaheen (✅)
- Learn plain-Python graph basics: adjacency list, remove a node, BFS/DFS reachability check — Zaheen (✅)
- Pull real wattages for 5-8 sample devices (Cisco Power Calculator + datasheets) — Anas Shah (✅)

Day 2 — Finish data/topology.yaml
- Write network_links for a 5-8 device topology, with one access switch deliberately given two uplinks ("backed up") — Zaheen (✅)
- Write the power section: feeds A/B, capacity_kw, psu_links, N/N+1/2N — Anas Shah (✅)

**Day 3 — Build the graph**
- [ ]Merge both sections into one working YAML file — both 
- [ ] Parse the YAML into a plain adjacency-list graph with two edge types (network
      link, power link), same node set — *Zaheen* (✅)
- [ ] Quick script/test that loads it and prints node/edge counts — *Anas Shah*
- [ ] Map out Cisco Packet Tracer (devices) connected and simulate their errors through their failures (cyberattack, natural disaster, shutdown, etc). 

**Day 4 — Failure simulation day to test a specific failure situation, maybe also create an incident report**
- [ ] Remove a node or link, recheck the network layer: still has a path to the internet
      node? — *Zaheen*
- [ ] Recheck the power layer: do the surviving feeds still cover the device's load
      (still N/N+1/2N, or under-provisioned now)? — *Anas Shah*

**Day 5 — Resilience report + the hidden SPOF**
- [ ] Classify each device's network status: fine / degraded / down by reachability —
      *Zaheen*
- [ ] Classify each device's power status: fine / degraded / down by feed-capacity
      margin — *Anas Shah*
- [ ] Combine both into one overall status per device — *Zaheen + Anas Shah*
- [ ] Seed one deliberate hidden single point of failure in the sample data (Anas Shah
      picks a power-side one — e.g. two feeds sharing an upstream circuit; Zaheen picks a
      network-side one — e.g. two uplinks terminating on the same core switch) — *Zaheen +
      Anas Shah*
- [ ] Confirm the tool catches it: Zaheen writes the network-side test, Anas Shah writes
      the power-side test — *Zaheen + Anas Shah*

**Day 6 — Visualization**
- [ ] Simple manual layout (e.g. position by role: core/distribution/access as rows) since
      there's no graph library to auto-lay-out nodes — *Zaheen*
- [ ] Status-to-color mapping (fine/degraded/down → green/yellow/red) — *Anas Shah*
- [ ] Before/after picture with matplotlib, wiring the layout and colors together —
      *Zaheen, Anas Shah*

**Day 7 — Azure deployment (AZ-900/104 practice)**
- [ ] Create a resource group → App Service (F1 free tier) → deploy the report page, "mini dashboard" creation as well—
      *Zaheen*
- [ ] Confirm logs in Azure Monitor / Log Stream — *Zaheen*
- [ ] Sanity-check the deployed report: do the power numbers and the seeded SPOF match
      what went into the YAML? — *Anas Shah*
- [ ] Tick off remaining checkboxes, dry-run the demo, jot CCNA/AZ-900 talking points for
      the interview — e.g. the second uplink is normally handled by STP/EtherChannel in
      real L2 designs, and `core1`/`core2` would normally run HSRP/VRRP for first-hop
      redundancy; explain why this twin models both as plain parallel paths instead —
      *Zaheen*


## Roadmap

**Core (build this first)**
- [ ] Learn NetworkX basics: build a graph, remove a node, check connectivity
- [ ] Write `data/topology.yaml` for a small (5 to 8 device) sample network
- [ ] Build the graph from the YAML: network layer + power layer, same nodes
- [ ] Failure simulation: remove one node/link, recheck each layer
- [ ] Resilience report: fine / degraded / down
- [ ] Seed one deliberate hidden single point of failure in the sample data, and confirm
      the tool catches it
- [ ] Before/after picture with matplotlib
- [ ] Deploy the report as a simple page on Azure App Service (F1 tier)

**Stretch (only after core works)**
- [ ] Store `topology.yaml` in Azure Blob Storage instead of locally
- [ ] Map network nodes to ACI concepts (tenant/VRF/EPG) for the interview story
- [ ] Power factor / three-phase power in the power model
- [ ] ODE-based UPS/battery discharge model
- [ ] Thin FastAPI wrapper: `POST /simulate/{target}`

## Limitations

- A simulation over a small, hand-written topology — not live telemetry from real
  hardware.
- Connectivity checks are structural (is there still a path?), not a full physical
  power-flow or routing-protocol model.
- Deliberately small scope: this proves the idea on a handful of devices, not a full
  data center.

## Related work

**PowerOps Gateway** (`datacenter-aci-blueprint` repo) — a separate, already-in-progress
project: a FastAPI health/compliance API over a similar shared network+power model. That
project asks "is this compliant right now?"; this one asks "what breaks if this fails?"
Built and delivered separately.

## Secrets

No credentials needed for the core, local version. Once anything is hosted on Azure,
connection strings and any keys go in **Azure Key Vault** or environment variables —
never in `data/topology.yaml` or committed code.

## Authors

Zaheen Rahman (networking + Azure side) + power/electrical engineering partner Anas Shah
