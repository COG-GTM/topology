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
Test suite for module topology.pytest.plugin.

See http://pythontesting.net/framework/pytest/pytest-introduction/#fixtures
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

from pytest import mark

# Reload module to properly measure coverage
from six.moves import reload_module

import topology.pytest.plugin
from topology.manager import TopologyManager

reload_module(topology.pytest.plugin)

TOPOLOGY = """
# Nodes
[shell=vtysh name="Switch 1"] sw1
[shell=vtysh name="Switch 2"] sw2
[type=host name="Host 1"] hs1
[type=host name="Host 2"] hs2

# Links
hs1:1 -- sw1:1
hs2:1 -- sw2:1
[attr1=1] sw1:2 -- sw2:2
"""


@mark.test_id(1000)
def test_build(topology, pytestconfig):
    """
    Test automatic build and unbuild of the topology using pytest plugin.
    """
    assert pytestconfig.pluginmanager.getplugin('topology')
    assert isinstance(topology, TopologyManager)
    assert topology.get('sw1') is not None
    assert topology.get('sw2') is not None
    assert topology.get('hs1') is not None
    assert topology.get('hs2') is not None


@mark.test_id(1001)
@mark.skipif(True, reason='This test must always skip')
def test_skipped_test_id():
    """
    This test must be skipped always, it allows to test if a test_id is always
    recorded even when the test is skipped.
    """
    assert False


# FIXME: Find out how to test the presence of test_id in the previous test
# case, since after updating pytest to 3.0.4, config._xml has no tests
# attribute. The following code is the old test case:
# @mark.skipif(not hasattr(config, '_xml'), reason='XML output not enabled')
# def test_previous_has_test_id():
#     """
#     Test that previous test recorded the test_id.
#     """
#     assert hasattr(config, '_xml')
#     xml = str(config._xml.tests[-1])
#     assert '<property name="test_id" value="1001"/>' in xml


@mark.platform_incompatible(['debug'])
def test_incompatible_marker():
    """
    Test that the incompatible marker is interpreted.
    """
    assert False


@mark.platform_incompatible(['debug'], reason='Do not question my skips')
def test_incompatible_marker_with_reason():
    """
    Test that the incompatible marker is interpreted.
    """
    assert False


def test_step_fixture_returns_step_logger(step):
    """
    Test that the step fixture returns a StepLogger instance.

    The step fixture should provide a logger for recording test steps
    with proper context (test_suite and test_case).
    """
    from topology.logging import StepLogger

    assert isinstance(step, StepLogger), (
        f'step fixture should return StepLogger, got {type(step).__name__}'
    )


def test_step_fixture_is_callable(step):
    """
    Test that the step fixture is callable.

    The StepLogger implements __call__ for logging test steps.
    """
    assert callable(step), (
        'StepLogger should be callable (implements __call__)'
    )


def test_step_fixture_has_step_counter(step):
    """
    Test that the step fixture has a step counter attribute.

    The StepLogger tracks the current step number via the step attribute.
    """
    assert hasattr(step, 'step'), (
        'StepLogger should have step attribute'
    )
    assert isinstance(step.step, int), (
        f'StepLogger.step should be int, got {type(step.step).__name__}'
    )


def test_topology_plugin_pytest_report_header_output(pytestconfig):
    """
    Test that pytest_report_header returns properly formatted output.

    The header should include the platform name and optionally the log_dir.
    """
    plugin = pytestconfig._topology_plugin
    header = plugin.pytest_report_header(pytestconfig)

    assert header is not None, (
        'pytest_report_header should return a non-None value'
    )
    assert isinstance(header, str), (
        f'pytest_report_header should return str, got {type(header).__name__}'
    )
    assert 'topology:' in header, (
        'Header should contain "topology:" prefix'
    )
    assert f"platform='{plugin.platform}'" in header, (
        f'Header should contain platform name {plugin.platform!r}'
    )


def test_topology_plugin_destroy_topology_when_none(pytestconfig):
    """
    Test that destroy_topology handles None topomgr gracefully.

    When topomgr is None, destroy_topology should return early without error.
    """
    plugin = pytestconfig._topology_plugin

    original_topomgr = plugin.topomgr
    original_hash = plugin.curr_topology_hash

    try:
        plugin.topomgr = None
        plugin.curr_topology_hash = None

        plugin.destroy_topology()

        assert plugin.topomgr is None, (
            'topomgr should remain None after destroy_topology'
        )
        assert plugin.curr_topology_hash is None, (
            'curr_topology_hash should remain None after destroy_topology'
        )
    finally:
        plugin.topomgr = original_topomgr
        plugin.curr_topology_hash = original_hash


def test_topology_plugin_platform_matches_option(pytestconfig):
    """
    Test that the TopologyPlugin platform matches the CLI option.

    This verifies that the plugin is initialized with the correct
    platform value from the command line option.
    """
    plugin = pytestconfig._topology_plugin
    option_value = pytestconfig.getoption('--topology-platform')

    assert plugin.platform == option_value, (
        f'Plugin platform {plugin.platform!r} should match '
        f'option value {option_value!r}'
    )


