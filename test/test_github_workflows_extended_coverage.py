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
Additional test coverage for GitHub Actions workflow configuration.

These tests complement test_github_workflows_extended.py by adding:
- Workflow trigger and permissions configuration tests
- Checkout step and job runner configuration tests
- jq command usage pattern tests
- Comment body structure validation tests
- Edge case tests for test fixtures
"""

from __future__ import unicode_literals, absolute_import
from __future__ import print_function, division

import os

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


class TestWorkflowTriggerConfiguration:
    """Tests for workflow trigger configuration."""

    def test_workflow_triggers_on_pull_request(self, workflow_content):
        """Test that workflow triggers on pull_request event."""
        on_key = workflow_content.get('on') or workflow_content.get(True)
        assert 'pull_request' in on_key

    def test_workflow_triggers_on_opened_type(self, workflow_content):
        """Test that workflow triggers on opened PR type."""
        on_key = workflow_content.get('on') or workflow_content.get(True)
        pr_types = on_key['pull_request']['types']
        assert 'opened' in pr_types

    def test_workflow_triggers_on_synchronize_type(self, workflow_content):
        """Test that workflow triggers on synchronize PR type."""
        on_key = workflow_content.get('on') or workflow_content.get(True)
        pr_types = on_key['pull_request']['types']
        assert 'synchronize' in pr_types

    def test_workflow_triggers_on_reopened_type(self, workflow_content):
        """Test that workflow triggers on reopened PR type."""
        on_key = workflow_content.get('on') or workflow_content.get(True)
        pr_types = on_key['pull_request']['types']
        assert 'reopened' in pr_types

    def test_workflow_has_exactly_three_trigger_types(self, workflow_content):
        """Test that workflow has exactly three trigger types."""
        on_key = workflow_content.get('on') or workflow_content.get(True)
        pr_types = on_key['pull_request']['types']
        assert len(pr_types) == 3


class TestWorkflowPermissionsConfiguration:
    """Tests for workflow permissions configuration."""

    def test_workflow_has_permissions_section(self, workflow_content):
        """Test that workflow has permissions section."""
        assert 'permissions' in workflow_content

    def test_workflow_has_contents_read_permission(self, workflow_content):
        """Test that workflow has contents read permission."""
        permissions = workflow_content['permissions']
        assert permissions.get('contents') == 'read'

    def test_workflow_has_pull_requests_write_permission(
        self, workflow_content
    ):
        """Test that workflow has pull-requests write permission."""
        permissions = workflow_content['permissions']
        assert permissions.get('pull-requests') == 'write'

    def test_workflow_has_issues_read_permission(self, workflow_content):
        """Test that workflow has issues read permission."""
        permissions = workflow_content['permissions']
        assert permissions.get('issues') == 'read'

    def test_workflow_permissions_are_minimal(self, workflow_content):
        """Test that workflow uses minimal required permissions."""
        permissions = workflow_content['permissions']
        assert len(permissions) == 3


class TestJobRunnerConfiguration:
    """Tests for job runner configuration."""

    def test_job_runs_on_ubuntu_latest(self, workflow_content):
        """Test that job runs on ubuntu-latest."""
        job = workflow_content['jobs']['generate-test-plan']
        assert job['runs-on'] == 'ubuntu-latest'

    def test_job_has_steps_defined(self, workflow_content):
        """Test that job has steps defined."""
        job = workflow_content['jobs']['generate-test-plan']
        assert 'steps' in job
        assert len(job['steps']) > 0

    def test_job_name_matches_key(self, workflow_content):
        """Test that job key is generate-test-plan."""
        assert 'generate-test-plan' in workflow_content['jobs']


class TestCheckoutStepConfiguration:
    """Tests for checkout step configuration."""

    def test_checkout_uses_actions_checkout_v4(self, workflow_content):
        """Test that checkout uses actions/checkout@v4."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        checkout_step = steps[0]
        assert checkout_step['uses'] == 'actions/checkout@v4'

    def test_checkout_has_fetch_depth_zero(self, workflow_content):
        """Test that checkout has fetch-depth: 0 for full history."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        checkout_step = steps[0]
        assert checkout_step.get('with', {}).get('fetch-depth') == 0

    def test_checkout_step_has_name(self, workflow_content):
        """Test that checkout step has a name."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        checkout_step = steps[0]
        assert 'name' in checkout_step
        assert len(checkout_step['name']) > 0


