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
