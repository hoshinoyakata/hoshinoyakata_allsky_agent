#!/usr/bin/env bash
sudo systemctl stop hoshinoyakata-capture
sudo systemctl disable hoshinoyakata-capture
echo "外部自動撮影を停止しました。Web画面はそのまま使えます。"
