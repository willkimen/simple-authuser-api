"""
Constants module to centralize strings related to Celery.
Centralizing these names helps avoid inconsistencies and simplifies code maintenance.
"""

REMOVE_EXPIRED_TOKENS_TASK_NAME = "Remove Expired Tokens Task"
REMOVE_EXPIRED_CODE_TASK_NAME = "Remove Expired Codes Task"
NOTIFY_FIRST_REMINDER_TASK_NAME = "Notify First Reminder Task"
NOTIFY_SECOND_REMINDER_TASK_NAME = "Notify Second Reminder Task"
REMOVE_EXPIRED_ACCOUNT_TASK_NAME = "Remove Expired Account"
REMOVALS_QUEUE_NAME = "removal_queue"
EMAIL_QUEUE_NAME = "email_queue"
