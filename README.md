# dc-resilience-twin

**A network + power resilience simulator for a small data center — model it as one graph,
break it on purpose if something happens like a cyber attack, natural disaster, and see what actually survives.**

> **Status: brand new, nothing built yet.** This README describes the design. Everything
> below is a plan until the roadmap checkboxes say otherwise.

## Why this project, and not another health-check API

It's easy to keep building the same shape of project: pull some state, run rule checks,
return a findings list as JSON. That's useful, but it only ever answers *"is this
compliant right now?"* This project asks a different question instead:

> **"If this one thing fails, what actually goes down — and did we already have a hidden
> single point of failure we didn't know about?"**

A device can look network-redundant (two uplinks) and power-redundant (two PSUs)
separately, and still share one hidden common failure point — the same rack PDU, the same
spine switch, the same feed — that only shows up once the network graph and the power
graph are modeled *together* and something is actually removed from both at once. That's
the insight this project is built to surface.

## The idea, in one picture

```
Nodes:  spine1, spine2, leaf1, leaf2, srv1, srv2, feedA, feedB, pdu1, pdu2...
Edges:  network links   (leaf1 —— spine1, leaf1 —— spine2, ...)
        power links      (leaf1 —— PSU-A —— feedA, leaf1 —— PSU-B —— feedB, ...)

Simulate:  "remove feedA"   or   "remove spine1"   or   "remove pdu1"

For every surviving device, check:
  - network reachability to the core   (graph connectivity, network edges only)
  - power delivery                     (graph connectivity, power edges only)

Report:  which devices lost BOTH at once — the real single point of failure —
         vs. devices that lost only one and are still limping along fine.
```

## Architecture

```
data/topology.yaml ──► graph builder (NetworkX) ──► two-layer graph
                                                       (network edges + power edges,
                                                        same node set)
                                                              │
                                             failure simulation engine
                                        (remove a node/edge, re-check connectivity
                                         on each layer independently)
                                                              │
                                    ┌─────────────────────────┴─────────────────────┐
                                    ▼                                               ▼
                         resilience report (text/JSON)                topology visualization
                         - devices that lost both layers               (before/after, color-coded
                         - resilience score per scenario                 by what's still alive)
```

An optional thin FastAPI layer can expose `POST /simulate/{node}` later, but the core
deliverable is the graph model and the simulation engine, not an API.

## Who works on what

| | Electrical Engineering | Computer Science / Networking |
|---|---|---|
| **Owns in this repo** | Power subgraph data: feeds, PDUs, UPS, dual-PSU wiring, realistic wattages | Network subgraph data: topology, links, spine-leaf design; the simulation engine and graph logic |
| **Core knowledge needed** | Redundancy models (N, N+1, 2N) — this *is* a graph-connectivity question on the power layer; Ohm's law/circuit basics you already have from Physics 2 | Graph theory basics: nodes, edges, connectivity, BFS/DFS (new, but small — NetworkX does the heavy lifting) |
| **Stretch** | Model a UPS/battery failure as time-dependent, not just on/off (uses Diff Eq) | Map network nodes to CCNA/ACI concepts (spine-leaf, VRF, EPG) for the consulting narrative |
| **Shared** | The `data/topology.yaml` schema, Python fundamentals, Git/GitHub, reading the resilience report together | |

Same split philosophy as before: neither side needs to master the other's domain, the
shared data file is where the two meet.

## Data model (planned: `data/topology.yaml`)

```yaml
devices:
  - {name: spine1, role: spine}
  - {name: leaf1,  role: leaf}
  - {name: srv1,   role: server}

network_links:
  - [leaf1, spine1]
  - [leaf1, spine2]

power:
  feeds:
    A: {capacity_kw: 8.0}
    B: {capacity_kw: 8.0}
  psu_links:              # which device's PSU connects to which feed
    - {device: leaf1, psu: A, feed: A}
    - {device: leaf1, psu: B, feed: B}
```

This is a superset of the `inventory.yaml` idea from the PowerOps Gateway project — same
spirit (network and power described in one file), extended with explicit network links
so the graph has edges to simulate, not just wattage numbers.

## What "resilience score" means here

For each simulated failure, the report gives:
- **Devices unaffected** — kept both network and power connectivity
- **Devices degraded** — lost one layer (still up, but no longer redundant)
- **Devices down** — lost both layers, or lost their only path in a layer
- **Hidden single points of failure** — devices that looked fully redundant on paper
  but go fully down together under one simulated failure

## Getting started (planned)

**Requirements**
- Python 3.10+
- `networkx`, `matplotlib` (or `graphviz`), `pyyaml`, `pytest`

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
python -m twin simulate --topology data/topology.yaml --remove spine1 --draw
```

## Roadmap

- [ ] Learn NetworkX basics (build a graph, check connectivity, remove a node)
- [ ] Design `data/topology.yaml` schema (network side + power side together)
- [ ] Build the graph from the YAML (two edge types, one node set)
- [ ] Failure simulation: remove a node or edge, re-check connectivity per layer
- [ ] Resilience report: unaffected / degraded / down / hidden single points of failure
- [ ] Topology visualization: before/after, color-coded by survival
- [ ] Seed a deliberate hidden single point of failure in the sample data, to prove the tool catches it
- [ ] *(stretch)* Time-dependent UPS/battery failure model (ODE-based)
- [ ] *(stretch)* Thin FastAPI wrapper: `POST /simulate/{target}`
- [ ] Slides and demo rehearsal

## Limitations

- This is a simulation over a modeled topology, not live telemetry from real hardware.
- Connectivity checks are structural (graph reachability), not a full physical power-flow
  or network-protocol-timing model.
- The consulting/ACI framing (mapping nodes to spine-leaf, VRF, EPG concepts) is
  presentation-layer — the simulator itself is platform-agnostic.

## Related work

**PowerOps Gateway** (`datacenter-aci-blueprint` repo) — a separate, already-in-progress
project: a FastAPI health/compliance API over a similar shared network+power inventory
model. That project asks "is this compliant right now?"; this one asks "what breaks if
this fails?" They could eventually share a data schema, but are built and delivered
separately.

## Secrets

No credentials are needed for the core simulator (it runs on local YAML data). If a live
telemetry source is added later, credentials go in environment variables or a
`.gitignore`d `.env` file — never in `data/topology.yaml` or committed code.

## Authors

Zaheen Rahman (network/graph side) + power/electrical engineering partner Anas Shah
