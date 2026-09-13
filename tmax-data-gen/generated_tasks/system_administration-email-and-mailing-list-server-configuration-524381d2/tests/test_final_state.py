# test_final_state.py

import os
import pwd
import grp
import pytest
import re

def test_final_state():
    # Test 1: Check /etc/postfix/main.cf file contents
    main_cf_file = "/etc/postfix/main.cf"
    expected_contents = "transport_maps = hash:/etc/postfix/transport"
    with open(main_cf_file, "r") as f:
        actual_contents = f.read()
    assert re.search(expected_contents, actual_contents)

    # Test 2: Check /etc/postfix/transport file contents
    transport_file = "/etc/postfix/transport"
    expected_contents = "dev-notifications    mailman:/var/lib/mailman/lists/dev-notifications/dev-notifications"
    with open(transport_file, "r") as f:
        actual_contents = f.read()
    assert re.search(expected_contents, actual_contents)

    # Test 3: Check /etc/postfix/transport file permissions
    transport_permissions = os.stat(transport_file).st_mode
    expected_permissions = 0o644
    assert transport_permissions == expected_permissions

    # Test 4: Check /etc/postfix/transport file ownership
    transport_ownership = (os.stat(transport_file).st_uid, os.stat(transport_file).st_gid)
    expected_ownership = (pwd.getpwnam("postfix").pw_uid, grp.getgrnam("postfix").gr_gid)
    assert transport_ownership == expected_ownership

    # Test 5: Check /etc/hosts file contents
    hosts_file = "/etc/hosts"
    expected_contents = "testuser   testuser@example.com"
    with open(hosts_file, "r") as f:
        actual_contents = f.read()
    assert re.search(expected_contents, actual_contents)

    # Test 6: Check /etc/hosts file permissions
    hosts_permissions = os.stat(hosts_file).st_mode
    expected_permissions = 0o644
    assert hosts_permissions == expected_permissions

    # Test 7: Check /etc/hosts file ownership
    hosts_ownership = (os.stat(hosts_file).st_uid, os.stat(hosts_file).st_gid)
    expected_ownership = (pwd.getpwnam("root").pw_uid, pwd.getpwnam("root").pw_gid)
    assert hosts_ownership == expected_ownership

    # Test 8: Check /var/log/syslog file contents
    syslog_file = "/var/log/syslog"
    expected_contents = "mail.[mailgroup]=" + "dev-notifications"
    with open(syslog_file, "r") as f:
        actual_contents = f.read()
    assert re.search(expected_contents, actual_contents)

    # Test 9: Check /var/log/syslog file permissions
    syslog_permissions = os.stat(syslog_file).st_mode
    expected_permissions = 0o644
    assert syslog_permissions == expected_permissions

    # Test 10: Check /var/log/syslog file ownership
    syslog_ownership = (os.stat(syslog_file).st_uid, os.stat(syslog_file).st_gid)
    expected_ownership = (pwd.getpwnam("root").pw_uid, grp.getgrnam("adm").gr_gid)
    assert syslog_ownership == expected_ownership

    # Test 11: Check /var/lib/mailman/lists/dev-notifications/dev-notifications file contents
    mailman_file = "/var/lib/mailman/lists/dev-notifications/dev-notifications"
    expected_contents = "testuser@example.com"
    with open(mailman_file, "r") as f:
        actual_contents = f.read()
    assert re.search(expected_contents, actual_contents)

    # Test 12: Check /var/lib/mailman/lists/dev-notifications/dev-notifications file permissions
    mailman_permissions = os.stat(mailman_file).st_mode
    expected_permissions = 0o644
    assert mailman_permissions == expected_permissions

    # Test 13: Check /var/lib/mailman/lists/dev-notifications/dev-notifications file ownership
    mailman_ownership = (os.stat(mailman_file).st_uid, os.stat(mailman_file).st_gid)
    expected_ownership = (pwd.getpwnam("postfix").pw_uid, grp.getgrnam("mailman").gr_gid)
    assert mailman_ownership == expected_ownership

    # Test 14: Check postfix service status
    postfix_status = os.system("systemctl status postfix")
    expected_status = 0
    assert postfix_status == expected_status

    # Test 15: Check rsyslog service status
    rsyslog_status = os.system("systemctl status rsyslog")
    expected_status = 0
    assert rsyslog_status == expected_status

    # Test 16: Check mailman service status
    mailman_status = os.system("systemctl status mailman")
    expected_status = 0
    assert mailman_status == expected_status

    # Test 17: Check testuser account existence
    testuser_exists = os.system("getent passwd testuser")
    expected_status = 0
    assert testuser_exists == expected_status

    # Test 18: Check testuser account membership in dev-notifications mailing list
    mailman_list = os.system("mailman list --list dev-notifications")
    expected_output = "testuser@example.com"
    actual_output = mailman_list.decode("utf-8")
    assert expected_output in actual_output

if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
