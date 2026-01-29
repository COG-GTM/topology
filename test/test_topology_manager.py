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


def test_node_subnode_management():
    """
    Test adding and retrieving subnodes from a node.
    """
    from topology.graph import Node
    from topology.graph.exceptions import AlreadyExists, NotFound

    parent = Node('parent_node', metadata={'type': 'switch'})
    child1 = Node('child1', parent=parent, metadata={'type': 'vlan'})
    child2 = Node('child2', parent=parent, metadata={'type': 'vlan'})

    parent.add_subnode(child1)
    parent.add_subnode(child2)

    assert parent.has_subnode('child1') is True
    assert parent.has_subnode('child2') is True
    assert parent.has_subnode('nonexistent') is False

    retrieved = parent.get_subnode('child1')
    assert retrieved.identifier == 'child1'
    assert retrieved.metadata.get('type') == 'vlan'

    with pytest.raises(NotFound):
        parent.get_subnode('nonexistent')

    with pytest.raises(AlreadyExists):
        parent.add_subnode(child1)


def test_node_has_parent():
    """
    Test the has_parent method on nodes.
    """
    from topology.graph import Node

    parent = Node('parent_node')
    child = Node('child_node', parent=parent)
    orphan = Node('orphan_node')

    assert child.has_parent() is True
    assert child.parent.identifier == 'parent_node'
    assert orphan.has_parent() is False


def test_node_port_inconsistent_error():
    """
    Test that adding a port with wrong node_id raises Inconsistent error.
    """
    from topology.graph import Node, Port
    from topology.graph.exceptions import Inconsistent

    node = Node('node1')
    port = Port('p1', 'different_node')

    with pytest.raises(Inconsistent):
        node.add_port(port)


def test_node_duplicate_port_error():
    """
    Test that adding a duplicate port raises AlreadyExists error.
    """
    from topology.graph import Node, Port
    from topology.graph.exceptions import AlreadyExists

    node = Node('node1')
    port1 = Port('p1', 'node1')
    port2 = Port('p1', 'node1')

    node.add_port(port1)

    with pytest.raises(AlreadyExists):
        node.add_port(port2)


def test_port_calc_id():
    """
    Test the Port.calc_id static method.
    """
    from topology.graph import Port

    port_id = Port.calc_id('sw1', 'eth0')
    assert port_id == 'sw1:eth0'

    port_id2 = Port.calc_id('router', 'mgmt')
    assert port_id2 == 'router:mgmt'


def test_port_properties():
    """
    Test Port properties (label, identifier, node_id, metadata).
    """
    from topology.graph import Port

    port = Port('eth0', 'sw1', metadata={'speed': '1G', 'duplex': 'full'})

    assert port.label == 'eth0'
    assert port.identifier == 'sw1:eth0'
    assert port.node_id == 'sw1'
    assert port.metadata.get('speed') == '1G'
    assert port.metadata.get('duplex') == 'full'
    assert port.metadata.get('label') == 'eth0'


def test_link_has_node():
    """
    Test the Link.has_node method.
    """
    from topology.graph import Node, Port, Link

    node1 = Node('sw1')
    node2 = Node('hs1')
    port1 = Port('p1', 'sw1')
    port2 = Port('p1', 'hs1')

    link = Link(node1, port1, node2, port2)

    assert link.has_node('sw1') is True
    assert link.has_node('hs1') is True
    assert link.has_node('nonexistent') is False


def test_link_has_port():
    """
    Test the Link.has_port method.
    """
    from topology.graph import Node, Port, Link

    node1 = Node('sw1')
    node2 = Node('hs1')
    port1 = Port('p1', 'sw1')
    port2 = Port('p2', 'hs1')

    link = Link(node1, port1, node2, port2)

    assert link.has_port('sw1', 'p1') is True
    assert link.has_port('hs1', 'p2') is True
    assert link.has_port('sw1', 'p2') is False
    assert link.has_port('hs1', 'p1') is False


