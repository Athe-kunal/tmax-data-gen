# test_final_state.py

import os
import pytest
import stat

# Truth data
admin_password = 'cloud_admin_99'
export_path = '/home/user/export_data'
migration_fstab = '/home/user/migration_fstab'
migration_status_log = '/home/user/migration_status.log'

# Expected output
expected_export_dirs = [
    '/home/user/export_data/export_dir1',
    '/home/user/export_data/export_dir2',
    '/home/user/export_data/export_dir3'
]
expected_symlinks = {
    '/home/user/cloud_mounts/export_dir1': '/home/user/export_data/export_dir1',
    '/home/user/cloud_mounts/export_dir2': '/home/user/export_data/export_dir2',
    '/home/user/cloud_mounts/export_dir3': '/home/user/export_data/export_dir3'
}

def test_export_dirs_exist():
    """Test that the export directories exist"""
    for dir in expected_export_dirs:
        assert os.path.exists(dir), f"Export directory {dir} does not exist"

def test_symlinks_exist():
    """Test that the symbolic links exist and point to the correct directories"""
    for symlink, target in expected_symlinks.items():
        assert os.path.islink(symlink), f"Symlink {symlink} does not exist"
        assert os.readlink(symlink) == target, f"Symlink {symlink} does not point to {target}"

def test_log_file_exists():
    """Test that the log file exists and contains the correct string"""
    assert os.path.exists(migration_status_log), f"Log file {migration_status_log} does not exist"
    with open(migration_status_log, 'r') as f:
        log_contents = f.read()
        assert log_contents == 'MIGRATION_COMPLETE', f"Log file {migration_status_log} does not contain 'MIGRATION_COMPLETE'"

def test_permissions():
    """Test that the export directories and symbolic links have the correct permissions"""
    for dir in expected_export_dirs:
        stat_info = os.stat(dir)
        assert stat.S_IMODE(stat_info.st_mode) == 0o755, f"Export directory {dir} has incorrect permissions"
    for symlink in expected_symlinks.keys():
        stat_info = os.stat(symlink)
        assert stat.S_IMODE(stat_info.st_mode) == 0o755, f"Symlink {symlink} has incorrect permissions"

def test_migration_fstab_contents():
    """Test that the migration_fstab file contains the correct contents"""
    with open(migration_fstab, 'r') as f:
        contents = f.readlines()
        expected_contents = [
            'export_dir1 /home/user/cloud_mounts/export_dir1\n',
            '# This is a comment\n',
            'export_dir2 /home/user/cloud_mounts/export_dir2\n',
            'export_dir3 /home/user/cloud_mounts/export_dir3\n'
        ]
        assert contents == expected_contents, f"Migration fstab file {migration_fstab} has incorrect contents"
