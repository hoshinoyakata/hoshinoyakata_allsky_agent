#!/usr/bin/env bash
sudo systemctl daemon-reload
sudo systemctl restart hoshinoyakata-allsky
sudo systemctl restart hoshinoyakata-capture
sudo systemctl status hoshinoyakata-allsky --no-pager -l
sudo systemctl status hoshinoyakata-capture --no-pager -l
