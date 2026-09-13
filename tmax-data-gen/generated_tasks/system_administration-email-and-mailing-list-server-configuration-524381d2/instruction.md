As an observability engineer, my main responsibility is to ensure our application's performance and health are visible to the team. To do this, I rely on our monitoring and logging infrastructure, which is configured to send metrics and logs to our email-based notification system.

My goal is to optimize our notification system to minimize unnecessary emails while still ensuring that critical issues are immediately visible to the team. To achieve this, I need to configure our mail server to only send emails when there are new or changed notifications, and I need to set up a mailing list to filter out duplicate emails.

Here are the specific requirements for this task:

1.  Configure our mail server to send emails using the `postfix` package, which I have installed using `apt-get`.
2.  Set up a mailing list using the `mailman` package, which I have installed using `apt-get`. This mailing list should be named `dev-notifications`.
3.  Configure the mail server to only send emails to the `dev-notifications` mailing list when there are new or changed notifications. I need to use the `newgrp` command to add the `dev-notifications` mailing list to the `postfix` mail group.
4.  Create a new file called `/etc/postfix/transport` that specifies the transport settings for the `dev-notifications` mailing list. This file should contain the following content:

    ```bash
dev-notifications    mailman:/var/lib/mailman/lists/dev-notifications/dev-notifications
```

    This file should also have the correct permissions set:

    ```bash
chmod 0644 /etc/postfix/transport
```

    And it should be owned by the `postfix` user:

    ```bash
chown postfix:postfix /etc/postfix/transport
```

    Finally, I need to restart the `postfix` service to apply the new configuration:

    ```bash
systemctl restart postfix
```

5.  Configure the mail server to only send emails to the `dev-notifications` mailing list when there are new or changed notifications. I need to use the `rsyslog` configuration to specify the email transport for log messages. The `rsyslog` configuration file should be modified to contain the following line:

    ```bash
mail.[mailgroup]="dev-notifications"
```

    This will configure `rsyslog` to use the `postfix` mail group to send emails.

6.  Create a test user `testuser` and add them to the `dev-notifications` mailing list using the `mailman` package. This user should receive emails when there are new or changed notifications.

The goal is to have the mail server configured to send emails to the `dev-notifications` mailing list only when there are new or changed notifications. The `dev-notifications` mailing list should be filtered to remove duplicate emails, and the `postfix` service should be restarted to apply the new configuration.

The system should be configured to send emails to the `testuser` account when there are new or changed notifications.

I will verify that this task is complete by checking the email logs to see that the `testuser` account is receiving emails only when there are new or changed notifications.