def test_link_calc_id_ordering():
    """
    Test that Link.calc_id produces consistent identifiers regardless of order.
    """
    from topology.graph import Link

    id1 = Link.calc_id('sw1', 'p1', 'hs1', 'p1')
    id2 = Link.calc_id('hs1', 'p1', 'sw1', 'p1')

    assert id1 == id2


def test_graph_get_port_by_id():
    """
    Test the TopologyGraph.get_port_by_id method.
    """
    from topology.graph.exceptions import NotFound

    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_port('p1', 'sw1', speed='1G')

    port = graph.get_port_by_id('sw1:p1')
    assert port.label == 'p1'
    assert port.metadata.get('speed') == '1G'

    with pytest.raises(NotFound):
        graph.get_port_by_id('sw1:nonexistent')


def test_graph_get_link_by_id():
    """
    Test the TopologyGraph.get_link_by_id method.
    """
    from topology.graph.exceptions import NotFound

    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_node('hs1')
    graph.create_port('p1', 'sw1')
    graph.create_port('p1', 'hs1')
    graph.create_link('sw1', 'p1', 'hs1', 'p1', speed='10G')

    link_id = 'hs1:p1 -- sw1:p1'
    link = graph.get_link_by_id(link_id)
    assert link.metadata.get('speed') == '10G'

    with pytest.raises(NotFound):
        graph.get_link_by_id('nonexistent:p1 -- other:p1')


def test_graph_get_link():
    """
    Test the TopologyGraph.get_link method.
    """
    from topology.graph.exceptions import NotFound

    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_node('hs1')
    graph.create_port('p1', 'sw1')
    graph.create_port('p1', 'hs1')
    graph.create_link('sw1', 'p1', 'hs1', 'p1', mtu=9000)

    link = graph.get_link('sw1', 'p1', 'hs1', 'p1')
    assert link.metadata.get('mtu') == 9000

    link_reversed = graph.get_link('hs1', 'p1', 'sw1', 'p1')
    assert link_reversed.metadata.get('mtu') == 9000

    with pytest.raises(NotFound):
        graph.get_link('sw1', 'p1', 'hs1', 'p2')


def test_graph_has_port_id():
    """
    Test the TopologyGraph.has_port_id method.
    """
    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_port('p1', 'sw1')

    assert graph.has_port_id('sw1:p1') is True
    assert graph.has_port_id('sw1:p2') is False


def test_graph_has_link_id():
    """
    Test the TopologyGraph.has_link_id method.
    """
    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_node('hs1')
    graph.create_port('p1', 'sw1')
    graph.create_port('p1', 'hs1')
    graph.create_link('sw1', 'p1', 'hs1', 'p1')

    link_id = 'hs1:p1 -- sw1:p1'
    assert graph.has_link_id(link_id) is True
    assert graph.has_link_id('nonexistent:p1 -- other:p1') is False


def test_graph_bilinks_deprecated():
    """
    Test that TopologyGraph.bilinks() emits deprecation warning.
    """
    import warnings

    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_node('hs1')
    graph.create_port('p1', 'sw1')
    graph.create_port('p1', 'hs1')
    graph.create_link('sw1', 'p1', 'hs1', 'p1')

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        bilinks = list(graph.bilinks())
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert 'bilinks' in str(w[0].message)

    assert len(bilinks) == 1
    (node1, port1), (node2, port2), link = bilinks[0]
    assert node1.identifier in ['sw1', 'hs1']
    assert node2.identifier in ['sw1', 'hs1']


def test_graph_biports_deprecated():
    """
    Test that TopologyGraph.biports() emits deprecation warning.
    """
    import warnings

    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_port('p1', 'sw1')
    graph.create_port('p2', 'sw1')

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        biports = list(graph.biports())
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert 'biports' in str(w[0].message)

    assert len(biports) == 2


def test_graph_duplicate_node_returns_existing():
    """
    Test that creating a duplicate node returns the existing node.
    """
    graph = TopologyGraph()
    node1 = graph.create_node('sw1', name='Switch 1')
    node2 = graph.create_node('sw1', name='Different Name')

    assert node1 is node2
    assert node1.metadata.get('name') == 'Switch 1'


