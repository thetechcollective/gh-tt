import pytest
from pytest_mock import MockerFixture

from gh_tt.classes.sync import (
    SyncPlan,
    SyncResult,
    build_label_commands,
    build_milestone_commands,
    build_sync_plan,
    categorize_results,
    sync,
)


@pytest.mark.unittest
def test_sync_exits_when_no_sibling_repos(mocker: MockerFixture, capsys):
    """Test that sync() exits with error when no sibling repositories are configured"""
    
    mocker.patch(
        "gh_tt.classes.sync.Config.config",
        return_value={
            "sync": {
                "sibling_repos": [],  # Empty list
                "template_repo": "owner/template",
            }
        },
    )

    with pytest.raises(SystemExit) as exc_info:
        sync(labels=True)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Cannot sync without sibling repositories" in captured.err
    assert "Set the sync:sibling_repos configuration value" in captured.err


@pytest.mark.unittest
def test_sync_exits_when_no_template_repo(mocker: MockerFixture, capsys):
    """Test that sync() exits when no template repo"""
    
    mocker.patch("gh_tt.classes.sync.Config.config", return_value={
        "sync": {
            "sibling_repos": ["owner/repo1", "owner/repo2"],
            "template_repo": "",  # Empty template repo
        }
    })

    with pytest.raises(SystemExit) as exc_info:
        sync(labels=True)

    assert exc_info.value.code == 1
    assert "Cannot sync without a template repository" in capsys.readouterr().err


@pytest.mark.unittest
@pytest.mark.parametrize('override_labels', [True, False])
def test_build_label_commands_generates_correct_commands(override_labels):
    """Test that build_label_commands generates correct command structure"""
    
    labels = [
        {"name": "bug", "color": "ff0000", "description": "Bug report"},
        {"name": "feature", "color": "00ff00", "description": "Feature request"},
    ]
    sibling_repos = ["owner/repo1", "owner/repo2"]

    commands = build_label_commands(labels, sibling_repos, override_labels=override_labels)

    assert len(commands) == 4  # 2 labels x 2 repos

    # Check first command
    cmd, metadata = commands[0]
    assert "gh label create 'bug'" in cmd
    assert "'owner/repo1'" in cmd
    assert "--color 'ff0000'" in cmd
    assert "--description 'Bug report'" in cmd
    assert "--force" in cmd if override_labels else "--force" not in cmd

    assert metadata["operation_type"] == "label"
    assert metadata["target_repo"] == "owner/repo1"
    assert metadata["resource_name"] == "bug"


@pytest.mark.unittest
def test_build_milestone_commands_generates_correct_commands():
    """Test that build_milestone_commands generates correct command structure"""
    
    milestones = [
        {"title": "v1.0", "description": "First release", "state": "open"},
        {"title": "v2.0", "state": "closed", "due_on": "2025-12-31T23:59:59Z"},
    ]
    sibling_repos = ["owner/repo1"]

    commands = build_milestone_commands(milestones, sibling_repos)

    assert len(commands) == 2  # 2 milestones x 1 repo

    # Check first command
    cmd, metadata = commands[0]
    assert "gh api" in cmd
    assert "/repos/owner/repo1/milestones" in cmd
    assert "v1.0" in cmd
    assert "First release" in cmd

    assert metadata["operation_type"] == "milestone"
    assert metadata["target_repo"] == "owner/repo1"
    assert metadata["resource_name"] == "v1.0"


@pytest.mark.unittest
def test_build_milestone_commands_skips_milestones_without_title():
    """Test that milestones without titles are skipped"""
    # Arrange
    milestones = [
        {"title": "v1.0", "description": "First release"},
        {"description": "No title milestone"},  # Missing title
        {"title": "", "description": "Empty title"},  # Empty title
    ]
    sibling_repos = ["owner/repo1"]

    # Act
    commands = build_milestone_commands(milestones, sibling_repos)

    # Assert
    assert len(commands) == 1  # Only the valid milestone


@pytest.mark.unittest
def test_build_sync_plan_combines_commands_correctly():
    """Test that build_sync_plan correctly combines label and milestone commands"""
    
    labels = [{"name": "bug", "color": "ff0000", "description": "Bug"}]
    milestones = [{"title": "v1.0", "description": "Release"}]
    template_repo = "owner/template"
    sibling_repos = ["owner/repo1", "owner/repo2"]

    # Act
    plan = build_sync_plan(template_repo, sibling_repos, labels, milestones, override_labels=False)

    # Assert
    assert isinstance(plan, SyncPlan)
    assert plan.template_repo == template_repo
    assert plan.sibling_repos == sibling_repos
    assert len(plan.commands_with_metadata) == 4 # (1 label + 1 milestone) * 2 repos


@pytest.mark.unittest
def test_categorize_results_handles_different_result_types():
    """Test that categorize_results properly categorizes different result types"""
    
    results = [
        SyncResult(
            command="cmd1",
            success=True,
            operation_type="label",
            target_repo="repo1",
            resource_name="bug",
        ),
        SyncResult(
            command="cmd2",
            success=False,
            error="Error message",
            operation_type="milestone",
            target_repo="repo2",
            resource_name="v1.0",
        ),
        Exception("Unexpected error"),
        "unknown_result_type",
    ]

    # Act
    successes, failures = categorize_results(results)

    # Assert
    assert len(successes) == 1
    assert len(failures) == 3

    assert isinstance(successes[0], SyncResult)
    assert successes[0].success is True

    assert "milestone 'v1.0' to repo2: Error message" in failures[0]
    assert "Unexpected error: Unexpected error" in failures[1]
    assert "Unknown result type: unknown_result_type" in failures[2]


@pytest.mark.unittest
def test_categorize_results_handles_empty_list():
    """Test that categorize_results handles empty input"""
    successes, failures = categorize_results([])

    assert successes == []
    assert failures == []


@pytest.mark.unittest
def test_sync_result_creation_with_defaults():
    """Test SyncResult creation with default values"""
    result = SyncResult(command="test command", success=True)

    assert result.command == "test command"
    assert result.success is True
    assert result.error is None
    assert result.operation_type == ""
    assert result.target_repo == ""
    assert result.resource_name == ""


@pytest.mark.unittest
def test_sync_result_creation_with_all_fields():
    """Test SyncResult creation with all fields specified"""
    # Act
    result = SyncResult(
        command="gh label create",
        success=False,
        error="Permission denied",
        operation_type="label",
        target_repo="owner/repo",
        resource_name="bug",
    )

    # Assert
    assert result.command == "gh label create"
    assert result.success is False
    assert result.error == "Permission denied"
    assert result.operation_type == "label"
    assert result.target_repo == "owner/repo"
    assert result.resource_name == "bug"


@pytest.mark.unittest
def test_sync_plan_creation():
    """Test SyncPlan creation"""
    # Arrange
    commands = [("cmd1", {"type": "label"}), ("cmd2", {"type": "milestone"})]
    template_repo = "owner/template"
    sibling_repos = ["owner/repo1", "owner/repo2"]

    # Act
    plan = SyncPlan(commands, template_repo, sibling_repos)

    # Assert
    assert plan.commands_with_metadata == commands
    assert plan.template_repo == template_repo
    assert plan.sibling_repos == sibling_repos
