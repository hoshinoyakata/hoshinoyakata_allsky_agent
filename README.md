# 星の館 全天カメラAIエージェント Ver.5.0 Practical Complete

## 修正内容
- 気圧表示を校正済みに変更
  - BME280 raw が850未満なら mmHg相当として hPa換算
  - 標高108mで海面更正
  - さらに `pressure_offset_hpa = 38.0` を加えて実用値へ補正
- LIVE開始/LIVE停止を、外部自動撮影ON/OFFに連動
- 雨センサー未接続時は「未接続」と表示
- 風向は未接続として表示
- 機能しないボタンは「準備中」と分かるよう整理
- 外部自動撮影サービス方式を維持
  - Web: `hoshinoyakata-allsky`
  - 撮影: `hoshinoyakata-capture`

## 実装済み
- 自動撮影
- ライブ表示更新
- 全画面表示
- ワンクリック撮影
- BME280温度/湿度/気圧表示
- 気圧校正
- 雲量AI
- 星空感度切替
- LIVE開始/停止

## 準備中
- 動画録画
- 流星/火球/飛行機/人工衛星/雷の検出
- HP自動更新
- Instagram投稿
- Webからの再起動/シャットダウン

## 更新方法
```bash
cd ~/hoshinoyakata_allsky_agent_real_v2
bash scripts/install.sh
```

## 確認
```bash
bash scripts/check_all.sh
bash scripts/check_pressure.sh
```

## 気圧補正の調整
`config/settings.json` の `pressure_offset_hpa` を変更します。
今は `38.0` です。近くの気象値に合わせて 35〜45 程度で微調整してください。