def test_graph_duplicate_port_returns_existing():
    """
    Test that creating a duplicate port returns the existing port.
    """
    graph = TopologyGraph()
    graph.create_node('sw1')
    port1 = graph.create_port('p1', 'sw1', speed='1G')
    port2 = graph.create_port('p1', 'sw1', speed='10G')

    assert port1 is port2
    assert port1.metadata.get('speed') == '1G'


def test_graph_duplicate_link_returns_existing():
    """
    Test that creating a duplicate link returns the existing link.
    """
    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_node('hs1')
    graph.create_port('p1', 'sw1')
    graph.create_port('p1', 'hs1')

    link1 = graph.create_link('sw1', 'p1', 'hs1', 'p1', speed='1G')
    link2 = graph.create_link('sw1', 'p1', 'hs1', 'p1', speed='10G')

    assert link1 is link2
    assert link1.metadata.get('speed') == '1G'


def test_graph_consistency_check_missing_subnode():
    """
    Test that consistency check fails when a subnode is not in the topology.

    Note: The check_consistency method iterates over node._subnodes dict,
    which yields keys (identifiers). It then checks if those identifiers
    exist in the graph's _nodes dict.
    """
    from topology.graph import Node
    from topology.graph.exceptions import NotFound

    graph = TopologyGraph()
    parent = graph.create_node('parent')

    orphan_subnode = Node('orphan')
    parent._subnodes[orphan_subnode.identifier] = orphan_subnode

    with pytest.raises((NotFound, AttributeError)):
        graph.check_consistency()


def test_graph_str_representation():
    """
    Test that TopologyGraph has a string representation.
    """
    graph = TopologyGraph()
    graph.create_node('sw1', name='Switch')

    str_repr = str(graph)
    assert 'sw1' in str_repr
    assert 'Switch' in str_repr


def test_node_str_representation():
    """
    Test that Node has a string representation.
    """
    from topology.graph import Node

    node = Node('sw1', metadata={'name': 'Switch', 'type': 'switch'})
    str_repr = str(node)

    assert 'sw1' in str_repr
    assert 'Switch' in str_repr


def test_port_str_representation():
    """
    Test that Port has a string representation.
    """
    from topology.graph import Port

    port = Port('eth0', 'sw1', metadata={'speed': '1G'})
    str_repr = str(port)

    assert 'eth0' in str_repr
    assert 'sw1' in str_repr


def test_link_str_representation():
    """
    Test that Link has a string representation.
    """
    from topology.graph import Node, Port, Link

    node1 = Node('sw1')
    node2 = Node('hs1')
    port1 = Port('p1', 'sw1')
    port2 = Port('p1', 'hs1')
    link = Link(node1, port1, node2, port2, metadata={'speed': '10G'})

    str_repr = str(link)
    assert 'sw1' in str_repr
    assert 'hs1' in str_repr


def test_node_subnodes_iterator():
    """
    Test the Node.subnodes() iterator.
    """
    from topology.graph import Node

    parent = Node('parent')
    child1 = Node('child1', parent=parent)
    child2 = Node('child2', parent=parent)

    parent.add_subnode(child1)
    parent.add_subnode(child2)

    subnodes = list(parent.subnodes())
    assert len(subnodes) == 2
    identifiers = [s.identifier for s in subnodes]
    assert 'child1' in identifiers
    assert 'child2' in identifiers


def test_node_ports_iterator():
    """
    Test the Node.ports() iterator.
    """
    from topology.graph import Node, Port

    node = Node('sw1')
    port1 = Port('p1', 'sw1')
    port2 = Port('p2', 'sw1')

    node.add_port(port1)
    node.add_port(port2)

    ports = list(node.ports())
    assert len(ports) == 2
    labels = [p.label for p in ports]
    assert 'p1' in labels
    assert 'p2' in labels


