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


def test_obsolete_args_error_message_content(tmpdir):
    """
    Test that the error message for obsolete arguments contains helpful
    information about the unrecognized argument.
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
        stderr_capture = StringIO()
        with pytest.raises(SystemExit):
            old_stderr = sys.stderr
            sys.stderr = stderr_capture
            try:
                parse_args([str(topology), arg_name, arg_value])
            finally:
                sys.stderr = old_stderr

        error_output = stderr_capture.getvalue()
        assert 'unrecognized arguments' in error_output, (
            f'Error message for {arg_name} should mention '
            f'"unrecognized arguments"'
        )
        assert arg_name in error_output, (
            f'Error message should contain the argument name {arg_name}'
        )


def test_obsolete_args_with_equals_syntax(tmpdir):
    """
    Test that obsolete arguments using the --arg=value syntax are also
    rejected by the argument parser.
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    obsolete_args_with_equals = [
        '--plot-dir=/tmp/plots',
        '--plot-format=png',
        '--nml-dir=/tmp/nml',
    ]

    for arg in obsolete_args_with_equals:
        with pytest.raises(SystemExit) as exc_info:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                parse_args([str(topology), arg])
            finally:
                sys.stderr = old_stderr
        assert exc_info.value.code == 2, (
            f'Expected SystemExit with code 2 for unrecognized argument '
            f'{arg}, got {exc_info.value.code}'
        )


def test_obsolete_args_combined_with_valid_args(tmpdir):
    """
    Test that combining obsolete arguments with valid arguments still
    results in rejection of the obsolete arguments.
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    test_cases = [
        ['-v', '--plot-dir', '/tmp/plots'],
        ['--platform=debug', '--plot-format', 'png'],
        ['--non-interactive', '--nml-dir', '/tmp/nml'],
        ['-vvv', '--platform=debug', '--plot-dir', '/tmp/plots'],
    ]

    for args_list in test_cases:
        full_args = [str(topology)] + args_list
        with pytest.raises(SystemExit) as exc_info:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                parse_args(full_args)
            finally:
                sys.stderr = old_stderr
        assert exc_info.value.code == 2, (
            f'Expected SystemExit with code 2 for args {args_list}, '
            f'got {exc_info.value.code}'
        )


def test_valid_args_still_work_after_obsolete_removal(tmpdir):
    """
    Regression test to ensure that all valid arguments still work correctly
    after the removal of obsolete arguments.
    """
    topology = tmpdir.join('topology.szn')
    topology.write('')

    log_dir = tmpdir.mkdir('logs')

    parsed = parse_args([
        str(topology),
        '-v',
        '--platform=debug',
        '--log-dir', str(log_dir),
        '--non-interactive',
    ])

    assert parsed.verbose == 1
    assert parsed.platform == 'debug'
    assert parsed.log_dir == str(log_dir)
    assert parsed.non_interactive is True


def test_valid_args_with_options_after_obsolete_removal(tmpdir):
    """
    Regression test to ensure that the --option argument still works
    correctly after the removal of obsolete arguments.
    """
    topology = tmpdir.join('topology.szn')
    topology.write('')

    parsed = parse_args([
        str(topology),
        '--option', 'key1=value1', 'key2=100', 'key3=true',
    ])

    assert parsed.options['key1'] == 'value1'
    assert parsed.options['key2'] == 100
    assert parsed.options['key3'] is True


def test_help_contains_valid_args(tmpdir):
    """
    Test that the --help output still contains all valid arguments
    after the removal of obsolete arguments.
    """
    from subprocess import run
    from sys import executable

    completed = run(
        [executable, '-m', 'topology', '--help'],
        encoding='utf-8',
        capture_output=True,
    )

    assert completed.returncode == 0, 'topology --help failed'

    valid_args = [
        '--verbose',
        '--version',
        '--platform',
        '--option',
        '--log-dir',
        '--inject',
        '--non-interactive',
    ]
    for arg in valid_args:
        assert arg in completed.stdout, (
            f'Valid argument {arg} should appear in --help output'
        )


def test_multiple_obsolete_args_all_rejected(tmpdir):
    """
    Test that providing multiple obsolete arguments at once still results
    in rejection (the parser should fail on the first unrecognized argument).
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    with pytest.raises(SystemExit) as exc_info:
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            parse_args([
                str(topology),
                '--plot-dir', '/tmp/plots',
                '--plot-format', 'png',
                '--nml-dir', '/tmp/nml',
            ])
        finally:
            sys.stderr = old_stderr
    assert exc_info.value.code == 2, (
        f'Expected SystemExit with code 2 for multiple obsolete arguments, '
        f'got {exc_info.value.code}'
    )


def test_obsolete_args_case_sensitivity(tmpdir):
    """
    Test that case variations of obsolete arguments are also rejected.
    argparse is case-sensitive by default, so --Plot-Dir should be rejected
    as an unrecognized argument (not matched to any valid argument).
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    case_variations = [
        '--Plot-Dir',
        '--PLOT-DIR',
        '--Plot-Format',
        '--PLOT-FORMAT',
        '--Nml-Dir',
        '--NML-DIR',
    ]

    for arg in case_variations:
        with pytest.raises(SystemExit) as exc_info:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                parse_args([str(topology), arg, '/tmp/value'])
            finally:
                sys.stderr = old_stderr
        assert exc_info.value.code == 2, (
            f'Expected SystemExit with code 2 for case variation {arg}, '
            f'got {exc_info.value.code}'
        )


def test_obsolete_args_prefix_not_matched(tmpdir):
    """
    Test that partial/prefix versions of obsolete argument names are rejected.
    This ensures that argparse prefix matching doesn't accidentally accept
    shortened forms of the removed arguments.
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    prefix_variations = [
        '--plot',
        '--plot-',
        '--nml',
        '--nml-',
    ]

    for arg in prefix_variations:
        with pytest.raises(SystemExit) as exc_info:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                parse_args([str(topology), arg, '/tmp/value'])
            finally:
                sys.stderr = old_stderr
        assert exc_info.value.code == 2, (
            f'Expected SystemExit with code 2 for prefix {arg}, '
            f'got {exc_info.value.code}'
        )