class TestJqCommandUsage:
    """Tests for jq command usage patterns in workflow scripts."""

    def test_pr_files_uses_jq_for_json_processing(self, workflow_content):
        """Test that PR files step uses jq for JSON processing."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert 'jq' in script

    def test_pr_files_extracts_filenames_with_jq(self, workflow_content):
        """Test that PR files step extracts filenames using jq."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert '.filename' in script or 'filename' in script

    def test_devin_session_uses_jq_for_escaping(self, workflow_content):
        """Test that Devin session step uses jq for escaping prompt."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert 'jq -Rs' in script or 'jq' in script

    def test_devin_session_uses_jq_for_response_parsing(
        self, workflow_content
    ):
        """Test that Devin session step uses jq for response parsing."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert 'jq -r' in script

    def test_post_comment_uses_jq_for_body_construction(
        self, workflow_content
    ):
        """Test that post comment step uses jq for body construction."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        script = comment_step.get('run', '')
        assert 'jq' in script


class TestCommentBodyStructure:
    """Tests for comment body structure in post comment step."""

    def test_comment_body_mentions_devin(self, workflow_content):
        """Test that comment body mentions Devin."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        script = comment_step.get('run', '')
        assert 'Devin' in script

    def test_comment_body_has_session_url(self, workflow_content):
        """Test that comment body includes session URL."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        script = comment_step.get('run', '')
        assert 'SESSION_URL' in script or 'session-url' in script

    def test_comment_body_has_numbered_list(self, workflow_content):
        """Test that comment body has numbered list of actions."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        script = comment_step.get('run', '')
        assert '1.' in script
        assert '2.' in script
        assert '3.' in script

    def test_comment_mentions_test_coverage(self, workflow_content):
        """Test that comment mentions test coverage."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        comment_step = next(
            s for s in steps if 'comment' in s.get('name', '').lower()
        )
        script = comment_step.get('run', '')
        assert 'test' in script.lower()


class TestStepIdentifiers:
    """Tests for step identifiers (id) configuration."""

    def test_pr_files_step_has_id(self, workflow_content):
        """Test that PR files step has an id."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        assert 'id' in pr_files_step
        assert pr_files_step['id'] == 'pr-files'

    def test_devin_session_step_has_id(self, workflow_content):
        """Test that Devin session step has an id."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        assert 'id' in devin_step
        assert devin_step['id'] == 'devin-session'

    def test_step_ids_are_unique(self, workflow_content):
        """Test that all step ids are unique."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        ids = [s.get('id') for s in steps if s.get('id')]
        assert len(ids) == len(set(ids))


