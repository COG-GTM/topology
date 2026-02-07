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


def test_documented_pytest_flags_are_registered(pytestconfig):
    """
    Test that documented pytest plugin flags are properly registered.

    This test verifies that the flags documented in doc/user.rst are
    registered and can be retrieved without raising ValueError.
    """
    documented_flags = [
        '--topology-platform',
        '--topology-inject',
        '--topology-log-dir',
        '--topology-szn-dir',
        '--topology-platform-options',
        '--topology-build-retries',
        '--topology-group-by-topology',
        '--topology-topologies-file',
    ]

    for flag in documented_flags:
        try:
            pytestconfig.getoption(flag)
        except ValueError:
            raise AssertionError(
                f'Documented flag {flag} is not registered in pytest plugin'
            )


def test_topology_build_retries_type(pytestconfig):
    """
    Test that --topology-build-retries is registered as an integer type.

    This test verifies that the build retries option is properly typed
    as an integer, which is important for the retry logic in the plugin.
    """
    value = pytestconfig.getoption('--topology-build-retries')
    assert isinstance(value, int), (
        f'--topology-build-retries should be int, got {type(value).__name__}'
    )


def test_topology_group_by_topology_is_boolean(pytestconfig):
    """
    Test that --topology-group-by-topology is registered as a boolean flag.

    This test verifies that the group-by-topology option is properly typed
    as a boolean, which is important for the grouping logic in the plugin.
    """
    value = pytestconfig.getoption('--topology-group-by-topology')
    assert isinstance(value, bool), (
        '--topology-group-by-topology should be bool, '
        f'got {type(value).__name__}'
    )


def test_topology_szn_dir_accepts_multiple_values(pytestconfig):
    """
    Test that --topology-szn-dir can accept multiple values via append action.

    This test verifies that the szn-dir option is configured to accept
    multiple directory paths, which is documented behavior.
    """
    value = pytestconfig.getoption('--topology-szn-dir')
    assert value is None or isinstance(value, list), (
        '--topology-szn-dir should be None or list, '
        f'got {type(value).__name__}'
    )


def test_topology_platform_options_accepts_multiple_values(pytestconfig):
    """
    Test that --topology-platform-options can accept multiple key=value pairs.

    This test verifies that the platform-options option is configured to
    accept multiple arguments, which is documented behavior.
    """
    value = pytestconfig.getoption('--topology-platform-options')
    assert value is None or isinstance(value, list), (
        f'--topology-platform-options should be None or list, '
        f'got {type(value).__name__}'
    )


def test_topology_plugin_registered(pytestconfig):
    """
    Test that the topology plugin is properly registered with pytest.

    This test verifies that the TopologyPlugin instance is accessible
    via the config and has the expected attributes.
    """
    plugin = pytestconfig._topology_plugin
    assert plugin is not None, 'Topology plugin should be registered'
    assert plugin.__class__.__name__ == 'TopologyPlugin', (
        'Plugin should be TopologyPlugin instance'
    )

    assert hasattr(plugin, 'platform'), 'Plugin should have platform attribute'
    assert hasattr(plugin, 'log_dir'), 'Plugin should have log_dir attribute'
    assert hasattr(plugin, 'szn_dir'), 'Plugin should have szn_dir attribute'
    assert hasattr(plugin, 'build_retries'), (
        'Plugin should have build_retries attribute'
    )


def test_topology_plugin_platform_matches_option(pytestconfig):
    """
    Test that the TopologyPlugin platform matches --topology-platform option.

    This test verifies that the plugin is initialized with the correct
    platform value from the command line option.
    """
    plugin = pytestconfig._topology_plugin
    option_value = pytestconfig.getoption('--topology-platform')

    assert plugin.platform == option_value, (
        f'Plugin platform {plugin.platform!r} should match '
        f'option value {option_value!r}'
    )
