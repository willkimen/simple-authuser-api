"""
Constants module to centralize the names of Celery Beat periodic tasks.

This module contains the names used to identify periodic tasks registered in Celery Beat. 
Centralizing these names helps prevent inconsistencies and simplifies code maintenance.
"""

REMOVE_EXPIRED_TOKENS_TASK_NAME = "Remove Expired Tokens Task"
REMOVE_EXPIRED_CODE_TASK_NAME = "Remove Expired Codes Task"
