"""Load a data center topology from YAML into a NetworkX graph.

Expected YAML shape (the power section is optional):

    devices:
      - {name: core1, role: core}
    network_links:
      - [acc1, core1]
    power:
      feeds:
        A: {capacity_kw: 8.0}
      psu_links:
        - {device: core1, psu: A, feed: A}
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import yaml


def load_topology(path: str | Path) -> nx.Graph:
    """Read a YAML file and return the topology graph."""
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return build_graph(data)


def build_graph(data: dict) -> nx.Graph:
    """Build a graph from already-parsed topology data.

    Node attributes: role. Graph attributes:
      feeds     - set of power feed names
      psu_feeds - dict of device name -> set of feeds that power it
    A device with no psu_links is treated as always powered (for example the
    upstream placeholder, which stands in for the rest of the network).
    """
    graph = nx.Graph()

    for device in data.get("devices", []):
        graph.add_node(str(device["name"]), role=device.get("role", "unknown"))

    for a, b in data.get("network_links", []):
        a, b = str(a), str(b)
        for name in (a, b):
            if name not in graph:
                raise ValueError(f"network_links mentions unknown device '{name}'")
        graph.add_edge(a, b)

    power = data.get("power") or {}
    feeds = {str(name) for name in (power.get("feeds") or {})}
    psu_feeds: dict[str, set[str]] = {}
    for link in power.get("psu_links") or []:
        device, feed = str(link["device"]), str(link["feed"])
        if device not in graph:
            raise ValueError(f"psu_links mentions unknown device '{device}'")
        if feed not in feeds:
            raise ValueError(f"psu_links mentions unknown feed '{feed}'")
        psu_feeds.setdefault(device, set()).add(feed)

    graph.graph["feeds"] = feeds
    graph.graph["psu_feeds"] = psu_feeds
    return graph
