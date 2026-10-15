"""Run only the task safety suite, with socket access blocked before Django loads."""
import os
import socket
import sys


def blocked(*args, **kwargs):
    raise RuntimeError("Network access is forbidden in offline task tests")


def main():
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test_tasks"
    os.environ["CELERY_BROKER_URL"] = "memory://"
    os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"
    socket.socket.connect = blocked
    socket.socket.connect_ex = blocked
    socket.create_connection = blocked
    from django.core.management import execute_from_command_line
    execute_from_command_line(["offline-tests", *sys.argv[1:]])


if __name__ == "__main__":
    main()
