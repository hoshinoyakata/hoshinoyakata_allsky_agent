#!/usr/bin/env bash
sudo systemctl daemon-reload
sudo systemctl restart hoshinoyakata-allsky
sudo systemctl status hoshinoyakata-allsky --no-pager