class TestWorkflowFileStructure:
    """Tests for overall workflow file structure."""

    def test_workflow_has_name_key(self, workflow_content):
        """Test that workflow has name key."""
        assert 'name' in workflow_content

    def test_workflow_has_on_key(self, workflow_content):
        """Test that workflow has on key."""
        assert 'on' in workflow_content or True in workflow_content

    def test_workflow_has_jobs_key(self, workflow_content):
        """Test that workflow has jobs key."""
        assert 'jobs' in workflow_content

    def test_workflow_has_single_job(self, workflow_content):
        """Test that workflow has exactly one job."""
        assert len(workflow_content['jobs']) == 1

    def test_workflow_has_four_steps(self, workflow_content):
        """Test that workflow has exactly four steps."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        assert len(steps) == 4


class TestCurlAuthorizationHeaders:
    """Tests for curl authorization header patterns."""

    def test_github_api_uses_token_auth(self, workflow_raw):
        """Test that GitHub API calls use token authorization."""
        assert 'Authorization: token' in workflow_raw

    def test_devin_api_uses_bearer_auth(self, workflow_raw):
        """Test that Devin API calls use Bearer authorization."""
        assert 'Authorization: Bearer' in workflow_raw

    def test_github_api_uses_accept_header(self, workflow_raw):
        """Test that GitHub API calls use Accept header."""
        assert 'Accept: application/vnd.github+json' in workflow_raw


class TestAnalysisPromptContent:
    """Tests for the analysis prompt content in Devin session step."""

    def test_prompt_mentions_repository_variable(self, workflow_content):
        """Test that prompt mentions repository variable."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        prompt = env.get('ANALYSIS_PROMPT', '')
        assert 'Repository' in prompt

    def test_prompt_mentions_pr_number_variable(self, workflow_content):
        """Test that prompt mentions PR number variable."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        prompt = env.get('ANALYSIS_PROMPT', '')
        assert 'PR Number' in prompt

    def test_prompt_mentions_changed_files(self, workflow_content):
        """Test that prompt mentions changed files."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        prompt = env.get('ANALYSIS_PROMPT', '')
        assert 'Changed files' in prompt or 'changed files' in prompt.lower()

    def test_prompt_has_ten_tasks(self, workflow_content):
        """Test that prompt has ten numbered tasks."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        prompt = env.get('ANALYSIS_PROMPT', '')
        assert '10.' in prompt

    def test_prompt_mentions_guidelines(self, workflow_content):
        """Test that prompt has guidelines section."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        prompt = env.get('ANALYSIS_PROMPT', '')
        assert 'Guidelines' in prompt

    def test_prompt_mentions_rules(self, workflow_content):
        """Test that prompt has rules section."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        env = devin_step.get('env', {})
        prompt = env.get('ANALYSIS_PROMPT', '')
        assert 'Rules' in prompt


class TestFixtureEdgeCases:
    """Tests for edge cases in the test fixtures."""

    def test_workflow_content_is_dict(self, workflow_content):
        """Test that workflow_content fixture returns a dict."""
        assert isinstance(workflow_content, dict)

    def test_workflow_raw_is_string(self, workflow_raw):
        """Test that workflow_raw fixture returns a string."""
        assert isinstance(workflow_raw, str)

    def test_workflow_raw_is_not_empty(self, workflow_raw):
        """Test that workflow_raw is not empty."""
        assert len(workflow_raw) > 0

    def test_workflow_content_has_expected_keys(self, workflow_content):
        """Test that workflow_content has expected top-level keys."""
        keys = set(workflow_content.keys())
        assert 'name' in keys
        assert 'permissions' in keys
        assert 'jobs' in keys
        assert 'on' in keys or True in keys

    def test_workflow_raw_starts_with_name(self, workflow_raw):
        """Test that workflow raw content starts with name key."""
        assert workflow_raw.strip().startswith('name:')


class TestScriptShellConfiguration:
    """Tests for shell script configuration in workflow steps."""

    def test_pr_files_script_uses_shell_variables(self, workflow_content):
        """Test that PR files script uses shell variables correctly."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        pr_files_step = next(
            s for s in steps if s.get('name') == 'Get PR files'
        )
        script = pr_files_step.get('run', '')
        assert '$' in script

    def test_devin_session_script_uses_shell_variables(self, workflow_content):
        """Test that Devin session script uses shell variables correctly."""
        steps = workflow_content['jobs']['generate-test-plan']['steps']
        devin_step = next(
            s for s in steps
            if 'devin' in s.get('name', '').lower()
            and 'session' in s.get('name', '').lower()
        )
        script = devin_step.get('run', '')
        assert '$' in script

    def test_scripts_use_double_quotes_for_variables(self, workflow_raw):
        """Test that scripts use double quotes for variable expansion."""
        assert '"$' in workflow_raw


class TestApiEndpointStructure:
    """Tests for API endpoint URL structure."""

    def test_github_api_endpoint_has_repos_path(self, workflow_raw):
        """Test that GitHub API endpoint has /repos/ path."""
        assert '/repos/' in workflow_raw

    def test_github_api_endpoint_has_pulls_path(self, workflow_raw):
        """Test that GitHub API endpoint has /pulls/ path."""
        assert '/pulls/' in workflow_raw

    def test_github_api_endpoint_has_files_path(self, workflow_raw):
        """Test that GitHub API endpoint has /files path."""
        assert '/files' in workflow_raw

    def test_github_api_endpoint_has_issues_path(self, workflow_raw):
        """Test that GitHub API endpoint has /issues/ path for comments."""
        assert '/issues/' in workflow_raw

    def test_github_api_endpoint_has_comments_path(self, workflow_raw):
        """Test that GitHub API endpoint has /comments path."""
        assert '/comments' in workflow_raw

    def test_devin_api_endpoint_has_sessions_path(self, workflow_raw):
        """Test that Devin API endpoint has /sessions path."""
        assert '/sessions' in workflow_raw

    def test_devin_api_endpoint_has_v1_path(self, workflow_raw):
        """Test that Devin API endpoint has /v1/ version path."""
        assert '/v1/' in workflow_raw
