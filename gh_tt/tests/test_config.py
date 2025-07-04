import os
import re
import sys

import pytest
from gh_tt.classes.config import Config


@pytest.fixture(scope="function")
def config() -> tuple[dict, list, Config]:
    """
    Loads a config

    Returns:
        tuple: (config, config files, Config class)
    """

    Config.clear_config()
    config = Config.config()
    config_files = Config.config_files()

    return (config, config_files, Config)

@pytest.fixture(scope="function")
def default_config() -> tuple[dict, list, Config]:
    """
    Loads a config with default values only

    Returns:
        tuple: (config, config files, Config class)
    """

    Config.clear_config()
    config = Config.config(load_only_default=True)
    config_files = Config.config_files()
    return (config, config_files, Config)


@pytest.mark.unittest
def test_read_app_defaults_static(default_config):
    """Test app defaults"""
    config, files, _ = default_config
    assert len(files) == 1, "Expected exactly one config file"
    assert re.search(r'../.tt-config.json', files[0]), "File name does not match expected pattern"
    
    assert config['project']['owner'] == '', "Project owner should be empty by default"
    assert config['project']['number'] == '', "Project number should be empty by default"
    assert config['workon']['status'] == 'In Progress', "Workon status should be 'In Progress'"
    
    assert config['workon']['default_type_labels']['title'] == 'ad hoc', "Default type label title should be 'ad hoc'"
    assert config['workon']['default_type_labels']['issue'] == 'development', "Default type label issue should be 'development'"
    
    assert config['squeeze']['policies']['abort_for_rebase'] is True, "Policy 'abort_for_rebase' should be True"
    assert config['squeeze']['policies']['allow-dirty'] is True, "Policy 'allow-dirty' should be True"
    assert config['squeeze']['policies']['allow-staged'] is False, "Policy 'allow-staged' should be False"
    assert config['squeeze']['policies']['quiet'] is False, "Policy 'quiet' should be False"
    assert config['squeeze']['policies']['close-keyword'] == 'resolves', "Policy 'close-keyword' should be 'resolves'"
    
    assert config['wrapup']['policies']['warn_about_rebase'] is True, "Policy 'warn_about_rebase' should be True"
    
    assert config['deliver']['status'] == 'Delivery Initiated', "Deliver status should be 'Delivery Initiated'"
    assert config['deliver']['policies']['branch_prefix'] == 'ready', "Policy 'branch_prefix' should be 'ready'"
    
    assert re.match(r'[0-9a-fA-F]{6}', config['labels']['ad hoc']['color']), "Color code for 'ad hoc' label does not match the expected hexadecimal pattern"
    assert re.match(r'.*', config['labels']['ad hoc']['description']), "Description for 'ad hoc' label should not be empty"
    assert len(config['labels']['ad hoc']['description']) <= 100, "Description for 'ad hoc' label exceeds 100 characters"
    
    assert re.match(r'[0-9a-fA-F]{6}', config['labels']['rework']['color']), "Color code for 'rework' label does not match the expected hexadecimal pattern"
    assert re.match(r'.*', config['labels']['rework']['description']), "Description for 'rework' label should not be empty"
    assert len(config['labels']['rework']['description']) <= 100, "Description for 'rework' label exceeds 100 characters"
    
    assert re.match(r'[0-9a-fA-F]{6}', config['labels']['development']['color']), "Color code for 'development' label does not match the expected hexadecimal pattern"
    assert re.match(r'.*', config['labels']['development']['description']), "Description for 'development' label should not be empty"
    assert len(config['labels']['development']['description']) <= 100, "Description for 'development' label exceeds 100 characters"

@pytest.mark.unittest
def test_read_project_static(default_config):
    """Test project specifics """
    _, _, configClass = default_config

    config = configClass.add_config('gh_tt/tests/data/.tt-config-project.json')
    files = Config.config_files()
    assert len(files) == 2
    assert re.search(r'.tt-config-project.json', files[1])
    
    assert config['project']['owner'] == 'thetechcollective'
    assert config['project']['number'] == '12'
    assert config['wrapup']['policies']['warn_about_rebase'] is False
    assert config['wrapup']['policies']['allow-dirty'] is False
    assert config['squeeze']['policies']['close-keyword'] == 'resolves'

@pytest.mark.unittest
def test_read_malformed_static_exit(capsys, default_config):
    """Test malformed config exits with error"""
    _, _, configClass = default_config
    
    with pytest.raises(SystemExit) as cm:
            configClass.add_config('gh_tt/tests/data/.tt-config-malformed.json')

    # Assertions
    assert cm.value.code == 1

    captured = capsys.readouterr()
    assert "Could not parse JSON" in captured.err

@pytest.mark.unittest
def test_read_nonexisting_static_exit(default_config):
    """Test nonexisting config exits with error"""

    _, _, configClass = default_config

    with pytest.raises(FileNotFoundError) as cm:
        configClass.add_config('gh_tt/tests/data/.tt-config-nonexisting.json')
    
    assert "No such file or directory" in str(cm.value)

