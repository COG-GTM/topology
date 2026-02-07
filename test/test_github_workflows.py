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
Test suite for GitHub Actions workflow configuration.

Tests the pr-review.yml workflow that creates Devin sessions for
analyzing PRs, generating test plans, and implementing tests.
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import os
import re
import subprocess

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


class TestWorkflowStructure:
    """Tests for the workflow YAML structure and syntax."""

    def test_workflow_file_exists(self):
        """Test that the workflow file exists."""
        assert os.path.exists(WORKFLOW_PATH), (
            f"Workflow file not found at {WORKFLOW_PATH}"
        )

    def test_workflow_is_valid_yaml(self, workflow_content):
        """Test that the workflow file is valid YAML."""
        assert workflow_content is not None
        assert isinstance(workflow_content, dict)

    def test_workflow_has_name(self, workflow_content):
        """Test that the workflow has a name."""
        assert 'name' in workflow_content
        assert workflow_content['name']

    def test_workflow_has_trigger(self, workflow_content):
        """Test that the workflow has trigger configuration."""
        # YAML parses 'on' as boolean True, so check for both
        trigger_key = 'on' if 'on' in workflow_content else True
        assert trigger_key in workflow_content
        assert 'pull_request' in workflow_content[trigger_key]

    def test_workflow_has_jobs(self, workflow_content):
        """Test that the workflow has jobs defined."""
        assert 'jobs' in workflow_content
        assert len(workflow_content['jobs']) > 0


class TestWorkflowTriggers:
    """Tests for workflow trigger configuration."""

    def test_pull_request_trigger_types(self, workflow_content):
        """Test that PR trigger includes required event types."""
        # YAML parses 'on' as boolean True
        trigger_key = 'on' if 'on' in workflow_content else True
        pr_config = workflow_content[trigger_key]['pull_request']
        assert 'types' in pr_config

        types = pr_config['types']
        assert 'opened' in types
        assert 'synchronize' in types
        assert 'reopened' in types

    def test_no_push_trigger(self, workflow_content):
        """Test that workflow does not trigger on push events."""
        # YAML parses 'on' as boolean True
        trigger_key = 'on' if 'on' in workflow_content else True
        assert 'push' not in workflow_content[trigger_key]


class TestWorkflowPermissions:
    """Tests for workflow permissions configuration."""

    def test_has_permissions(self, workflow_content):
        """Test that permissions are defined."""
        assert 'permissions' in workflow_content

    def test_contents_read_permission(self, workflow_content):
        """Test that contents read permission is set."""
        permissions = workflow_content['permissions']
        assert permissions.get('contents') == 'read'

    def test_pull_requests_write_permission(self, workflow_content):
        """Test that pull-requests write permission is set."""
        permissions = workflow_content['permissions']
        assert permissions.get('pull-requests') == 'write'

    def test_issues_read_permission(self, workflow_content):
        """Test that issues read permission is set."""
        permissions = workflow_content['permissions']
        assert permissions.get('issues') == 'read'


class TestJobConfiguration:
    """Tests for job configuration."""

    def test_generate_test_plan_job_exists(self, workflow_content):
        """Test that generate-test-plan job exists."""
        assert 'generate-test-plan' in workflow_content['jobs']

    def test_job_runs_on_ubuntu(self, workflow_content):
        """Test that job runs on ubuntu-latest."""
        job = workflow_content['jobs']['generate-test-plan']
        assert job['runs-on'] == 'ubuntu-latest'

    def test_job_has_steps(self, workflow_content):
        """Test that job has steps defined."""
        job = workflow_content['jobs']['generate-test-plan']
        assert 'steps' in job
        assert len(job['steps']) >= 4


