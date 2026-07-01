#!/usr/bin/env bash
(crontab -l 2>/dev/null | grep -v hoshinoyakata_agent; echo '*/5 * * * * cd /home/pi/hoshinoyakata_agent && git pull && sudo systemctl restart hoshinoyakata-allsky') | crontab -
