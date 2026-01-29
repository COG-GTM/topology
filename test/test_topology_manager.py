# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Test suite for module topology.manager.

See http://pythontesting.net/framework/pytest/pytest-introduction/#fixtures
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import pytest  # noqa
from deepdiff import DeepDiff

# Reload module to properly measure coverage
from six.moves import reload_module

import topology.platforms.manager
from topology.manager import TopologyManager
from topology.graph import TopologyGraph


reload_module(topology.platforms.manager)


def test_build():
    """
    Test building and unbuilding a topology using the Mininet engine.
    """
    # Create a graph
    graph = TopologyGraph()

    # Create some nodes
    graph.create_node('sw1', name='My Switch 1')
    graph.create_node('hs1', name='My Host 1', type='host')

    # Create some ports
    graph.create_port('p1', 'sw1')
    graph.create_port('p2', 'sw1')
    graph.create_port('p3', 'sw1')

    graph.create_port('p1', 'hs1')
    graph.create_port('p2', 'hs1')
    graph.create_port('p3', 'hs1')

    # Create the links
    graph.create_link('sw1', 'p1', 'hs1', 'p1')
    graph.create_link('sw1', 'p2', 'hs1', 'p2')

    # Check consistency of the graph
    graph.check_consistency()

    # Create the topology and set the graph
    topology = TopologyManager(engine='debug')
    topology.graph = graph

    # Build the topology
    topology.build()

    assert topology.engine == 'debug'
    assert topology.platform.debug_value == 'fordebug'

    # Get an engine node
    assert topology.get('sw1') is not None
    assert topology.get('hs1') is not None

    # Unbuild topology
    topology.unbuild()


def test_autoport():
    """
    Test the autoport feature.
    """
    topodesc = """
        [port_number=5] hs1:oobm
        hs1:a -- hs2:x
        hs1:2 -- hs2:2
        hs1:4 -- hs2:4
        hs1:b -- hs2:y
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    assert topology.get('hs1') is not None
    assert topology.get('hs2') is not None

    ports = {k: dict(v) for k, v in topology.ports.items()}
    expected = {
        'hs1': {
            'oobm': 'oobm',
            'a': 'a',
            '2': '2',
            '4': '4',
            'b': 'b',
        },
        'hs2': {
            'x': 'x',
            '2': '2',
            '4': '4',
            'y': 'y',
        }
    }

    topology.unbuild()

    ddiff = DeepDiff(ports, expected)
    assert not ddiff


def test_nml_attribute_removed():
    """
    Test that the deprecated nml attribute has been removed.

    The nml property was deprecated in v1.18.0 and has now been removed.
    Users should use the graph attribute instead.
    """
    topology = TopologyManager(engine='debug')

    assert not hasattr(topology, 'nml'), (
        "The deprecated 'nml' attribute should have been removed from "
        "TopologyManager. Use 'graph' attribute instead."
    )

    with pytest.raises(AttributeError):
        _ = topology.nml


def test_graph_attribute_works_as_replacement():
    """
    Test that the graph attribute works correctly as the replacement for nml.

    After removing the deprecated nml property, users should use the graph
    attribute directly to access the TopologyGraph.
    """
    topology = TopologyManager(engine='debug')

    assert hasattr(topology, 'graph')
    assert isinstance(topology.graph, TopologyGraph)

    topology.graph.create_node('sw1', name='Switch 1')
    topology.graph.create_node('hs1', name='Host 1', type='host')

    nodes = list(topology.graph.nodes())
    assert len(nodes) == 2

    node_ids = [node.identifier for node in nodes]
    assert 'sw1' in node_ids
    assert 'hs1' in node_ids


def test_graph_attribute_after_parse():
    """
    Test that the graph attribute is properly populated after parsing topology.
    """
    topodesc = """
        [type=switch] sw1
        [type=host] hs1
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)

    assert topology.graph is not None
    assert isinstance(topology.graph, TopologyGraph)

    nodes = list(topology.graph.nodes())
    assert len(nodes) == 2

    links = list(topology.graph.links())
    assert len(links) == 1


