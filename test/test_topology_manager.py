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


def test_graph_attribute_with_dictmeta_load():
    """
    Test that the graph attribute works correctly when loading topology
    via the load() method with dictionary metadata.
    """
    dictmeta = {
        'nodes': [
            {
                'nodes': ['sw1', 'hs1'],
                'attributes': {'type': 'switch'},
                'parent': None
            },
            {
                'nodes': ['hs1'],
                'attributes': {'type': 'host', 'name': 'Host 1'},
                'parent': None
            }
        ],
        'ports': [
            {
                'ports': [('sw1', '1'), ('hs1', '1')],
                'attributes': {}
            }
        ],
        'links': [
            {
                'endpoints': (('sw1', '1'), ('hs1', '1')),
                'attributes': {'speed': '1G'}
            }
        ]
    }

    topology = TopologyManager(engine='debug')
    topology.load(dictmeta)

    assert topology.graph is not None
    assert isinstance(topology.graph, TopologyGraph)

    nodes = list(topology.graph.nodes())
    assert len(nodes) == 2

    links = list(topology.graph.links())
    assert len(links) == 1

    link = links[0]
    assert link.metadata.get('speed') == '1G'


def test_graph_attribute_with_attribute_injection():
    """
    Test that the graph attribute correctly handles attribute injection.
    """
    topodesc = """
        [type=switch] sw1
        [type=host] hs1
        sw1:1 -- hs1:1
    """

    inject = {
        'nodes': {
            'sw1': {'vlan': 100, 'management_ip': '10.0.0.1'},
            'hs1': {'ip': '192.168.1.10'}
        },
        'ports': {},
        'links': {}
    }

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc, inject=inject)

    sw1_node = topology.graph.get_node('sw1')
    assert sw1_node.metadata.get('vlan') == 100
    assert sw1_node.metadata.get('management_ip') == '10.0.0.1'

    hs1_node = topology.graph.get_node('hs1')
    assert hs1_node.metadata.get('ip') == '192.168.1.10'


def test_graph_attribute_isolation_between_instances():
    """
    Test that graph attributes are isolated between different
    TopologyManager instances.
    """
    topology1 = TopologyManager(engine='debug')
    topology1.parse("""
        [type=switch] sw1
        [type=host] hs1
        sw1:1 -- hs1:1
    """)

    topology2 = TopologyManager(engine='debug')
    topology2.parse("""
        [type=router] r1
        [type=server] srv1
        r1:1 -- srv1:1
    """)

    assert topology1.graph is not topology2.graph

    nodes1 = [n.identifier for n in topology1.graph.nodes()]
    nodes2 = [n.identifier for n in topology2.graph.nodes()]

    assert 'sw1' in nodes1
    assert 'hs1' in nodes1
    assert 'r1' not in nodes1

    assert 'r1' in nodes2
    assert 'srv1' in nodes2
    assert 'sw1' not in nodes2


def test_graph_attribute_with_environment():
    """
    Test that the graph attribute correctly handles environment variables.
    """
    dictmeta = {
        'environment': {
            'NETWORK_NAME': 'test-network',
            'VLAN_ID': '100'
        },
        'nodes': [
            {
                'nodes': ['sw1'],
                'attributes': {'type': 'switch'},
                'parent': None
            }
        ],
        'ports': [],
        'links': []
    }

    topology = TopologyManager(engine='debug')
    topology.load(dictmeta)

    assert topology.graph.environment.get('NETWORK_NAME') == 'test-network'
    assert topology.graph.environment.get('VLAN_ID') == '100'


def test_graph_attribute_error_handling_nonexistent_node():
    """
    Test that accessing a non-existent node via graph raises appropriate error.
    """
    from topology.graph.exceptions import NotFound

    topology = TopologyManager(engine='debug')
    topology.parse("""
        [type=switch] sw1
    """)

    with pytest.raises(NotFound):
        topology.graph.get_node('nonexistent')


def test_graph_attribute_error_handling_nonexistent_port():
    """
    Test that accessing a non-existent port via graph raises appropriate error.
    """
    from topology.graph.exceptions import NotFound

    topology = TopologyManager(engine='debug')
    topology.parse("""
        [type=switch] sw1
    """)

    with pytest.raises(NotFound):
        topology.graph.get_port_by_label('sw1', 'nonexistent')


