# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2024 Hewlett Packard Enterprise Development LP
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
Test suite for the --topology-verbose flag functionality.

Tests cover:
- TopologyManager verbose parameter
- TopologyPlugin verbose parameter
- CLI option integration
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import logging

from six.moves import reload_module

import topology.platforms.manager
from topology.manager import TopologyManager
from topology.pytest.plugin import TopologyPlugin
from topology.graph import TopologyGraph

reload_module(topology.platforms.manager)


class TestTopologyManagerVerbose:
    """Tests for TopologyManager verbose parameter."""

    def test_verbose_defaults_to_false(self):
        """Test that verbose defaults to False when not specified."""
        topology = TopologyManager(engine='debug')
        assert topology.verbose is False

    def test_verbose_can_be_set_to_true(self):
        """Test that verbose can be set to True."""
        topology = TopologyManager(engine='debug', verbose=True)
        assert topology.verbose is True

    def test_verbose_can_be_set_to_false_explicitly(self):
        """Test that verbose can be explicitly set to False."""
        topology = TopologyManager(engine='debug', verbose=False)
        assert topology.verbose is False

    def test_verbose_logging_during_resolve(self, caplog):
        """Test that verbose logging is produced during resolve phase."""
        topodesc = """
            hs1
        """
        topology = TopologyManager(engine='debug', verbose=True)
        topology.parse(topodesc)

        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.resolve()

        log_messages = [record.message for record in caplog.records]
        assert any('[VERBOSE] Starting topology resolution phase' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Loading platform engine: debug' in msg
                   for msg in log_messages)
        assert any(
            '[VERBOSE] Creating platform instance with timestamp:' in msg
            for msg in log_messages
        )

    def test_verbose_logging_during_build(self, caplog):
        """Test that verbose logging is produced during build phase."""
        topodesc = """
            hs1:1 -- hs2:1
        """
        topology = TopologyManager(engine='debug', verbose=True)
        topology.parse(topodesc)

        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.build()

        log_messages = [record.message for record in caplog.records]

        assert any('[VERBOSE] Starting topology build phase' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Build stage: pre_build' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Build stage: add_node' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Adding node: hs1' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Adding node: hs2' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Build stage: add_biport' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Adding port' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Build stage: add_bilink' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Adding link:' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Build stage: post_build' in msg
                   for msg in log_messages)
        assert any(
            '[VERBOSE] Topology build phase completed successfully' in msg
            for msg in log_messages
        )

        topology.unbuild()

    def test_verbose_logging_during_unbuild(self, caplog):
        """Test that verbose logging is produced during unbuild phase."""
        topodesc = """
            hs1
        """
        topology = TopologyManager(engine='debug', verbose=True)
        topology.parse(topodesc)
        topology.build()

        caplog.clear()
        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.unbuild()

        log_messages = [record.message for record in caplog.records]

        assert any('[VERBOSE] Starting topology unbuild phase' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Removing references to engine nodes' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Calling platform destroy hook' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Deleting platform instance' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Topology unbuild phase completed' in msg
                   for msg in log_messages)

    def test_no_verbose_logging_when_disabled(self, caplog):
        """Test that no verbose logging is produced when verbose=False."""
        topodesc = """
            hs1:1 -- hs2:1
        """
        topology = TopologyManager(engine='debug', verbose=False)
        topology.parse(topodesc)

        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.build()
            topology.unbuild()

        log_messages = [record.message for record in caplog.records]
        verbose_messages = [msg for msg in log_messages if '[VERBOSE]' in msg]
        assert len(verbose_messages) == 0

    def test_verbose_logging_with_graph_api(self, caplog):
        """Test verbose logging when using the graph API directly."""
        graph = TopologyGraph()
        graph.create_node('sw1', name='My Switch 1')
        graph.create_node('hs1', name='My Host 1', type='host')
        graph.create_port('p1', 'sw1')
        graph.create_port('p1', 'hs1')
        graph.create_link('sw1', 'p1', 'hs1', 'p1')

        topology = TopologyManager(engine='debug', verbose=True)
        topology.graph = graph

        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.build()

        log_messages = [record.message for record in caplog.records]
        assert any('[VERBOSE] Starting topology build phase' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Adding node: sw1' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Adding node: hs1' in msg
                   for msg in log_messages)

        topology.unbuild()


class TestTopologyPluginVerbose:
    """Tests for TopologyPlugin verbose parameter."""

    def test_plugin_verbose_defaults_to_false(self):
        """Test that TopologyPlugin verbose defaults to False."""
        plugin = TopologyPlugin(
            platform='debug',
            injected_attr=None,
            log_dir=None,
            szn_dir=None,
            platform_options={},
            build_retries=0
        )
        assert plugin.verbose is False

    def test_plugin_verbose_can_be_set_to_true(self):
        """Test that TopologyPlugin verbose can be set to True."""
        plugin = TopologyPlugin(
            platform='debug',
            injected_attr=None,
            log_dir=None,
            szn_dir=None,
            platform_options={},
            build_retries=0,
            verbose=True
        )
        assert plugin.verbose is True

    def test_plugin_verbose_can_be_set_to_false_explicitly(self):
        """Test that TopologyPlugin verbose can be explicitly set to False."""
        plugin = TopologyPlugin(
            platform='debug',
            injected_attr=None,
            log_dir=None,
            szn_dir=None,
            platform_options={},
            build_retries=0,
            verbose=False
        )
        assert plugin.verbose is False


