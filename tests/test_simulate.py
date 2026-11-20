from pathlib import Path

import pytest

from model.simulate import (
    FAILED,
    ISOLATED,
    NO_POWER,
    UP,
    Failure,
    device_status,
    impacted_devices,
    parse_failure,
    single_points_of_failure,
)
from model.topology import build_graph, load_topology

REPO_ROOT = Path(__file__).resolve().parent.parent

# Same shape as DataCenterYAML, plus a small power section for the power tests.
TOPOLOGY = {
    "devices": [
        {"name": "core1", "role": "core"},
        {"name": "core2", "role": "core"},
        {"name": "acc1", "role": "access"},
        {"name": "acc2", "role": "access"},
        {"name": "srv1", "role": "server"},
        {"name": "srv2", "role": "server"},
        {"name": "upstream", "role": "core"},
    ],
    "network_links": [
        ["core1", "upstream"],
        ["core2", "upstream"],
        ["acc1", "core1"],
        ["acc1", "core2"],
        ["acc2", "core1"],
        ["acc2", "core2"],
        ["srv1", "acc1"],
        ["srv2", "acc2"],
    ],
}

POWERED = {
    **TOPOLOGY,
    "power": {
        "feeds": {"A": {"capacity_kw": 5.5}, "B": {"capacity_kw": 5.5}},
        "psu_links": [
            {"device": "core1", "psu": "A", "feed": "A"},
            {"device": "core2", "psu": "A", "feed": "A"},  # both cores share feed A
            {"device": "acc1", "psu": "A", "feed": "A"},
            {"device": "acc1", "psu": "B", "feed": "B"},   # acc1 has two feeds
            {"device": "acc2", "psu": "B", "feed": "B"},
            {"device": "srv1", "psu": "B", "feed": "B"},
            {"device": "srv2", "psu": "B", "feed": "B"},
        ],
    },
}


@pytest.fixture
def graph():
    return build_graph(TOPOLOGY)


@pytest.fixture
def powered_graph():
    return build_graph(POWERED)


def test_baseline_everything_is_up(graph):
    assert set(device_status(graph).values()) == {UP}


def test_one_core_failing_is_survivable(graph):
    assert impacted_devices(graph, parse_failure(["device:core1"])) == []
    assert impacted_devices(graph, parse_failure(["device:core2"])) == []


def test_both_cores_failing_cuts_off_everything_below(graph):
    hit = impacted_devices(graph, parse_failure(["device:core1", "device:core2"]))
    assert hit == ["acc1", "acc2", "srv1", "srv2"]


def test_access_switch_is_a_single_point_of_failure_for_its_server(graph):
    assert impacted_devices(graph, parse_failure(["device:acc1"])) == ["srv1"]
    assert impacted_devices(graph, parse_failure(["device:acc2"])) == ["srv2"]


def test_redundant_uplink_survives_one_link_but_not_both(graph):
    assert impacted_devices(graph, parse_failure(["link:acc1-core1"])) == []
    both = parse_failure(["link:acc1-core1", "link:acc1-core2"])
    assert impacted_devices(graph, both) == ["acc1", "srv1"]


def test_failed_device_is_reported_failed_not_impacted(graph):
    status = device_status(graph, parse_failure(["device:acc1"]))
    assert status["acc1"] == FAILED
    assert status["srv1"] == ISOLATED


def test_upstream_is_a_single_point_of_failure(graph):
    spofs = dict(single_points_of_failure(graph))
    assert "device:upstream" in spofs
    assert "core1" in spofs["device:upstream"]


def test_shared_feed_takes_out_both_cores(powered_graph):
    status = device_status(powered_graph, parse_failure(["feed:A"]))
    assert status["core1"] == NO_POWER
    assert status["core2"] == NO_POWER
    # acc1 still has power from feed B, but it lost both uplinks.
    assert status["acc1"] == ISOLATED
    assert status["srv1"] == ISOLATED


def test_dual_fed_device_keeps_power_when_one_feed_fails(powered_graph):
    status = device_status(powered_graph, parse_failure(["feed:B"]))
    assert status["acc1"] != NO_POWER
    assert status["acc2"] == NO_POWER


def test_power_single_points_of_failure_are_found(powered_graph):
    spofs = dict(single_points_of_failure(powered_graph))
    assert "feed:A" in spofs  # the "redundant" cores secretly share it


def test_parse_failure_rejects_bad_input():
    with pytest.raises(ValueError):
        parse_failure(["core1"])
    with pytest.raises(ValueError):
        parse_failure(["link:acc1"])


def test_unknown_names_are_rejected(graph):
    with pytest.raises(ValueError):
        device_status(graph, Failure(devices=frozenset(["nope"])))
    with pytest.raises(ValueError):
        device_status(graph, parse_failure(["link:acc1-srv2"]))


def test_repo_yaml_loads_and_is_healthy():
    path = REPO_ROOT / "DataCenterYAML"
    if not path.exists():
        pytest.skip("DataCenterYAML not found")
    graph = load_topology(path)
    assert set(device_status(graph).values()) == {UP}