class TestWorkflowSteps:
    """Tests for individual workflow steps."""

    def test_checkout_step_exists(self, workflow_content):
        """Test that checkout step exists."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        checkout_steps = [s for s in steps if s.get('uses', '').startswith(
            'actions/checkout'
        )]
        assert len(checkout_steps) == 1

    def test_checkout_uses_v4(self, workflow_content):
        """Test that checkout uses v4."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        checkout_step = next(
            s for s in steps
            if s.get('uses', '').startswith('actions/checkout')
        )
        assert checkout_step['uses'] == 'actions/checkout@v4'

    def test_checkout_has_fetch_depth(self, workflow_content):
        """Test that checkout has fetch-depth configured."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        checkout_step = next(
            s for s in steps
            if s.get('uses', '').startswith('actions/checkout')
        )
        assert checkout_step.get('with', {}).get('fetch-depth') == 0

    def test_get_pr_files_step_exists(self, workflow_content):
        """Test that get PR files step exists."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_steps = [s for s in steps if s.get('name') == 'Get PR files']
        assert len(pr_files_steps) == 1

    def test_devin_session_step_exists(self, workflow_content):
        """Test that Devin session creation step exists."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_steps = [
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        ]
        assert len(devin_steps) >= 1

    def test_post_comment_step_exists(self, workflow_content):
        """Test that post comment step exists."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_steps = [
            s for s in steps
            if 'comment' in s.get('name', '').lower()
        ]
        assert len(comment_steps) >= 1


class TestSecretsConfiguration:
    """Tests for secrets usage in the workflow."""

    def test_github_token_used(self, workflow_raw):
        """Test that GITHUB_TOKEN secret is used."""
        assert 'secrets.GITHUB_TOKEN' in workflow_raw

    def test_devin_api_key_used(self, workflow_raw):
        """Test that DEVIN_API_KEY secret is used."""
        assert 'secrets.DEVIN_API_KEY' in workflow_raw


class TestStepOutputs:
    """Tests for step outputs configuration."""

    def test_pr_files_step_has_id(self, workflow_content):
        """Test that PR files step has an id for outputs."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        assert pr_files_step.get('id') == 'pr-files'

    def test_devin_session_step_has_id(self, workflow_content):
        """Test that Devin session step has an id for outputs."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        assert devin_step.get('id') == 'devin-session'


class TestShellScriptLogic:
    """Tests for embedded shell script logic."""

    def test_pr_files_script_uses_curl(self, workflow_content):
        """Test that PR files script uses curl to fetch files."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert 'curl' in script
        assert 'api.github.com' in script

    def test_pr_files_script_uses_jq(self, workflow_content):
        """Test that PR files script uses jq for JSON parsing."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert 'jq' in script

    def test_pr_files_script_handles_empty_response(self, workflow_content):
        """Test that PR files script handles empty response."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert 'exit 1' in script
        assert '[]' in script or 'empty' in script.lower()

    def test_pr_files_script_outputs_to_github(self, workflow_content):
        """Test that PR files script outputs to GITHUB_OUTPUT."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert 'GITHUB_OUTPUT' in script

    def test_devin_session_script_uses_curl(self, workflow_content):
        """Test that Devin session script uses curl."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert 'curl' in script
        assert 'api.devin.ai' in script

    def test_devin_session_script_handles_errors(self, workflow_content):
        """Test that Devin session script handles API errors."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert 'exit 1' in script
        assert 'Error' in script or 'error' in script

    def test_devin_session_script_outputs_session_info(self, workflow_content):
        """Test that Devin session script outputs session info."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert 'session-id' in script
        assert 'session-url' in script
        assert 'GITHUB_OUTPUT' in script

    def test_post_comment_script_uses_curl(self, workflow_content):
        """Test that post comment script uses curl."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        script = comment_step.get('run', '')
        assert 'curl' in script
        assert 'api.github.com' in script
        assert 'comments' in script


