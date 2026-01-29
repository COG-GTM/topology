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
Extended test suite for GitHub Actions workflow configuration.

These tests complement the base test_github_workflows.py by adding:
- Error handling and edge case tests
- Environment variable configuration tests
- HTTP request validation tests
- Workflow structure validation tests
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import os
import re

import pytest
import yaml


WORKFLOW_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    '.github', 'workflows', 'pr-review.yml'
)


@pytest.fixture
def workflow_content():
    """Load the workflow YAML file content."""
    with open(WORKFLOW_PATH, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def workflow_raw():
    """Load the raw workflow file content as string."""
    with open(WORKFLOW_PATH, 'r') as f:
        return f.read()


class TestWorkflowFileValidation:
    """Tests for workflow file existence and basic validation."""

    def test_workflow_file_is_readable(self):
        """Test that the workflow file can be read."""
        with open(WORKFLOW_PATH, 'r') as f:
            content = f.read()
        assert len(content) > 0

    def test_workflow_file_has_yaml_extension(self):
        """Test that the workflow file has .yml extension."""
        assert WORKFLOW_PATH.endswith('.yml')

    def test_workflow_file_is_in_correct_directory(self):
        """Test that the workflow file is in .github/workflows."""
        assert '.github/workflows' in WORKFLOW_PATH


class TestEnvironmentVariableConfiguration:
    """Tests for environment variable configuration in workflow steps."""

    def test_pr_files_step_has_github_token_env(self, workflow_content):
        """Test that PR files step has GITHUB_TOKEN environment variable."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        env = pr_files_step.get('env', {})
        assert 'GITHUB_TOKEN' in env

    def test_devin_session_step_has_devin_api_key_env(self, workflow_content):
        """Test that Devin session step has DEVIN_API_KEY env variable."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        assert 'DEVIN_API_KEY' in env, 'DEVIN_API_KEY env var missing'

    def test_devin_session_step_has_files_changed_env(self, workflow_content):
        """Test that Devin session step has FILES_CHANGED env variable."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        assert 'FILES_CHANGED' in env

    def test_devin_session_has_analysis_prompt_env(self, workflow_content):
        """Test that Devin session step has ANALYSIS_PROMPT env var."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        assert 'ANALYSIS_PROMPT' in env

    def test_post_comment_step_has_github_token_env(self, workflow_content):
        """Test that post comment step has GITHUB_TOKEN env variable."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        env = comment_step.get('env', {})
        assert 'GITHUB_TOKEN' in env


class TestHttpRequestConfiguration:
    """Tests for HTTP request configuration in workflow scripts."""

    def test_pr_files_curl_uses_get_method(self, workflow_content):
        """Test that PR files curl uses GET method (implicit)."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert 'curl' in script
        assert '-X POST' not in script.split('FILES_JSON')[0]

    def test_devin_session_curl_uses_post_method(self, workflow_raw):
        """Test that Devin session curl uses POST method."""
        assert '-X POST' in workflow_raw
        devin_section = workflow_raw.split('api.devin.ai')[0]
        assert '-X POST' in devin_section or 'POST' in devin_section

    def test_devin_session_curl_has_content_type_header(self, workflow_raw):
        """Test that Devin session curl has Content-Type header."""
        assert 'Content-Type: application/json' in workflow_raw

    def test_post_comment_curl_uses_post_method(self, workflow_content):
        """Test that post comment curl uses POST method."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        script = comment_step.get('run', '')
        assert '-X POST' in script

    def test_curl_commands_use_silent_flag(self, workflow_raw):
        """Test that curl commands use -s (silent) flag."""
        curl_count = workflow_raw.count('curl')
        silent_curl_count = workflow_raw.count('curl -s')
        assert silent_curl_count >= curl_count - 1


class TestWorkflowNameConfiguration:
    """Tests for workflow name configuration."""

    def test_workflow_name_is_descriptive(self, workflow_content):
        """Test that workflow name describes its purpose."""
        name = workflow_content['name']
        assert 'test' in name.lower() or 'plan' in name.lower()

    def test_workflow_name_is_not_empty(self, workflow_content):
        """Test that workflow name is not empty."""
        name = workflow_content['name']
        assert len(name.strip()) > 0


class TestJobStepOrdering:
    """Tests for correct ordering of workflow steps."""

    def test_checkout_is_first_step(self, workflow_content):
        """Test that checkout is the first step."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        first_step = steps[0]
        assert 'checkout' in first_step.get('uses', '').lower()

    def test_pr_files_comes_before_devin_session(self, workflow_content):
        """Test that PR files step comes before Devin session step."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_idx = None
        devin_idx = None

        for i, step in enumerate(steps):
            if step.get('name') == 'Get PR files':
                pr_files_idx = i
            if 'devin' in step.get('name', '').lower() and \
               'session' in step.get('name', '').lower():
                devin_idx = i

        assert pr_files_idx is not None
        assert devin_idx is not None
        assert pr_files_idx < devin_idx

    def test_devin_session_comes_before_post_comment(self, workflow_content):
        """Test that Devin session step comes before post comment step."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_idx = None
        comment_idx = None

        for i, step in enumerate(steps):
            if step.get('id') == 'devin-session':
                devin_idx = i
            name = step.get('name', '').lower()
            if 'post' in name and 'comment' in name:
                comment_idx = i

        assert devin_idx is not None
        assert comment_idx is not None
        assert devin_idx < comment_idx


class TestPromptStructure:
    """Tests for the Devin prompt structure and content."""

    def test_prompt_has_repository_placeholder(self, workflow_raw):
        """Test that prompt includes repository placeholder."""
        assert 'github.repository' in workflow_raw

    def test_prompt_has_pr_number_placeholder(self, workflow_raw):
        """Test that prompt includes PR number placeholder."""
        assert 'github.event.pull_request.number' in workflow_raw

    def test_prompt_has_numbered_tasks(self, workflow_raw):
        """Test that prompt has numbered task list."""
        assert '1.' in workflow_raw
        assert '2.' in workflow_raw
        assert '3.' in workflow_raw

    def test_prompt_mentions_clone_repository(self, workflow_raw):
        """Test that prompt mentions cloning the repository."""
        assert 'clone' in workflow_raw.lower()

    def test_prompt_mentions_view_pr(self, workflow_raw):
        """Test that prompt mentions viewing the PR."""
        assert 'view' in workflow_raw.lower()
        assert 'pr' in workflow_raw.lower()

    def test_prompt_mentions_analyze(self, workflow_raw):
        """Test that prompt mentions analyzing changes."""
        assert 'analyze' in workflow_raw.lower()


class TestErrorHandlingPatterns:
    """Tests for error handling patterns in workflow scripts."""

    def test_pr_files_checks_empty_response(self, workflow_content):
        """Test that PR files script checks for empty response."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert '-z' in script or 'empty' in script.lower() or '[]' in script

    def test_devin_session_checks_error_response(self, workflow_content):
        """Test that Devin session script checks for error response."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert 'detail' in script or 'error' in script.lower()

    def test_devin_session_checks_missing_session_info(self, workflow_content):
        """Test that Devin session script checks for missing session info."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert 'SESSION_ID' in script or 'session_id' in script
        assert 'SESSION_URL' in script or 'session-url' in script


class TestGitHubOutputFormat:
    """Tests for GitHub Actions output format."""

    def test_pr_files_uses_github_output_format(self, workflow_content):
        """Test that PR files step uses correct GITHUB_OUTPUT format."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert 'GITHUB_OUTPUT' in script
        assert '>>' in script

    def test_devin_session_uses_github_output_format(self, workflow_content):
        """Test that Devin session step uses correct GITHUB_OUTPUT format."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert 'GITHUB_OUTPUT' in script
        assert '>>' in script


class TestStepOutputReferences:
    """Tests for step output references between steps."""

    def test_devin_session_references_pr_files_output(self, workflow_content):
        """Test that Devin session step references PR files output."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        files_changed = env.get('FILES_CHANGED', '')
        assert 'steps.pr-files.outputs.files' in files_changed

    def test_post_comment_references_devin_session_output(
        self, workflow_content
    ):
        """Test that post comment step references Devin session output."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        script = comment_step.get('run', '')
        assert 'steps.devin-session.outputs' in script


class TestSecurityConfiguration:
    """Tests for security-related configuration."""

    def test_github_token_uses_secrets_context(self, workflow_raw):
        """Test that GITHUB_TOKEN uses secrets context."""
        assert 'secrets.GITHUB_TOKEN' in workflow_raw

    def test_devin_api_key_uses_secrets_context(self, workflow_raw):
        """Test that DEVIN_API_KEY uses secrets context."""
        assert 'secrets.DEVIN_API_KEY' in workflow_raw

    def test_no_hardcoded_tokens(self, workflow_raw):
        """Test that there are no hardcoded tokens in the workflow."""
        token_patterns = [
            r'ghp_[a-zA-Z0-9]{36}',
            r'github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}',
            r'gho_[a-zA-Z0-9]{36}',
        ]
        for pattern in token_patterns:
            assert not re.search(pattern, workflow_raw)


class TestWorkflowYamlSyntax:
    """Tests for YAML syntax correctness."""

    def test_workflow_has_no_duplicate_keys(self, workflow_raw):
        """Test that workflow has no duplicate keys at top level."""
        lines = workflow_raw.split('\n')
        top_level_keys = []
        for line in lines:
            if line and not line.startswith(' ') and ':' in line:
                key = line.split(':')[0].strip()
                if key and not key.startswith('#'):
                    top_level_keys.append(key)
        assert len(top_level_keys) == len(set(top_level_keys))

    def test_workflow_top_level_indentation_is_consistent(self, workflow_raw):
        """Test that workflow top-level keys use consistent indentation."""
        lines = workflow_raw.split('\n')
        for line in lines:
            stripped = line.lstrip()
            if stripped and not stripped.startswith('#'):
                leading_spaces = len(line) - len(stripped)
                if leading_spaces > 0 and leading_spaces <= 6:
                    assert leading_spaces % 2 == 0


class TestApiEndpointPatterns:
    """Tests for API endpoint URL patterns."""

    def test_github_api_uses_https(self, workflow_raw):
        """Test that GitHub API calls use HTTPS."""
        github_api_calls = re.findall(
            r'(https?://api\.github\.com[^\s"\']*)', workflow_raw
        )
        for url in github_api_calls:
            assert url.startswith('https://')

    def test_devin_api_uses_https(self, workflow_raw):
        """Test that Devin API calls use HTTPS."""
        devin_api_calls = re.findall(
            r'(https?://api\.devin\.ai[^\s"\']*)', workflow_raw
        )
        for url in devin_api_calls:
            assert url.startswith('https://')

    def test_github_api_endpoint_includes_repo_variable(self, workflow_raw):
        """Test that GitHub API endpoints include repository variable."""
        assert 'github.repository' in workflow_raw