def test_graph_attribute_after_build():
    """
    Test that the graph attribute remains accessible after building topology.
    """
    topodesc = """
        [type=switch] sw1
        [type=host] hs1
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    assert topology.graph is not None
    assert isinstance(topology.graph, TopologyGraph)

    nodes = list(topology.graph.nodes())
    assert len(nodes) == 2

    topology.unbuild()

    assert topology.graph is not None


def test_graph_attribute_identity_preserved():
    """
    Test that the graph attribute is the same object throughout the lifecycle.

    The graph object should maintain identity (same object reference) before
    and after build operations.
    """
    topology = TopologyManager(engine='debug')
    graph_before_parse = topology.graph

    topodesc = """
        [type=switch] sw1
        [type=host] hs1
        sw1:1 -- hs1:1
    """
    topology.parse(topodesc)
    graph_after_parse = topology.graph

    assert graph_before_parse is graph_after_parse, (
        "Graph object should be the same instance after parse"
    )

    topology.build()
    graph_after_build = topology.graph

    assert graph_before_parse is graph_after_build, (
        "Graph object should be the same instance after build"
    )

    topology.unbuild()
    graph_after_unbuild = topology.graph

    assert graph_before_parse is graph_after_unbuild, (
        "Graph object should be the same instance after unbuild"
    )


def test_graph_attribute_with_complex_topology():
    """
    Test graph attribute with a more complex topology containing multiple
    nodes, ports, and links.
    """
    topodesc = """
        [type=switch name="Core Switch"] sw1
        [type=switch name="Access Switch 1"] sw2
        [type=switch name="Access Switch 2"] sw3
        [type=host name="Host 1"] hs1
        [type=host name="Host 2"] hs2
        [type=host name="Host 3"] hs3

        sw1:1 -- sw2:1
        sw1:2 -- sw3:1
        sw2:2 -- hs1:1
        sw2:3 -- hs2:1
        sw3:2 -- hs3:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)

    assert isinstance(topology.graph, TopologyGraph)

    nodes = list(topology.graph.nodes())
    assert len(nodes) == 6

    links = list(topology.graph.links())
    assert len(links) == 5

    sw1_node = topology.graph.get_node('sw1')
    assert sw1_node is not None
    assert sw1_node.metadata.get('name') == 'Core Switch'
    assert sw1_node.metadata.get('type') == 'switch'

    topology.build()

    assert topology.get('sw1') is not None
    assert topology.get('sw2') is not None
    assert topology.get('sw3') is not None
    assert topology.get('hs1') is not None
    assert topology.get('hs2') is not None
    assert topology.get('hs3') is not None

    topology.unbuild()


def test_other_topology_manager_attributes_unaffected():
    """
    Test that other TopologyManager attributes work correctly.

    This ensures the removal of the nml property didn't inadvertently affect
    other attributes like engine, nodes, ports, platform, etc.
    """
    topology = TopologyManager(engine='debug')

    assert topology.engine == 'debug'
    assert isinstance(topology.nodes, dict)
    assert isinstance(topology.ports, dict)
    assert topology.platform is None
    assert topology.is_built() is False

    topodesc = """
        [type=switch] sw1
        [type=host] hs1
        sw1:1 -- hs1:1
    """
    topology.parse(topodesc)
    topology.build()

    assert topology.engine == 'debug'
    assert topology.platform is not None
    assert topology.is_built() is True
    assert 'sw1' in topology.nodes
    assert 'hs1' in topology.nodes
    assert 'sw1' in topology.ports
    assert 'hs1' in topology.ports

    topology.unbuild()

    assert topology.platform is None


def test_graph_attribute_with_node_attributes():
    """
    Test that graph attribute correctly handles node attributes after parsing.
    """
    topodesc = """
        [type=switch name="Switch 1" vlan=100] sw1
        [type=host name="Host 1" ip="192.168.1.1"] hs1
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)

    sw1_node = topology.graph.get_node('sw1')
    assert sw1_node.metadata.get('type') == 'switch'
    assert sw1_node.metadata.get('name') == 'Switch 1'
    assert sw1_node.metadata.get('vlan') == 100

    hs1_node = topology.graph.get_node('hs1')
    assert hs1_node.metadata.get('type') == 'host'
    assert hs1_node.metadata.get('name') == 'Host 1'
    assert hs1_node.metadata.get('ip') == '192.168.1.1'


def test_graph_attribute_ports_and_links():
    """
    Test that graph attribute correctly exposes ports and links.
    """
    topodesc = """
        [type=switch] sw1
        [type=host] hs1
        [type=host] hs2
        sw1:1 -- hs1:1
        sw1:2 -- hs2:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)

    sw1_node = topology.graph.get_node('sw1')
    sw1_ports = list(sw1_node.ports())
    assert len(sw1_ports) == 2

    port_labels = [p.metadata.get('label', p.identifier) for p in sw1_ports]
    assert '1' in port_labels or 'sw1:1' in [p.identifier for p in sw1_ports]

    links = list(topology.graph.links())
    assert len(links) == 2

    link_nodes = set()
    for link in links:
        link_nodes.add(link.node1.identifier)
        link_nodes.add(link.node2.identifier)

    assert 'sw1' in link_nodes
    assert 'hs1' in link_nodes
    assert 'hs2' in link_nodes
