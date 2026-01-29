# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Hewlett Packard Enterprise Development LP
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
Test suite for module topology.args.

See http://pythontesting.net/framework/pytest/pytest-introduction/#fixtures
"""

from collections import OrderedDict

import pytest  # noqa
from deepdiff import DeepDiff

from topology.args import parse_args, InvalidArgument


def setup_module(module):
    print('setup_module({})'.format(module.__name__))


def teardown_module(module):
    print('teardown_module({})'.format(module.__name__))


def test_args(tmpdir):

    with pytest.raises(InvalidArgument):
        parse_args(['/this/doesnt/exists.szn'])

    topology = tmpdir.join('topology.szn')
    topology.write('')

    parsed = parse_args([str(topology)])
    assert parsed.verbose == 0

    parsed = parse_args(['-v', str(topology)])
    assert parsed.verbose == 1

    parsed = parse_args(['-vv', str(topology)])
    assert parsed.verbose == 2

    parsed = parse_args(['-vvv', str(topology)])
    assert parsed.verbose == 3

    # Validate option parsing
    with pytest.raises(InvalidArgument):
        parsed = parse_args([
            str(topology),
            '--option', '1argument=100',
        ])

    with pytest.raises(InvalidArgument):
        parsed = parse_args([
            str(topology),
            '--option', '$argument=100',
        ])

    parsed = parse_args([
        str(topology),
        '--option', 'var-1=Yes', 'var2=no', 'var_3=TRUE', 'var4=100',
        '--option', 'var4=200', 'var5=helloworld', 'var6=/tmp/a/path',
        '--option', 'var7=1.7560',
    ])

    expected = OrderedDict([
        ('var_1', True),
        ('var2', False),
        ('var_3', True),
        ('var4', 200),
        ('var5', 'helloworld'),
        ('var6', '/tmp/a/path'),
        ('var7', 1.7560),
    ])

    ddiff = DeepDiff(parsed.options, expected)
    assert not ddiff


def test_obsolete_args_removed(tmpdir):
    """
    Test that obsolete CLI arguments (--plot-dir, --plot-format, --nml-dir)
    are no longer recognized by the argument parser.
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    obsolete_args = [
        ('--plot-dir', '/tmp/plots'),
        ('--plot-format', 'png'),
        ('--nml-dir', '/tmp/nml'),
    ]

    for arg_name, arg_value in obsolete_args:
        with pytest.raises(SystemExit) as exc_info:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                parse_args([str(topology), arg_name, arg_value])
            finally:
                sys.stderr = old_stderr
        assert exc_info.value.code == 2, (
            f'Expected SystemExit with code 2 for unrecognized argument '
            f'{arg_name}, got {exc_info.value.code}'
        )


def test_help_does_not_contain_obsolete_args(tmpdir):
    """
    Test that the --help output does not contain references to obsolete
    arguments (--plot-dir, --plot-format, --nml-dir).
    """
    from subprocess import run
    from sys import executable

    topology = tmpdir.join('topology.szn')
    topology.write('')

    completed = run(
        [executable, '-m', 'topology', '--help'],
        encoding='utf-8',
        capture_output=True,
    )

    assert completed.returncode == 0, 'topology --help failed'

    obsolete_args = ['--plot-dir', '--plot-format', '--nml-dir']
    for arg in obsolete_args:
        assert arg not in completed.stdout, (
            f'Obsolete argument {arg} should not appear in --help output'
        )


def test_main_no_deprecation_warnings(tmpdir):
    """
    Test that the main function runs without emitting deprecation warnings
    for the removed obsolete arguments.
    """
    import warnings
    from topology import args, __main__ as main

    test_topology = """\
# Nodes
[type=host name="Host 1"] hs1
"""

    topology = tmpdir.join('topology.szn')
    topology.write(test_topology)

    arguments = ['--platform=debug', '--non-interactive', str(topology)]
    parsed_args = args.parse_args(arguments)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = main.main(parsed_args)

        deprecation_warnings = [
            warning for warning in w
            if issubclass(warning.category, DeprecationWarning)
            and any(
                arg in str(warning.message)
                for arg in ['--plot-dir', '--nml-dir']
            )
        ]

        assert len(deprecation_warnings) == 0, (
            f'Expected no deprecation warnings for obsolete arguments, '
            f'but got: {[str(w.message) for w in deprecation_warnings]}'
        )

    assert result == 0
