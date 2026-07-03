hoshinoyakata_allsky_agent_v0_2

起動方法:
1. フォルダへ移動
   cd hoshinoyakata_allsky_agent_v0_2

2. 必要なものを入れる
   pip install flask opencv-python numpy

3. 起動
   python app.py

4. ブラウザで開く
   http://ラズパイのIPアドレス:5000

今回の修正:
- ブラウザで横長の楕円にならないよう、表示枠を正方形に固定
- 保存画像も正方形キャンバスにして保存
- 全画面表示でも真円を維持

Pi Cameraをlibcameraで使う場合:
app.py の USE_LIBCAMERA = False を True に変更してください。
USBカメラの場合は False のままでOKです。
