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


def test_set_link_emits_deprecation_warning():
    """
    Test that set_link() emits a DeprecationWarning since it internally
    calls the deprecated relink() method.
    """
    import warnings

    topodesc = """
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        topology.set_link('sw1', '1', 'hs1', '1')

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert 'relink() is deprecated' in str(w[0].message)

    topology.unbuild()


def test_unset_link_emits_deprecation_warning():
    """
    Test that unset_link() emits a DeprecationWarning since it internally
    calls the deprecated unlink() method.
    """
    import warnings

    topodesc = """
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        topology.unset_link('sw1', '1', 'hs1', '1')

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert 'unlink() is deprecated' in str(w[0].message)

    topology.unbuild()


def test_set_link_with_reversed_node_order():
    """
    Test that set_link() correctly handles reversed node order since
    Link.calc_id normalizes the link identifier regardless of order.
    """
    import warnings
    from unittest.mock import patch
    from topology.graph import Link

    topodesc = """
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    expected_link_id = Link.calc_id('sw1', '1', 'hs1', '1')
    reversed_link_id = Link.calc_id('hs1', '1', 'sw1', '1')

    assert expected_link_id == reversed_link_id

    with patch.object(topology._platform, 'relink') as mock_relink:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            topology.set_link('hs1', '1', 'sw1', '1')

        mock_relink.assert_called_once_with(expected_link_id)

    topology.unbuild()


def test_unset_link_with_reversed_node_order():
    """
    Test that unset_link() correctly handles reversed node order since
    Link.calc_id normalizes the link identifier regardless of order.
    """
    import warnings
    from unittest.mock import patch
    from topology.graph import Link

    topodesc = """
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    expected_link_id = Link.calc_id('sw1', '1', 'hs1', '1')
    reversed_link_id = Link.calc_id('hs1', '1', 'sw1', '1')

    assert expected_link_id == reversed_link_id

    with patch.object(topology._platform, 'unlink') as mock_unlink:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            topology.unset_link('hs1', '1', 'sw1', '1')

        mock_unlink.assert_called_once_with(expected_link_id)

    topology.unbuild()


def test_link_calc_id_normalization():
    """
    Test that Link.calc_id produces the same identifier regardless of
    the order of nodes/ports provided.
    """
    from topology.graph import Link

    link_id_1 = Link.calc_id('sw1', '1', 'hs1', '1')
    link_id_2 = Link.calc_id('hs1', '1', 'sw1', '1')

    assert link_id_1 == link_id_2

    link_id_3 = Link.calc_id('nodeA', 'portX', 'nodeB', 'portY')
    link_id_4 = Link.calc_id('nodeB', 'portY', 'nodeA', 'portX')

    assert link_id_3 == link_id_4


def test_multiple_sequential_link_operations():
    """
    Test that multiple sequential set_link/unset_link operations work
    correctly on the same topology.
    """
    import warnings
    from unittest.mock import patch
    from topology.graph import Link

    topodesc = """
        sw1:1 -- hs1:1
        sw1:2 -- hs2:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    link_id_1 = Link.calc_id('sw1', '1', 'hs1', '1')
    link_id_2 = Link.calc_id('sw1', '2', 'hs2', '1')

    with patch.object(topology._platform, 'unlink') as mock_unlink:
        with patch.object(topology._platform, 'relink') as mock_relink:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                topology.unset_link('sw1', '1', 'hs1', '1')
                topology.unset_link('sw1', '2', 'hs2', '1')
                topology.set_link('sw1', '1', 'hs1', '1')
                topology.set_link('sw1', '2', 'hs2', '1')

            assert mock_unlink.call_count == 2
            mock_unlink.assert_any_call(link_id_1)
            mock_unlink.assert_any_call(link_id_2)

            assert mock_relink.call_count == 2
            mock_relink.assert_any_call(link_id_1)
            mock_relink.assert_any_call(link_id_2)

    topology.unbuild()


def test_is_built_returns_false_before_build():
    """
    Test that is_built() returns False before build() is called.
    """
    topodesc = """
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)

    assert topology.is_built() is False


def test_is_built_returns_true_after_build():
    """
    Test that is_built() returns True after build() is called.
    """
    topodesc = """
        sw1:1 -- hs1:1
    """

    topology = TopologyManager(engine='debug')
    topology.parse(topodesc)
    topology.build()

    assert topology.is_built() is True

    topology.unbuild()
