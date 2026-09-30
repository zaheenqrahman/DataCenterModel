# Recreation of Data Center w/ Incident Response (Automatied)

**A model/reflection that maps a data center's network and its power together, then simulates
"what if this one thing breaks?"**




## What it actually does (core version)

1. Describe a small data center in one merged power and network
   YAML file: which switches connect to which
   (network side), and which devices plug into which power feed (power side).
3. Turn that into a simple graph: devices are dots, network cables and power cables are
   both lines connecting them. Map it out physically in Packet Tracer + draw.io.
4. Pick something to "break" — a switch, a feed, a link, even all of these.
5. For every other device, check two things: **does it still reach the network?** and
   **does it still have power?**, CHECK BOTH. 
6. Report the interesting case: a device that looked fully backed up (two network paths,
   two power feeds) but loses *both* at once, because its two "backups" secretly shared
   the same failure point.
7. Draw a simple before/after picture of the network, colored by what survived and what did not.

No hardware, but connects directly to what an ACI is. 

## Architecture

```
data/topology.yaml ──► build a graph ──► two kinds of connection:
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
                      hosted as a tiny web page on Azure App Service (F1, free tier) using FastAPI or Flask
```

## Who works on what (core scope)
|
| **New but small** | Plain-Python graph basics: adjacency list, remove a node, BFS/DFS to check if it's still connected | Redundancy models in plain terms: two feeds (2N) vs. one feed with a spare (N+1) |
| **Owns in this repo** | `network_links` in the YAML, the graph-building code, the CCNA talking points for the demo | `power` section in the YAML, realistic wattage numbers, *and* the power-side logic: capacity checks after a failure, N/N+1/2N classification |
| **Cert tie-in** | CCNA: two-tier core/access design; the deliberate second uplink is a real-world talking point for STP/EtherChannel; `core1`/`core2` redundancy maps to HSRP/VRRP first-hop redundancy (not implemented — just talking points for the interview) | Not cert-tracked — this is Physics 2 / circuits coursework, not a certification |
| **Stretch (optional, do the core first)** | Map nodes to ACI concepts (tenant/VRF/EPG) for the interview story | Power factor, three-phase power, or an ODE-based battery-discharge model |


Tools: 

**Core (need these to do the actual work):**

| Tool | Why | Cost |
|---|---|---|
| VS Code | Editing `topology.yaml` and any Python they touch | Free |
| Python 3 + `pip` | Same environment as the rest of the project — no separate tool needed | Free |
| Git / GitHub Desktop | Committing their part of the shared repo | Free |
| [Cisco Power Calculator](https://cpc.cloudapps.cisco.com/cpc/) | Real device wattages instead of placeholders | Free |
| A device datasheet (search "[model] power specifications" on cisco.com) | Backs up the Power Calculator numbers with actual PSU ratings | Free |
writing the `power` section of the YAML

**To store data**

| Tool | Why |
|---|---|
| Excel / Google Sheets | Sum rack wattages and feed loads by hand first, before encoding into YAML — catches mistakes early |



| Azure |
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
small before making it bigger. Then begin to make it bigger as day 4-7 progresses. 

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

Day 1 — Environment settling in, practice and skeleton of YAML and Python

Repo scaffold: venv, requirements.txt (matplotlib, pyyaml, pytest) — Zaheen (✅)
Learn plain-Python graph basics: adjacency list, remove a node, BFS/DFS reachability check — Zaheen (✅)
Pull real wattages for 5-8 sample devices (Cisco Power Calculator + datasheets) — Anas Shah (✅)

Day 2 — Finish data/topology.yaml

Write network_links for a 5-8 device topology, with one access switch deliberately given two uplinks ("backed up") — Zaheen (✅)
Write the power section: feeds A/B, capacity_kw, psu_links, N/N+1/2N — Anas Shah (✅)

Day 3 — Build the graph and physical network topologies and practice breaking it virtually

[ ✅]Add IP/subnet per device for access-layer devices/servers in Packet Tracer; mark each network_link as trunk or access — Zaheen

[✅] Merge both sections into one working YAML file — both

[ ✅]Parse the YAML into a plain adjacency-list graph with two edge types (network link, power link), same node set — Zaheen (✅)

[ ✅] Quick script/test that loads it and prints node/edge counts — Anas Shah 

Day 4 — Failure simulation day to test a specific failure situation, maybe also create an incident report

 Remove a node or link, recheck the network layer: still has a path to the internet node? Also create the VLANS in cisco packet tracer update the switches if needed— Zaheen
 
 Recheck the power layer: do the surviving feeds still cover the device's load (still N/N+1/2N, or under-provisioned now)? — Anas Shah
 
 Model STP link state on acc1's two uplinks (one forwarding, one blocking); when the forwarding one fails, flip the blocked one to forwarding — Zaheen
 
 Model FHRP on core1/core2: active/standby with a priority value and a shared virtual gateway IP; standby takes over when active fails — Zaheen

Day 5 — Resilience report + the hidden SPOF (single point of failure)

 Classify each device's network status: fine / degraded / down by reachability — Zaheen
 
 Classify each device's power status: fine / degraded / down by feed-capacity margin — Anas Shah
 
 Combine both into one overall status per device — Zaheen + Anas Shah
 
 Seed one deliberate hidden single point of failure in the sample data (Anas Shah picks a power-side one — e.g. two feeds sharing an upstream circuit; Zaheen picks a network-side one — e.g. two uplinks terminating on the same core switch) — Zaheen + Anas Shah
 
 Confirm the tool catches it: Zaheen writes the network-side test, Anas Shah writes the power-side test — Zaheen + Anas Shah

Day 6 — Visualization/Mapping out

 Simple manual layout (e.g. position by role: core/distribution/access as rows) since there's no graph library to auto-lay-out nodes — Zaheen
 Status-to-color mapping (fine/degraded/down → green/yellow/red) — Anas Shah
 Show STP link state in the picture too (e.g. dashed line for the currently-blocked uplink) — Zaheen
 Before/after picture with matplotlib, wiring the layout and colors together — Zaheen, Anas Shah
 Download Terraform, learn the layout, then provision it to  the azure app service instead hand doing it in Portal - Zaheen

Day 7 — Azure deployment and FastAPI connections

 Create a resource group → App Service (F1 free tier) → deploy the report page, "mini dashboard" creation as well— Zaheen
 
 Confirm logs in Azure Monitor / Log Stream — Zaheen
 
 Sanity-check the deployed report: do the power numbers and the seeded SPOF match what went into the YAML? — Anas Shah
 
 Tick off remaining checkboxes, dry-run the demo, jot CCNA/AZ-104+900 talking points for the interview — e.g. walk through the STP failover and FHRP failover you actually built, not just describe them — Zaheen



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

**PowerOps Gateway** (`datacenter-aci-blueprint` repo) — a separate, finished
project: a FastAPI health/compliance API over a similar shared network+power model. That
project asks "is this compliant right now?"; this one asks "what breaks if this fails?"
Built / delivered seperate..


