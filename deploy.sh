#!/bin/bash
rsync -av --exclude-from=.gitignore --exclude .git ./ web@nuke:/web/key-nexus/
scp config/prod.json web@nuke:/web/key-nexus/config/prod.json
ssh web@nuke "sudo /usr/bin/systemctl reload key-nexus.service"