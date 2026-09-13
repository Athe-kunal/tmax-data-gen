# test_final_state.py

import os
import pytest
import stat

# Constants
LEGACY_EXPORT_TOOL = '/home/user/legacy_export.py'
RUN_EXPORT_SCRIPT = '/home/user/run_export.py'
SETUP_MOUNTS_SCRIPT = '/home/user/setup_mounts.py'
MIGRATION_FSTAB = '/home/user/migration_fstab'
EXPORT_DATA_DIR = '/home/user/export_data'
MIGRATION_STATUS_LOG = '/home/user/migration_status.log'
ADMIN_PASSWORD = 'cloud_admin_99'
EXPECTED_LOG_CONTENT = 'MIGRATION_COMPLETE'

def test_export_data_dir_exists():
    """Test if the export data directory exists"""
    assert os.path.exists(EXPORT_DATA_DIR), f"The directory {EXPORT_DATA_DIR} does not exist"

def test_migration_status_log_exists():
    """Test if the migration status log file exists"""
    assert os.path.exists(MIGRATION_STATUS_LOG), f"The file {MIGRATION_STATUS_LOG} does not exist"

def test_migration_status_log_content():
    """Test if the migration status log file contains the expected content"""
    with open(MIGRATION_STATUS_LOG, 'r') as f:
        log_content = f.read()
        assert log_content == EXPECTED_LOG_CONTENT, f"The log file {MIGRATION_STATUS_LOG} does not contain the expected content"

def test_symbolic_links_exist():
    """Test if the symbolic links exist at the target locations specified in the migration fstab file"""
    with open(MIGRATION_FSTAB, 'r') as f:
        for line in f:
            if not line.startswith('#'):
                source_dir, target_symlink_path = line.strip().split()
                target_symlink_path = os.path.abspath(target_symlink_path)
                assert os.path.exists(target_symlink_path), f"The symbolic link {target_symlink_path} does not exist"
                assert os.path.islink(target_symlink_path), f"The path {target_symlink_path} is not a symbolic link"
                # Check if the symbolic link points to the correct source directory
                link_target = os.readlink(target_symlink_path)
                assert link_target == os.path.join(EXPORT_DATA_DIR, source_dir), f"The symbolic link {target_symlink_path} does not point to the correct source directory"

def test_parent_directories_exist():
    """Test if the parent directories of the target symlink paths exist"""
    with open(MIGRATION_FSTAB, 'r') as f:
        for line in f:
            if not line.startswith('#'):
                source_dir, target_symlink_path = line.strip().split()
                target_symlink_path = os.path.abspath(target_symlink_path)
                parent_dir = os.path.dirname(target_symlink_path)
                assert os.path.exists(parent_dir), f"The parent directory {parent_dir} of the target symlink path {target_symlink_path} does not exist"

def test_run_export_script_executable():
    """Test if the run export script is executable"""
    assert os.access(RUN_EXPORT_SCRIPT, os.X_OK), f"The script {RUN_EXPORT_SCRIPT} is not executable"

def test_setup_mounts_script_executable():
    """Test if the setup mounts script is executable"""
    assert os.access(SETUP_MOUNTS_SCRIPT, os.X_OK), f"The script {SETUP_MOUNTS_SCRIPT} is not executable"

def test_legacy_export_tool_executable():
    """Test if the legacy export tool is executable"""
    assert os.access(LEGACY_EXPORT_TOOL, os.X_OK), f"The legacy export tool {LEGACY_EXPORT_TOOL} is not executable"

def test_migration_fstab_file_exists():
    """Test if the migration fstab file exists"""
    assert os.path.exists(MIGRATION_FSTAB), f"The file {MIGRATION_FSTAB} does not exist"

def test_export_data_dir_not_empty():
    """Test if the export data directory is not empty"""
    assert len(os.listdir(EXPORT_DATA_DIR)) > 0, f"The directory {EXPORT_DATA_DIR} is empty"
