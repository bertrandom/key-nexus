#!/bin/bash
rsync -av --exclude-from=.gitignore --exclude .git ./ web@nuke:/web/key-nexus/
scp config/prod.json web@nuke:/web/key-nexus/config/prod.json
ssh web@nuke -f "ps aux | grep gunicorn | grep "main:app" | awk '{ print \$2 }' | xargs kill -HUP"