def test_topology_szn_dir_option_type(pytestconfig):
    """
    Test that --topology-szn-dir option returns a list or None.

    The szn_dir option supports multiple values via append action,
    so it should return a list when specified or None when not.
    """
    value = pytestconfig.getoption('--topology-szn-dir')
    assert value is None or isinstance(value, list), (
        f'--topology-szn-dir should be None or list, '
        f'got {type(value).__name__}'
    )


def test_topology_plugin_szn_dir_type(pytestconfig):
    """
    Test that the TopologyPlugin szn_dir is a list or None.

    The szn_dir attribute should match the type of the CLI option.
    """
    plugin = pytestconfig._topology_plugin
    assert plugin.szn_dir is None or isinstance(plugin.szn_dir, list), (
        f'Plugin szn_dir should be None or list, '
        f'got {type(plugin.szn_dir).__name__}'
    )


def test_topology_platform_options_option_type(pytestconfig):
    """
    Test that --topology-platform-options returns None or list.

    The platform_options option supports multiple values via ExtendAction,
    so it should return a list when specified or None when not.
    """
    value = pytestconfig.getoption('--topology-platform-options')
    assert value is None or isinstance(value, list), (
        f'--topology-platform-options should be None or list, '
        f'got {type(value).__name__}'
    )


def test_topology_plugin_has_platform_attribute(pytestconfig):
    """
    Test that the TopologyPlugin has a platform attribute.

    The platform attribute holds the name of the platform engine to use.
    """
    plugin = pytestconfig._topology_plugin
    assert hasattr(plugin, 'platform'), (
        'Plugin should have platform attribute'
    )
    assert isinstance(plugin.platform, str), (
        f'Plugin platform should be str, got {type(plugin.platform).__name__}'
    )


def test_topology_plugin_topomgr_initial_state(pytestconfig):
    """
    Test that the TopologyPlugin topomgr can be None or TopologyManager.

    Before any topology is built, topomgr may be None. After building,
    it should be a TopologyManager instance.
    """
    from topology.manager import TopologyManager

    plugin = pytestconfig._topology_plugin
    topomgr = plugin.topomgr
    assert topomgr is None or isinstance(topomgr, TopologyManager), (
        f'Plugin topomgr should be None or TopologyManager, '
        f'got {type(topomgr).__name__}'
    )


def test_topology_plugin_curr_topology_hash_type(pytestconfig):
    """
    Test that curr_topology_hash is None or a valid hash type.

    The curr_topology_hash tracks the current topology for reuse logic.
    It should be None when no topology is built or a hash value otherwise.
    """
    plugin = pytestconfig._topology_plugin
    hash_val = plugin.curr_topology_hash

    assert hash_val is None or isinstance(hash_val, (str, int)), (
        f'curr_topology_hash should be None, str, or int, '
        f'got {type(hash_val).__name__}'
    )


def test_topology_plugin_curr_module_name_type(pytestconfig):
    """
    Test that curr_module_name is None or a string.

    The curr_module_name tracks the current module for topology reuse logic.
    """
    plugin = pytestconfig._topology_plugin
    module_name = plugin.curr_module_name

    assert module_name is None or isinstance(module_name, str), (
        f'curr_module_name should be None or str, '
        f'got {type(module_name).__name__}'
    )


def test_topology_group_by_topology_option_type(pytestconfig):
    """
    Test that --topology-group-by-topology returns a boolean.

    This option is a store_true action, so it should always be a boolean.
    """
    value = pytestconfig.getoption('--topology-group-by-topology')
    assert isinstance(value, bool), (
        f'--topology-group-by-topology should be bool, '
        f'got {type(value).__name__}'
    )


def test_topology_topologies_file_option_type(pytestconfig):
    """
    Test that --topology-topologies-file returns None or Path.

    When not specified, it should be None. When specified, it should be a Path.
    """
    from pathlib import Path

    value = pytestconfig.getoption('--topology-topologies-file')
    assert value is None or isinstance(value, Path), (
        f'--topology-topologies-file should be None or Path, '
        f'got {type(value).__name__}'
    )


def test_topology_build_retries_option_type(pytestconfig):
    """
    Test that --topology-build-retries returns an integer.

    This option has type=int, so it should always be an integer.
    """
    value = pytestconfig.getoption('--topology-build-retries')
    assert isinstance(value, int), (
        f'--topology-build-retries should be int, got {type(value).__name__}'
    )


def test_topology_build_retries_non_negative(pytestconfig):
    """
    Test that --topology-build-retries is non-negative.

    The plugin validates that build_retries cannot be less than 0.
    """
    value = pytestconfig.getoption('--topology-build-retries')
    assert value >= 0, (
        f'--topology-build-retries should be >= 0, got {value}'
    )
