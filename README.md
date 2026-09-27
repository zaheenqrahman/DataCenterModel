# dc-resilience-twin

**A small tool that maps a data center's network and its power together, then simulates
"what if this one thing breaks?"**

> **Status: brand new, nothing built yet.** This README is the plan. Roadmap checkboxes
> say what's actually done.

## Scope, on purpose

This project is built for exactly where we are right now, not for an ideal team:

- **Zaheen** is studying for the **CCNA** and interviewing for a Cisco Data Center
  Consulting internship — so the networking side stays at CCNA level (no ACI, no
  advanced SDN). It's meant to show CCNA fundamentals applied, not a whole new platform.
- **Anas Shah** is doing the power/electrical side, a sophomore who's taken **Physics 2
  (+ lab), Calc 2, Calc 3, Diff Eq, and intro Python** — so that side stays at "Ohm's law
  and basic redundancy," not full power-syst
- **Azure** is included because Zaheen is studying for **AZ-900 / AZ-104** — deploying
  this project is real, graded practice for that, not an add-on.

Everything past that (three-phase power, ACI's tenant/VRF/EPG model, ODE-based battery
modeling) is listed as **stretch**, clearly  Do the core
first. It's still a real, working project without any of the stretch items.

## What it actually does (core version)

1. Describe a small data center in one YAML file: which switches connect to which
   (network side), and which devices plug inde).
2. Turn that into a simple graph: devices are dots, network cables and power cables are
   both lines connecting them.
3. Pick something to "break" — a switch, a f
4. For every other device, check two things: **does it still reach the network?** and
   **does it still have power?**
5. Report the interesting case: a device that looked fully backed up (two network paths,
   two power feeds) but loses *both* at onceecretly shared
   the same failure point.
6. Draw a simple before/after picture of the network, colored by what survived.

That's the whole core project. No ACI, no live hardware, no three-phase math required.

## Architecture

data/topology.yaml ──► build a graph (NetworkX) ──► two kinds of connection:
                                            er links
                                                              │
                                    pick a node/link to remove, recheck connectivity

                                    ┌─────────────────────────┴──────────────┐
                                    ▼                                        ▼
                         resilience report (text)                 before/after picture
                         - what's still fine                       (color-coded graph)
                         - what's degraded
                         - what went fully d
                                    │
                                    ▼
                      hosted as a tiny web p free tier)

## Who works on what (core scope)


## Who works on what (core scope)

| | Networking (Zaheen, CCNA-level) | Power el) |
|---|---|---|
| **Knowledge needed** | Basic topology (core/distribution/access or spine-leaf, from CCNA ch. 52), what redundancy means (two uplinks), reading/writing YAML | Ohm's law (`P = VI`), series/parallel circuits, what "two power feeds" means for redundancy (all from Physics 2) |
| **New but small** | NetworkX basics: build a graph, remove a node, check if it's still connected | Redundancy models in plain terms: two feeds (2N) vs. one feed with a spare (N+1) |
| **Owns in this repo** | `network_links` in the YAML, the graph-building code, the CCNA talking points for the demo | `power` section in the YAML (feeds, which device plugs into which), realistic wattage numbers |
| **Stretch (optional, do the core first)** | Map nodes to ACI concepts (tenant/VRF/EPG) for the interview story | Power factor, three-phase power, or an ODE-based battery-discharge model |

## Tools for Anas Shah (power/electrical sid

**Core (need these to do the actual work):**

