"""
This Django management command runs Docker Compose commands to set up 
a production environment.
The command allows options to build or recreate containers when starting 
the environment.

To execute this command, you need to be in the same directory as the manage.py file.

Options:
    --build: Rebuild the Docker containers before starting.
    --recreate: Force the recreation of containers before starting.
"""

import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand

DOCKER_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "docker"

up_command = "docker compose -f docker-compose.prod.yml up"
up_build_command = "docker compose -f docker-compose.prod.yml up --build"
up_recreate_command = "docker compose -f docker-compose.prod.yml up --force-recreate"
up_build_recreate_command = (
    "docker compose -f docker-compose.prod.yml up --build --force-recreate"
)


class Command(BaseCommand):
    help = "Run docker compose up for production"

    def add_arguments(self, parser):
        parser.add_argument("--build", action="store_true")
        parser.add_argument("--recreate", action="store_true")

    def handle(self, *args, **kwargs):
        build = kwargs.get("build")
        recreate = kwargs.get("recreate")

        if build and recreate:
            subprocess.run(up_build_recreate_command, cwd=DOCKER_DIR, shell=True)
        elif build:
            subprocess.run(up_build_command, cwd=DOCKER_DIR, shell=True)
        elif recreate:
            subprocess.run(up_recreate_command, cwd=DOCKER_DIR, shell=True)
        else:
            subprocess.run(up_command, cwd=DOCKER_DIR, shell=True)