def test_graph_consistency_check():
    """
    Test that the graph consistency check works correctly.
    """
    graph = TopologyGraph()

    graph.create_node('sw1', name='Switch 1')
    graph.create_node('hs1', name='Host 1', type='host')

    graph.create_port('1', 'sw1')
    graph.create_port('1', 'hs1')

    graph.create_link('sw1', '1', 'hs1', '1')

    graph.check_consistency()

    topology = TopologyManager(engine='debug')
    topology.graph = graph
    topology.build()

    assert topology.get('sw1') is not None
    assert topology.get('hs1') is not None

    topology.unbuild()


def test_graph_attribute_with_link_metadata():
    """
    Test that link metadata is correctly accessible via graph attribute
    using the dictmeta load method.
    """
    dictmeta = {
        'nodes': [
            {
                'nodes': ['sw1'],
                'attributes': {'type': 'switch'},
                'parent': None
            },
            {
                'nodes': ['hs1'],
                'attributes': {'type': 'host'},
                'parent': None
            }
        ],
        'ports': [
            {
                'ports': [('sw1', '1'), ('hs1', '1')],
                'attributes': {}
            }
        ],
        'links': [
            {
                'endpoints': (('sw1', '1'), ('hs1', '1')),
                'attributes': {'speed': '10G', 'mtu': 9000}
            }
        ]
    }

    topology = TopologyManager(engine='debug')
    topology.load(dictmeta)

    links = list(topology.graph.links())
    assert len(links) == 1

    link = links[0]
    assert link.metadata.get('speed') == '10G'
    assert link.metadata.get('mtu') == 9000


def test_graph_attribute_with_port_metadata():
    """
    Test that port metadata is correctly accessible via graph attribute
    using the dictmeta load method.
    """
    dictmeta = {
        'nodes': [
            {
                'nodes': ['sw1'],
                'attributes': {'type': 'switch'},
                'parent': None
            },
            {
                'nodes': ['hs1'],
                'attributes': {'type': 'host'},
                'parent': None
            }
        ],
        'ports': [
            {
                'ports': [('sw1', 'mgmt')],
                'attributes': {'port_number': 5, 'speed': '1G'}
            },
            {
                'ports': [('sw1', '1'), ('hs1', '1')],
                'attributes': {}
            }
        ],
        'links': [
            {
                'endpoints': (('sw1', '1'), ('hs1', '1')),
                'attributes': {}
            }
        ]
    }

    topology = TopologyManager(engine='debug')
    topology.load(dictmeta)

    sw1_node = topology.graph.get_node('sw1')
    mgmt_port = sw1_node.get_port_by_label('mgmt')

    assert mgmt_port.metadata.get('port_number') == 5
    assert mgmt_port.metadata.get('speed') == '1G'


def test_graph_attribute_empty_topology():
    """
    Test that graph attribute works correctly with an empty topology.
    """
    topology = TopologyManager(engine='debug')

    assert topology.graph is not None
    assert isinstance(topology.graph, TopologyGraph)

    nodes = list(topology.graph.nodes())
    assert len(nodes) == 0

    links = list(topology.graph.links())
    assert len(links) == 0

    ports = list(topology.graph.ports())
    assert len(ports) == 0


def test_graph_as_dict_representation():
    """
    Test that the graph can be converted to a dictionary representation.
    """
    topodesc = """
        [type=switch name="Switch 1"] sw1
        [type=host name="Host 1"] hs1
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)

    graph_dict = topology.graph.as_dict()

    assert 'nodes' in graph_dict
    assert 'links' in graph_dict
    assert 'ports' in graph_dict
    assert 'environment' in graph_dict

    assert 'sw1' in graph_dict['nodes']
    assert 'hs1' in graph_dict['nodes']

    assert graph_dict['nodes']['sw1']['metadata']['type'] == 'switch'
    assert graph_dict['nodes']['hs1']['metadata']['type'] == 'host'


def test_graph_attribute_has_methods():
    """
    Test that the graph has_* methods work correctly.
    """
    topodesc = """
        [type=switch] sw1
        [type=host] hs1
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)

    assert topology.graph.has_node('sw1') is True
    assert topology.graph.has_node('hs1') is True
    assert topology.graph.has_node('nonexistent') is False

    assert topology.graph.has_port_label('sw1', '1') is True
    assert topology.graph.has_port_label('sw1', '999') is False

    assert topology.graph.has_link('sw1', '1', 'hs1', '1') is True
    assert topology.graph.has_link('sw1', '2', 'hs1', '2') is False