| Tool | Why | Cost |
|---|---|---|
| VS Code | Editing `topology.yaml` and any Python they touch | Free |
| Python 3 + `pip` | Same environment as the rest of the project — no separate tool needed | Free |
| Git / GitHub Desktop | Committing their part of the shared repo | Free |
| [Cisco Power Calculator](https://cpc.cloudapps.cisco.com/cpc/) | Real device wattages instead of placeholders | Free |
| A device datasheet (search "[model] power specifications" on cisco.com) | Backs up the Power Calculator numbers with actual PSU ratings | Free |

That's everything required for the core scopng N/N+1/2N
redundancy, writing the `power` section of the YAML. No specialized software needed.

**Recommended, not required (builds intuition):**

| Tool | Why |
|---|---|
| [Falstad Circuit Simulator](https://www.falstad.com/circuit/) (browser, free) | See series/parallel circuits and
Kirchhoff's laws animate, instead of only co
| Excel / Google Sheets | Sum rack wattages and feed loads by hand first, before encoding into YAML — catches mistakes early |

**Only needed for the stretch goals:**

| Tool | For |
|---|---|
| [LTspice](https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html) (free) | Actually simulating the UPS/battery discharge circuit instead of only solving the ODE symbolically |
| `scipy.integrate.solve_ivp` (`pip install scipy`) | Solving the battery-discharge ODE numerically — no new tool,
just a library, keeps everything in Python |

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

This is deliberately small — one App Service, one storage account, nothing that costs
money on the free tier.

## Data model (planned: `data/topology.yaml`)

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

Simple on purpose: a handful of devices, two feeds, a few links. Prove the idea works
small before making it bigger.

Getting started (planned)

Requirements: Python 3.10+, networkx, matplotlib, pyyaml, pytest

git clone <repo-url>
cd dc-resilience-twin
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

Run a simulation (once implemented)
python -m twin simulate --topology data/topology.yaml --remove feedA
python -m twin simulate --topology data/topology.yaml --remove core1 --draw

Roadmap

Core, as a 7-day build plan (who's doing what)

Day 1 — Environment + topology skeleton
- [ ] Repo scaffold: venv, requirements.txt (networkx, matplotlib, pyyaml, pytest) — Zaheen
- [ ] Learn NetworkX basics: build a graph, remove a node, check connectivity — Zaheen
- [ ] Pull real wattages for 5-8 sample devi datasheets) — Anas Shah

Day 2 — Finish data/topology.yaml
- [ ] Write network_links for a 5-8 device topology, with one access switch deliberately
  given two uplinks ("backed up") — Zaheen
- [ ] Write the power section: feeds A/B, capacity_kw, psu_links, and whether each
  device is N, N+1, or 2N — Anas Shah
- [ ] Merge both sections into one working YAML file — Zaheen + Anas Shah

Day 3 — Build the graph
- [ ] Parse the YAML into a NetworkX graph with two edge types (network link, power
  link), same node set — Zaheen
- [ ] Quick script/test that loads it and prn

Day 4 — Failure simulation
- [ ] Remove a node or link, recheck each laa network path?
  still has power? — Zaheen

Day 5 — Resilience report + the hidden SPOF
- [ ] Classify every device as fine / degraded / down after a failure — Zaheen
- [ ] Seed one deliberate hidden single point of failure in the sample data (Anas Shah
  picks a power-side one — e.g. two feeds shheen picks a
  network-side one — e.g. two uplinks terminating on the same core switch) — Zaheen +
  Anas Shah
- [ ] Confirm the tool catches it with a tes

Day 6 — Visualization
- [ ] Before/after picture with matplotlib, color-coded by fine/degraded/down — Zaheen

Day 7 — Azure deployment (AZ-900/104 practice)
- [ ] Create a resource group → App Service (F1 free tier) → deploy the report page —
  Zaheen
- [ ] Confirm logs in Azure Monitor / Log St
- [ ] Tick off remaining checkboxes, dry-run the demo, jot CCNA/AZ-900 talking points for
  the interview — Zaheen

Stretch (only after core works)
- [ ] Store topology.yaml in Azure Blob Stor
- [ ] Map network nodes to ACI concepts (tenant/VRF/EPG) for the interview story
- [ ] Power factor / three-phase power in the power model
- [ ] ODE-based UPS/battery discharge model
- [ ] Thin FastAPI wrapper: POST /simulate/{target}

Limitations

- A simulation over a small, hand-written topology — not live telemetry from real
  hardware.
- Connectivity checks are structural (is there still a path?), not a full physical
  power-flow or routing-protocol model.
- Deliberately small scope: this proves the idea on a handful of devices, not a full
  data center.
rate, already-in-progress
project: a FastAPI health/compliance API over a similar shared network+power model. That
project asks "is this compliant right now?"; this one asks "what breaks if this fails?"
Built and delivered separately.

Secrets

No credentials needed for the core, local ved on Azure,
connection strings and any keys go in Azure Key Vault or environment variables —
never in data/topology.yaml or committed cod

Authors

Zaheen Rahman (networking + Azure side) + Anas Shah (power/electrical side, sophomore)
