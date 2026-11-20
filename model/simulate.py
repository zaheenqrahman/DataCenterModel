"""Break parts of the data center model and report what keeps working.

A device is "up" when it is powered AND has a path to the target (default
"upstream") made only of powered, non-failed devices and non-failed links.

Examples (run from the repo root):

    py -3 -m model.simulate --fail device:core1
    py -3 -m model.simulate --fail link:acc1-core1 --fail device:core2
    py -3 -m model.simulate --all-single-failures
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import networkx as nx

from model.topology import load_topology

UP = "up"
FAILED = "failed"
NO_POWER = "no_power"
ISOLATED = "isolated"


@dataclass(frozen=True)
class Failure:
    """One or more things that are broken at the same time."""

    devices: frozenset = field(default_factory=frozenset)
    links: frozenset = field(default_factory=frozenset)  # frozensets of {a, b}
    feeds: frozenset = field(default_factory=frozenset)

    def label(self) -> str:
        parts = [f"device:{d}" for d in sorted(self.devices)]
        parts += [f"link:{'-'.join(sorted(link))}" for link in sorted(self.links, key=sorted)]
        parts += [f"feed:{f}" for f in sorted(self.feeds)]
        return " + ".join(parts) if parts else "(nothing)"


def parse_failure(specs: list[str]) -> Failure:
    """Turn ["device:core1", "link:acc1-core1", "feed:A"] into a Failure."""
    devices, links, feeds = set(), set(), set()
    for spec in specs:
        kind, _, value = spec.partition(":")
        if kind == "device" and value:
            devices.add(value)
        elif kind == "feed" and value:
            feeds.add(value)
        elif kind == "link" and "-" in value:
            a, _, b = value.partition("-")
            links.add(frozenset((a, b)))
        else:
            raise ValueError(
                f"Bad failure '{spec}'. Use device:NAME, link:A-B, or feed:NAME."
            )
    return Failure(frozenset(devices), frozenset(links), frozenset(feeds))


def _check_failure_exists(graph: nx.Graph, failure: Failure) -> None:
    for device in failure.devices:
        if device not in graph:
            raise ValueError(f"Unknown device '{device}'")
    for link in failure.links:
        a, b = sorted(link)
        if not graph.has_edge(a, b):
            raise ValueError(f"Unknown link '{a}-{b}'")
    for feed in failure.feeds:
        if feed not in graph.graph["feeds"]:
            raise ValueError(f"Unknown feed '{feed}'")


def _is_powered(graph: nx.Graph, device: str, failed_feeds: frozenset) -> bool:
    feeds = graph.graph["psu_feeds"].get(device)
    if not feeds:  # no power data: assume always powered
        return True
    return any(feed not in failed_feeds for feed in feeds)


def device_status(
    graph: nx.Graph, failure: Failure | None = None, target: str = "upstream"
) -> dict[str, str]:
    """Return {device: up | failed | no_power | isolated} for one failure scenario."""
    failure = failure or Failure()
    _check_failure_exists(graph, failure)
    if target not in graph:
        raise ValueError(f"Unknown target '{target}'")

    alive = {
        node
        for node in graph
        if node not in failure.devices and _is_powered(graph, node, failure.feeds)
    }

    working = nx.Graph()
    working.add_nodes_from(alive)
    for a, b in graph.edges:
        if a in alive and b in alive and frozenset((a, b)) not in failure.links:
            working.add_edge(a, b)

    reachable = set(nx.node_connected_component(working, target)) if target in alive else set()

    status = {}
    for node in graph:
        if node in failure.devices:
            status[node] = FAILED
        elif node not in alive:
            status[node] = NO_POWER
        elif node in reachable:
            status[node] = UP
        else:
            status[node] = ISOLATED
    return status


def impacted_devices(
    graph: nx.Graph, failure: Failure, target: str = "upstream"
) -> list[str]:
    """Devices that were up with nothing broken but are not up in this failure.

    The broken devices themselves are not counted as impacted.
    """
    baseline = device_status(graph, Failure(), target)
    after = device_status(graph, failure, target)
    return sorted(
        node
        for node, state in after.items()
        if baseline[node] == UP and state != UP and state != FAILED
    )


def single_failure_report(
    graph: nx.Graph, target: str = "upstream"
) -> list[tuple[str, list[str]]]:
    """Try every single device, link, and feed failure. Return (label, impacted)."""
    candidates = [Failure(devices=frozenset([d])) for d in sorted(graph.nodes)]
    candidates += [
        Failure(links=frozenset([frozenset(edge)])) for edge in sorted(map(sorted, graph.edges))
    ]
    candidates += [Failure(feeds=frozenset([f])) for f in sorted(graph.graph["feeds"])]

    report = []
    for failure in candidates:
        report.append((failure.label(), impacted_devices(graph, failure, target)))
    return report


def single_points_of_failure(
    graph: nx.Graph, target: str = "upstream"
) -> list[tuple[str, list[str]]]:
    """Single failures that take at least one other device down."""
    return [(label, hit) for label, hit in single_failure_report(graph, target) if hit]


def _print_status(status: dict[str, str]) -> None:
    width = max(len(name) for name in status)
    for name in sorted(status):
        print(f"  {name:<{width}}  {status[name]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Data center failure model")
    parser.add_argument("--topology", default="DataCenterYAML", help="YAML topology file")
    parser.add_argument("--target", default="upstream", help="device everything must reach")
    parser.add_argument(
        "--fail", action="append", default=[], metavar="SPEC",
        help="device:NAME, link:A-B, or feed:NAME (repeat to break several)",
    )
    parser.add_argument(
        "--all-single-failures", action="store_true",
        help="try every single failure and list the ones that take other devices down",
    )
    args = parser.parse_args(argv)

    graph = load_topology(args.topology)

    if args.all_single_failures:
        print(f"Single points of failure (everything must reach '{args.target}'):")
        spofs = single_points_of_failure(graph, args.target)
        if not spofs:
            print("  none found")
        for label, hit in spofs:
            print(f"  {label:<24} takes down: {', '.join(hit)}")
        return 0

    failure = parse_failure(args.fail)
    print(f"Failure: {failure.label()}")
    _print_status(device_status(graph, failure, args.target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
