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


def test_unknown_engine_raises_error():
    """
    Test that TopologyManager with unknown engine raises RuntimeError.
    """
    with pytest.raises(RuntimeError) as excinfo:
        TopologyManager(engine='nonexistent_engine')

    assert 'unknown platform engine' in str(excinfo.value).lower()


def test_nml_property_deprecated():
    """
    Test that nml property returns graph and emits DeprecationWarning.
    """
    import warnings

    topology = TopologyManager(engine='debug')
    topology.parse('sw1:1 -- hs1:1')

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        nml_result = topology.nml

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert 'nml attribute is obsolete' in str(w[0].message)

    assert nml_result is topology.graph


def test_parse_with_load_false():
    """
    Test that parse() with load=False returns data without loading topology.
    """
    topology = TopologyManager(engine='debug')
    data = topology.parse('sw1:1 -- hs1:1', load=False)

    assert isinstance(data, dict)
    assert 'nodes' in data
    assert 'links' in data
    assert len(list(topology.graph.nodes())) == 0
    assert len(list(topology.graph.links())) == 0


def test_resolve_on_built_topology_raises_error():
    """
    Test that resolve() raises RuntimeError on already built topology.
    """
    topology = TopologyManager(engine='debug')
    topology.parse('sw1:1 -- hs1:1')
    topology.build()

    with pytest.raises(RuntimeError) as excinfo:
        topology.resolve()

    assert 'cannot resolve an already built' in str(excinfo.value).lower()

    topology.unbuild()


def test_get_nonexistent_node_returns_none():
    """
    Test that get() returns None for non-existent node identifier.
    """
    topology = TopologyManager(engine='debug')
    topology.parse('sw1:1 -- hs1:1')
    topology.build()

    result = topology.get('nonexistent_node')
    assert result is None

    topology.unbuild()


def test_set_link_and_unset_link():
    """
    Test set_link() and unset_link() wrapper methods.
    """
    import warnings

    topology = TopologyManager(engine='debug')
    topology.parse('sw1:1 -- hs1:1')
    topology.build()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        topology.unset_link('sw1', '1', 'hs1', '1')
        topology.set_link('sw1', '1', 'hs1', '1')

    topology.unbuild()
