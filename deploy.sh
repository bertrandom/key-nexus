#!/bin/bash
rsync -av --exclude .venv --exclude .git --exclude .mypy_cache --exclude poetry.lock ./ web@nuke:/web/key-nexus/
ssh web@nuke -f "ps aux | grep gunicorn | grep "main:app" | awk '{ print \$2 }' | xargs kill -HUP"