class TestVerboseCLIOption:
    """Tests for --topology-verbose CLI option using pytester."""

    def test_verbose_option_registered(self, pytestconfig):
        """Test that --topology-verbose option is registered."""
        parser = pytestconfig._parser
        group = None
        for g in parser._groups:
            if g.name == 'topology':
                group = g
                break

        assert group is not None
        option_names = [opt.names() for opt in group.options]
        flat_names = [name for names in option_names for name in names]
        assert '--topology-verbose' in flat_names

    def test_verbose_option_default_is_false(self, pytestconfig):
        """Test that --topology-verbose defaults to False."""
        verbose = pytestconfig.getoption('--topology-verbose', default=False)
        assert verbose is False


class TestVerboseIntegration:
    """Integration tests for verbose flag end-to-end behavior."""

    def test_full_lifecycle_with_verbose(self, caplog):
        """Test complete topology lifecycle with verbose enabled."""
        topodesc = """
            [type=switch name="Switch 1"] sw1
            [type=host name="Host 1"] hs1
            sw1:1 -- hs1:1
        """
        topology = TopologyManager(engine='debug', verbose=True)
        topology.parse(topodesc)

        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.build()

            assert topology.get('sw1') is not None
            assert topology.get('hs1') is not None

            topology.unbuild()

        log_messages = [record.message for record in caplog.records]

        assert any('[VERBOSE] Starting topology resolution phase' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Starting topology build phase' in msg
                   for msg in log_messages)
        assert any(
            '[VERBOSE] Topology build phase completed successfully' in msg
            for msg in log_messages
        )
        assert any('[VERBOSE] Starting topology unbuild phase' in msg
                   for msg in log_messages)
        assert any('[VERBOSE] Topology unbuild phase completed' in msg
                   for msg in log_messages)

    def test_verbose_logs_all_build_stages_in_order(self, caplog):
        """Test that verbose logs all build stages in correct order."""
        topodesc = """
            hs1:1 -- hs2:1
        """
        topology = TopologyManager(engine='debug', verbose=True)
        topology.parse(topodesc)

        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.build()

        log_messages = [record.message for record in caplog.records]
        verbose_messages = [msg for msg in log_messages if '[VERBOSE]' in msg]

        stage_order = ['pre_build', 'add_node', 'add_biport',
                       'add_bilink', 'post_build']
        stage_indices = []
        for stage in stage_order:
            for i, msg in enumerate(verbose_messages):
                if f'Build stage: {stage}' in msg:
                    stage_indices.append(i)
                    break

        for i in range(len(stage_indices) - 1):
            assert stage_indices[i] < stage_indices[i + 1], (
                f'Stage order incorrect: {stage_order[i]} should come before '
                f'{stage_order[i + 1]}'
            )

        topology.unbuild()

    def test_verbose_logs_link_details(self, caplog):
        """Test that verbose logs link details with node and port info."""
        topodesc = """
            sw1:eth0 -- hs1:eth0
        """
        topology = TopologyManager(engine='debug', verbose=True)
        topology.parse(topodesc)

        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.build()

        log_messages = [record.message for record in caplog.records]
        link_messages = [msg for msg in log_messages
                         if '[VERBOSE] Adding link:' in msg]

        assert len(link_messages) == 1
        link_msg = link_messages[0]
        assert 'sw1' in link_msg
        assert 'hs1' in link_msg
        assert '<->' in link_msg

        topology.unbuild()

    def test_verbose_with_multiple_nodes_and_links(self, caplog):
        """Test verbose logging with complex topology."""
        topodesc = """
            [type=switch] sw1
            [type=switch] sw2
            [type=host] hs1
            [type=host] hs2
            sw1:1 -- hs1:1
            sw2:1 -- hs2:1
            sw1:2 -- sw2:2
        """
        topology = TopologyManager(engine='debug', verbose=True)
        topology.parse(topodesc)

        with caplog.at_level(logging.INFO, logger='topology.manager'):
            topology.build()

        log_messages = [record.message for record in caplog.records]

        node_add_messages = [msg for msg in log_messages
                             if '[VERBOSE] Adding node:' in msg]
        assert len(node_add_messages) == 4

        link_messages = [msg for msg in log_messages
                         if '[VERBOSE] Adding link:' in msg]
        assert len(link_messages) == 3

        topology.unbuild()
