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


def test_topology_platform_default_value(pytestconfig):
    """
    Test that --topology-platform has the expected default value.

    The default platform should be 'debug' as defined in
    topology.platforms.manager.DEFAULT_PLATFORM.
    """
    from topology.platforms.manager import DEFAULT_PLATFORM

    value = pytestconfig.getoption('--topology-platform')
    assert value == DEFAULT_PLATFORM, (
        f'--topology-platform default should be {DEFAULT_PLATFORM!r}, '
        f'got {value!r}'
    )


def test_topology_inject_default_value(pytestconfig):
    """
    Test that --topology-inject has None as default value.

    When no injection file is specified, the option should be None.
    """
    value = pytestconfig.getoption('--topology-inject')
    assert value is None, (
        f'--topology-inject default should be None, got {value!r}'
    )


def test_topology_log_dir_default_value(pytestconfig):
    """
    Test that --topology-log-dir has None as default value.

    When no log directory is specified, the option should be None.
    """
    value = pytestconfig.getoption('--topology-log-dir')
    assert value is None, (
        f'--topology-log-dir default should be None, got {value!r}'
    )


def test_topology_build_retries_default_value(pytestconfig):
    """
    Test that --topology-build-retries has 0 as default value.

    The default should be 0, meaning no retries by default.
    """
    value = pytestconfig.getoption('--topology-build-retries')
    assert value == 0, (
        f'--topology-build-retries default should be 0, got {value!r}'
    )


def test_topology_group_by_topology_default_value(pytestconfig):
    """
    Test that --topology-group-by-topology has False as default value.

    The default should be False, meaning tests are not grouped by topology.
    """
    value = pytestconfig.getoption('--topology-group-by-topology')
    assert value is False, (
        f'--topology-group-by-topology default should be False, got {value!r}'
    )


def test_topology_topologies_file_default_value(pytestconfig):
    """
    Test that --topology-topologies-file has None as default value.

    When no topologies file is specified, the option should be None.
    """
    value = pytestconfig.getoption('--topology-topologies-file')
    assert value is None, (
        f'--topology-topologies-file default should be None, got {value!r}'
    )


def test_topology_plugin_injected_attr_initialization(pytestconfig):
    """
    Test that the TopologyPlugin injected_attr is properly initialized.

    When no injection file is provided, injected_attr should be None.
    """
    plugin = pytestconfig._topology_plugin
    assert plugin.injected_attr is None, (
        'Plugin injected_attr should be None when no injection file provided'
    )


def test_topology_plugin_platform_options_initialization(pytestconfig):
    """
    Test that the TopologyPlugin platform_options is properly initialized.

    When no platform options are provided, platform_options should be
    an empty dict (after parsing None through parse_options).
    """
    plugin = pytestconfig._topology_plugin
    assert isinstance(plugin.platform_options, dict), (
        f'Plugin platform_options should be dict, '
        f'got {type(plugin.platform_options).__name__}'
    )


def test_topology_plugin_build_retries_matches_option(pytestconfig):
    """
    Test that the TopologyPlugin build_retries matches the CLI option.

    This verifies that the plugin is initialized with the correct
    build_retries value from the command line option.
    """
    plugin = pytestconfig._topology_plugin
    option_value = pytestconfig.getoption('--topology-build-retries')

    assert plugin.build_retries == option_value, (
        f'Plugin build_retries {plugin.build_retries!r} should match '
        f'option value {option_value!r}'
    )


def test_topology_plugin_log_dir_matches_option(pytestconfig):
    """
    Test that the TopologyPlugin log_dir matches the CLI option.

    This verifies that the plugin is initialized with the correct
    log_dir value from the command line option.
    """
    plugin = pytestconfig._topology_plugin
    option_value = pytestconfig.getoption('--topology-log-dir')

    assert plugin.log_dir == option_value, (
        f'Plugin log_dir {plugin.log_dir!r} should match '
        f'option value {option_value!r}'
    )


def test_topology_plugin_szn_dir_matches_option(pytestconfig):
    """
    Test that the TopologyPlugin szn_dir matches the CLI option.

    This verifies that the plugin is initialized with the correct
    szn_dir value from the command line option.
    """
    plugin = pytestconfig._topology_plugin
    option_value = pytestconfig.getoption('--topology-szn-dir')

    assert plugin.szn_dir == option_value, (
        f'Plugin szn_dir {plugin.szn_dir!r} should match '
        f'option value {option_value!r}'
    )


def test_topology_plugin_has_topomgr_attribute(pytestconfig):
    """
    Test that the TopologyPlugin has a topomgr attribute.

    The topomgr attribute holds the TopologyManager instance and should
    exist on the plugin (may be None if no topology has been built yet).
    """
    plugin = pytestconfig._topology_plugin
    assert hasattr(plugin, 'topomgr'), (
        'Plugin should have topomgr attribute'
    )


def test_topology_plugin_has_curr_topology_hash_attribute(pytestconfig):
    """
    Test that the TopologyPlugin has a curr_topology_hash attribute.

    The curr_topology_hash attribute tracks the current topology hash
    for reuse optimization.
    """
    plugin = pytestconfig._topology_plugin
    assert hasattr(plugin, 'curr_topology_hash'), (
        'Plugin should have curr_topology_hash attribute'
    )


def test_topology_plugin_has_curr_module_name_attribute(pytestconfig):
    """
    Test that the TopologyPlugin has a curr_module_name attribute.

    The curr_module_name attribute tracks the current module name
    for topology reuse logic.
    """
    plugin = pytestconfig._topology_plugin
    assert hasattr(plugin, 'curr_module_name'), (
        'Plugin should have curr_module_name attribute'
    )


def test_topology_plugin_has_destroy_topology_method(pytestconfig):
    """
    Test that the TopologyPlugin has a destroy_topology method.

    The destroy_topology method is used to clean up the topology
    when the session ends or when a new topology is built.
    """
    plugin = pytestconfig._topology_plugin
    assert hasattr(plugin, 'destroy_topology'), (
        'Plugin should have destroy_topology method'
    )
    assert callable(plugin.destroy_topology), (
        'Plugin destroy_topology should be callable'
    )


def test_topology_plugin_has_pytest_report_header_method(pytestconfig):
    """
    Test that the TopologyPlugin has a pytest_report_header method.

    This method is a pytest hook that prints information in the report header.
    """
    plugin = pytestconfig._topology_plugin
    assert hasattr(plugin, 'pytest_report_header'), (
        'Plugin should have pytest_report_header method'
    )
    assert callable(plugin.pytest_report_header), (
        'Plugin pytest_report_header should be callable'
    )
