# 小型ロボット設計書

## 1. プロジェクト概要
- **ロボット名**：〇〇ロボ
- **目的**：文化祭展示用。音声認識と対話機能を活用したコミュニケーション型ロボット。
- **特徴**：
  - 音声で動作する
  - 軽量かつ省電力
  - Raspberry Pi Zero 2 W を使用

---

## 2. 機能一覧
|機能名|内容|実装方法|
|-|-|-|
|音声認識|Gravity - オフライン音声認識センサモジュールのサポートする固定ワードを認識|Gravity - オフライン音声認識センサモジュール|
|対話応答|音声認識ICの固定ワードIDを基にルールベースチャットボットを実装|ルールベースチャットボット(Python)|
|動作制御|モーター制御による移動|PWM制御（Python）|
|電源監視|LEDによる状態表示|バッテリ監視センサを用いて独自実装(Python)|
---

## 3. 使用部品・構成
|部品名|型番|用途|メーカー|備考|
|-|-|-|-|-|
|Raspberry Pi Zero 2 W|-|本体制御|RaspberryPi財団|Wi-Fi内蔵|
|Gravity - オフライン音声認識センサモジュール|-|音声認識|DFRobot|-|
|LC709203F搭載 Adafruit Li-Po/リチウムイオン バッテリーモニタ（STEMMA QT/Qwiic）|-|電源レベル監視|Adafruit|-|
|モーター|-|動作制御|-|-|
|LED|-|電源状態の表示|-|赤・緑の2色|
|リポバッテリ|-|電源供給|-|-|
---

## 4. 回路図・構造図


## 5. ソフトウェア構成
ソフトウェア構成を以下に示す．

|名前|用途|実装有無|
|-|-|-|
|MainController.py| 機体制御プログラム||
|i2c_sensor.py|i2c接続のセンサ制御プログラム||
|respones_generator.py|応答生成プログラム||
|camera_controller.py|PiCamera制御プログラム||
|face_recognition.py|顔認識プログラム||
|sonar_controller.py|超音波センサ制御プログラム||
|motor_controller.py|モータ制御プログラム|☑|
|led_controller.py|LED制御プログラム||
|logwrite.py|ログ出力プログラム|☑|
|config_loading.py|設定ファイル(.ini)読み込みプログラム|☑|