class TestPromptContent:
    """Tests for the Devin prompt content."""

    def test_prompt_includes_repository_context(self, workflow_raw):
        """Test that prompt includes repository context variable."""
        assert 'github.repository' in workflow_raw

    def test_prompt_includes_pr_number(self, workflow_raw):
        """Test that prompt includes PR number context variable."""
        assert 'github.event.pull_request.number' in workflow_raw

    def test_prompt_includes_changed_files(self, workflow_raw):
        """Test that prompt includes changed files reference."""
        assert 'steps.pr-files.outputs.files' in workflow_raw

    def test_prompt_mentions_test_implementation(self, workflow_raw):
        """Test that prompt mentions implementing tests."""
        assert 'implement' in workflow_raw.lower()
        assert 'test' in workflow_raw.lower()

    def test_prompt_mentions_devin_link_or_pr_creation(self, workflow_raw):
        """Test prompt mentions either prefilled Devin link or PR creation."""
        has_devin_link = 'prefilled Devin link' in workflow_raw
        has_create_pr = (
            'Create a new PR' in workflow_raw or
            'create a PR' in workflow_raw.lower()
        )
        assert has_devin_link or has_create_pr


class TestJqCommands:
    """Tests for jq command syntax validation."""

    def test_jq_extract_filenames_syntax(self):
        """Test that jq command for extracting filenames is valid."""
        test_json = '[{"filename": "file1.py"}, {"filename": "file2.py"}]'
        result = subprocess.run(
            ['jq', '-r', '[.[].filename] | @json'],
            input=test_json,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'file1.py' in result.stdout
        assert 'file2.py' in result.stdout

    def test_jq_extract_detail_syntax(self):
        """Test that jq command for extracting error detail is valid."""
        test_json = '{"detail": "some error"}'
        result = subprocess.run(
            ['jq', '-r', '.detail'],
            input=test_json,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'some error' in result.stdout

    def test_jq_extract_session_id_syntax(self):
        """Test that jq command for extracting session_id is valid."""
        test_json = '{"session_id": "abc123", "url": "https://example.com"}'
        result = subprocess.run(
            ['jq', '-r', '.session_id'],
            input=test_json,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'abc123' in result.stdout

    def test_jq_extract_url_syntax(self):
        """Test that jq command for extracting url is valid."""
        test_json = '{"session_id": "abc123", "url": "https://example.com"}'
        result = subprocess.run(
            ['jq', '-r', '.url'],
            input=test_json,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'https://example.com' in result.stdout

    def test_jq_create_comment_body_syntax(self):
        """Test that jq command for creating comment body is valid."""
        result = subprocess.run(
            ['jq', '-n', '--arg', 'body', 'Test comment', '{body: $body}'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert 'Test comment' in result.stdout

    def test_jq_escape_prompt_syntax(self):
        """Test that jq command for escaping prompt is valid."""
        test_prompt = 'Line 1\nLine 2\n"quoted"'
        result = subprocess.run(
            ['jq', '-Rs', '.'],
            input=test_prompt,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        # Result should be a JSON string
        assert result.stdout.startswith('"')


class TestApiEndpoints:
    """Tests for API endpoint URLs in the workflow."""

    def test_github_api_pr_files_endpoint(self, workflow_raw):
        """Test that GitHub API PR files endpoint is correct."""
        pattern = r'api\.github\.com/repos/.*pulls/.*/files'
        assert re.search(pattern, workflow_raw)

    def test_github_api_comments_endpoint(self, workflow_raw):
        """Test that GitHub API comments endpoint is correct."""
        pattern = r'api\.github\.com/repos/.*issues/.*/comments'
        assert re.search(pattern, workflow_raw)

    def test_devin_api_sessions_endpoint(self, workflow_raw):
        """Test that Devin API sessions endpoint is correct."""
        assert 'api.devin.ai/v1/sessions' in workflow_raw


class TestAuthorizationHeaders:
    """Tests for authorization header configuration."""

    def test_github_token_header_format(self, workflow_raw):
        """Test that GitHub token header uses correct format."""
        assert 'Authorization: token $GITHUB_TOKEN' in workflow_raw

    def test_devin_api_key_header_format(self, workflow_raw):
        """Test that Devin API key header uses Bearer format."""
        assert 'Authorization: Bearer $DEVIN_API_KEY' in workflow_raw

    def test_github_accept_header(self, workflow_raw):
        """Test that GitHub API requests include Accept header."""
        assert 'application/vnd.github+json' in workflow_raw
