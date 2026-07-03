# Ver.3.5 Restore Clean UI

Ver.3.4の改悪を戻して、Ver.3.3に近い綺麗な全天画像表示へ戻した版です。

## 修正
- 全天画像の表示をVer.3.3寄りに復元
- システム情報欄を下段へ下げる
- 星空感度は右側に分離
- ライブビュー周りを広めに戻す
- 文字かぶりは維持して修正

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
git pull
bash scripts/install.sh
sudo systemctl restart hoshinoyakata-allsky
```
ブラウザで Ctrl + F5。