def test_obsolete_args_do_not_consume_topology_file(tmpdir):
    """
    Test that obsolete arguments placed before the topology file don't
    interfere with the required positional argument parsing.
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    with pytest.raises(SystemExit) as exc_info:
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            parse_args(['--plot-dir', '/tmp/plots', str(topology)])
        finally:
            sys.stderr = old_stderr
    assert exc_info.value.code == 2, (
        f'Expected SystemExit with code 2 when obsolete arg precedes '
        f'topology file, got {exc_info.value.code}'
    )


def test_obsolete_args_exit_code_consistency(tmpdir):
    """
    Test that all obsolete arguments produce the same exit code (2) which
    is the standard argparse exit code for unrecognized arguments.
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    obsolete_args = ['--plot-dir', '--plot-format', '--nml-dir']
    exit_codes = []

    for arg in obsolete_args:
        with pytest.raises(SystemExit) as exc_info:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                parse_args([str(topology), arg, 'value'])
            finally:
                sys.stderr = old_stderr
        exit_codes.append(exc_info.value.code)

    assert all(code == 2 for code in exit_codes), (
        f'All obsolete arguments should produce exit code 2, '
        f'but got: {dict(zip(obsolete_args, exit_codes))}'
    )
    assert len(set(exit_codes)) == 1, (
        'All obsolete arguments should produce consistent exit codes'
    )


def test_obsolete_args_with_special_value_types(tmpdir):
    """
    Test that obsolete arguments with various special value types
    (paths with spaces, empty values, unicode) are still rejected.
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    special_values = [
        ('--plot-dir', '/path/with spaces/plots'),
        ('--plot-dir', ''),
        ('--plot-format', 'png\u00e9'),
        ('--nml-dir', '/tmp/nml/\u4e2d\u6587'),
        ('--plot-dir', '/tmp/path with\ttab'),
    ]

    for arg_name, arg_value in special_values:
        with pytest.raises(SystemExit) as exc_info:
            old_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                parse_args([str(topology), arg_name, arg_value])
            finally:
                sys.stderr = old_stderr
        assert exc_info.value.code == 2, (
            f'Expected SystemExit with code 2 for {arg_name} with value '
            f'{repr(arg_value)}, got {exc_info.value.code}'
        )


def test_obsolete_args_do_not_interfere_with_help(tmpdir):
    """
    Test that --help still works correctly and obsolete arguments
    don't interfere with the help display.
    """
    from subprocess import run
    from sys import executable

    completed = run(
        [executable, '-m', 'topology', '--help'],
        encoding='utf-8',
        capture_output=True,
    )

    assert completed.returncode == 0, 'topology --help should succeed'
    assert 'topology' in completed.stdout.lower(), (
        '--help output should contain program description'
    )
    assert '--plot-dir' not in completed.stdout, (
        'Obsolete --plot-dir should not appear in help'
    )
    assert '--plot-format' not in completed.stdout, (
        'Obsolete --plot-format should not appear in help'
    )
    assert '--nml-dir' not in completed.stdout, (
        'Obsolete --nml-dir should not appear in help'
    )


def test_obsolete_args_do_not_interfere_with_version():
    """
    Test that --version still works correctly and obsolete arguments
    don't interfere with the version display.
    """
    from subprocess import run
    from sys import executable

    completed = run(
        [executable, '-m', 'topology', '--version'],
        encoding='utf-8',
        capture_output=True,
    )

    assert completed.returncode == 0, 'topology --version should succeed'
    assert 'topology' in completed.stdout.lower() or 'v' in completed.stdout, (
        '--version output should contain version information'
    )


def test_obsolete_args_stderr_format_consistency(tmpdir):
    """
    Test that the stderr error format is consistent across all obsolete
    arguments, following argparse conventions.
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

    error_outputs = []
    for arg_name, arg_value in obsolete_args:
        stderr_capture = StringIO()
        with pytest.raises(SystemExit):
            old_stderr = sys.stderr
            sys.stderr = stderr_capture
            try:
                parse_args([str(topology), arg_name, arg_value])
            finally:
                sys.stderr = old_stderr
        error_outputs.append((arg_name, stderr_capture.getvalue()))

    for arg_name, error_output in error_outputs:
        assert 'usage:' in error_output.lower(), (
            f'Error for {arg_name} should include usage information'
        )
        assert 'error:' in error_output.lower(), (
            f'Error for {arg_name} should include error prefix'
        )


def test_obsolete_args_with_double_dash_separator(tmpdir):
    """
    Test that obsolete arguments after -- separator are treated as
    positional arguments (standard argparse behavior).
    """
    from io import StringIO
    import sys

    topology = tmpdir.join('topology.szn')
    topology.write('')

    with pytest.raises(SystemExit) as exc_info:
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            parse_args([str(topology), '--', '--plot-dir'])
        finally:
            sys.stderr = old_stderr
    assert exc_info.value.code == 2, (
        'Arguments after -- should be treated as positional and cause error'
    )