def test_link_properties():
    """
    Test Link properties (node1, node2, port1, port2, metadata).
    """
    from topology.graph import Node, Port, Link

    node1 = Node('sw1', metadata={'type': 'switch'})
    node2 = Node('hs1', metadata={'type': 'host'})
    port1 = Port('p1', 'sw1')
    port2 = Port('p1', 'hs1')
    link = Link(
        node1, port1, node2, port2, metadata={'speed': '10G', 'mtu': 9000}
    )

    assert link.node1.identifier == 'sw1'
    assert link.node2.identifier == 'hs1'
    assert link.port1.label == 'p1'
    assert link.port2.label == 'p1'
    assert link.metadata.get('speed') == '10G'
    assert link.metadata.get('mtu') == 9000


def test_graph_create_port_nonexistent_node():
    """
    Test that creating a port for a non-existent node raises NotFound.
    """
    from topology.graph.exceptions import NotFound

    graph = TopologyGraph()

    with pytest.raises(NotFound):
        graph.create_port('p1', 'nonexistent_node')


def test_graph_create_link_nonexistent_node():
    """
    Test that creating a link with non-existent nodes raises NotFound.
    """
    from topology.graph.exceptions import NotFound

    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_port('p1', 'sw1')

    with pytest.raises(NotFound):
        graph.create_link('sw1', 'p1', 'nonexistent', 'p1')


def test_graph_create_link_nonexistent_port():
    """
    Test that creating a link with non-existent ports raises NotFound.
    """
    from topology.graph.exceptions import NotFound

    graph = TopologyGraph()
    graph.create_node('sw1')
    graph.create_node('hs1')
    graph.create_port('p1', 'sw1')

    with pytest.raises(NotFound):
        graph.create_link('sw1', 'p1', 'hs1', 'nonexistent')


def test_graph_has_port_label_nonexistent_node():
    """
    Test that has_port_label raises NotFound for non-existent node.
    """
    from topology.graph.exceptions import NotFound

    graph = TopologyGraph()

    with pytest.raises(NotFound):
        graph.has_port_label('nonexistent', 'p1')


def test_node_get_port_by_id_not_found():
    """
    Test that Node.get_port_by_id raises NotFound for non-existent port.
    """
    from topology.graph import Node
    from topology.graph.exceptions import NotFound

    node = Node('sw1')

    with pytest.raises(NotFound):
        node.get_port_by_id('sw1:nonexistent')


def test_link_as_dict():
    """
    Test the Link.as_dict method.
    """
    from topology.graph import Node, Port, Link

    node1 = Node('sw1', metadata={'type': 'switch'})
    node2 = Node('hs1', metadata={'type': 'host'})
    port1 = Port('p1', 'sw1')
    port2 = Port('p1', 'hs1')
    link = Link(node1, port1, node2, port2, metadata={'speed': '10G'})

    link_dict = link.as_dict()

    assert 'node1' in link_dict
    assert 'node2' in link_dict
    assert 'port1' in link_dict
    assert 'port2' in link_dict
    assert 'metadata' in link_dict
    assert link_dict['metadata'].get('speed') == '10G'


def test_node_as_dict():
    """
    Test the Node.as_dict method.
    """
    from topology.graph import Node, Port

    node = Node('sw1', metadata={'type': 'switch', 'name': 'Switch 1'})
    port = Port('p1', 'sw1')
    node.add_port(port)

    node_dict = node.as_dict()

    assert node_dict['identifier'] == 'sw1'
    assert node_dict['metadata']['type'] == 'switch'
    assert node_dict['metadata']['name'] == 'Switch 1'
    assert 'sw1:p1' in node_dict['ports']


def test_port_as_dict():
    """
    Test the Port.as_dict method.
    """
    from topology.graph import Port

    port = Port('eth0', 'sw1', metadata={'speed': '1G', 'duplex': 'full'})

    port_dict = port.as_dict()

    assert port_dict['identifier'] == 'sw1:eth0'
    assert port_dict['label'] == 'eth0'
    assert port_dict['node_id'] == 'sw1'
    assert port_dict['metadata']['speed'] == '1G'
    assert port_dict['metadata']['duplex'] == 'full'
