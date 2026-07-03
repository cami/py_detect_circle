# 設計方針

このプロジェクトのモジュール分割・クラス化の判断基準をまとめる。

## 1. 「状態を持たない処理」と「状態を持つ処理」を分離する

- [detection/circle_detector.py](detection/circle_detector.py) の `find_circle(frame) -> Circle | None` と
  [detection/color_classifier.py](detection/color_classifier.py) の `classify(frame, circle) -> ClassificationResult` は、
  入力から出力を計算するだけの純粋関数。フレームをまたいだ状態を持たないため、クラス化せず関数のままにしている。
- [trigger.py](trigger.py) の `TriggerStateMachine` は「何フレーム連続で円が判定ゾーンに見えているか」
  「クールダウン中かどうか」というフレームをまたぐ状態を持つ必要があるため、ここだけクラスにしている。
  状態を持つロジックを1箇所に閉じ込めることで、「いつ判定を実行すべきか」のタイミング制御だけを独立して
  変更・検証できるようにしている。

## 2. 抽象化（クラス階層）は「実際に複数実装が要る」場所にだけ導入する

- [camera/base.py](camera/base.py) の `CameraSource` 抽象基底クラスは、USBカメラ用の `UsbCameraSource` と、
  RPi移植時に必要になる Picamera2 用実装の両方が確実に存在することがわかっているため、インターフェースを切っている。
- 円検出・色判定は今のところ代替アルゴリズム（Hough変換など）を実装する予定がないため、
  `CircleDetector` のようなクラス階層にはせず関数のままにしている。使う予定のない差し替え可能性のために
  クラス化するのは過剰設計であり、将来別アルゴリズムを試したくなった時点で関数を追加・差し替えれば十分という判断。

## 3. データの受け渡しは辞書ではなく型付きの値オブジェクトにする

- `Circle`（`NamedTuple`: cx, cy, r）、`Judgment`（`Enum`: OK/NG/Error）、`ClassificationResult`（`NamedTuple`）を
  使うことで、円検出・判定の戻り値の形がコードを見ればすぐわかり、辞書のキー名のタイプミスのような不具合も
  型チェックで防げる。

## 4. `main.py` はロジックを持たない「配線役」に徹する

- [main.py](main.py) はカメラループを回し、`find_circle` → `TriggerStateMachine.step` → `classify` → 出力、
  という呼び出し順序を組み立てるだけで、検出・判定のアルゴリズム自体はここには書かない。
- これにより、例えば「常時ループ」から「外部トリガーで1枚だけ処理する」ように動作モードを変えたくなっても、
  `main.py` だけ書き換えれば済み、検出・判定ロジックには触れずに済む。

## 5. 設定値は `config.py` に集約し、ロジックコードにマジックナンバーを書かない

- 解像度、真円度・面積の閾値、HSVの色判定閾値、判定ゾーンの範囲、トリガー確定フレーム数などを
  各モジュールに埋め込まず [config.py](config.py) にまとめている。実機での再調整（照明条件・ベルト速度の変化）を
  ロジックコードを読み解かずに行えるようにするため。

## 6. 画面表示はpygameに統一し、`display.py`に共有する

- RPi4/5の実機本番はX11/Waylandを使わず、`pygame`でSPI/DRM経由の画面に直接描画する。`cv2.imshow`/
  `cv2.createTrackbar`（OpenCVのHighGUI）はウィンドウシステムが無いと動作しないため、本番・調整ツールとも
  `pygame`一択になる。
- この表示ロジックは[display.py](display.py)の`PygameDisplay`クラス（`show(frame)` / `poll_events()`）に集約し、
  [main.py](main.py)（本番プレビュー）と[calibration.py](calibration.py)（調整用プレビュー）の両方がこれ経由で
  描画する。calibration.pyを先にpygame方式で作った際、`main.py`側は`cv2.imshow`のまま取り残されていて
  実機では動かない状態になっていた（コードレビューで発覚し修正済み）。表示ロジックを1箇所にまとめたことで、
  今後どちらか一方だけ直しそびれるということが起きないようにしている。
- `main.py`は起動直後に空フレームを一度表示してウィンドウを作成しておく。判定イベント発生時だけ画面を
  更新する設計（RPiのSPI表示が遅いため）とは別に、終了キー(`q`/Esc)は最初の判定を待たずに効くようにするため。
- calibration.py側のUIはトラックバーのような専用ウィジェットを使わず、パラメータ名と現在値をフレームに
  文字として焼き込み、矢印キーで選択・増減するだけの最小限の作りにしている（RPi上で凝ったGUIを構築する
  必要はないため）。
- RPi実機にはHDMIなど他のDRM出力が存在しうるため、`display.py`の`_select_spi_display_driver()`が
  `/sys/class/drm/card*-SPI-*`からSPI接続のDRMカードを探し、`SDL_VIDEODRIVER=kmsdrm`と対応する
  `SDL_VIDEO_KMSDRM_DEVICE_INDEX`を設定してからpygameを初期化する。SDL_VIDEODRIVERが既に設定済み、
  またはローカルX11/Wayland（SSH -X/-Y転送含む）が検出された場合は何もせず、明示的な設定やSSH越しの
  開発用表示を上書きしない。`PygameDisplay.__init__`内で呼ぶことで、main.py/calibration.py双方に
  自動的に適用される。
  当初`DISPLAY`の判定を`.startswith(":")`（ローカルXの`:0`形式のみ）にしていたため、SSH -X/-Y転送時の
  `host:10.0`形式を検出できず、`SDL_VIDEO_X11_FORCE_EGL=1`を指定してもkmsdrmに上書きされてしまう
  不具合があった（実機での動作確認で発覚）。`DISPLAY`が空でなければ真とする判定に修正済み。
  逆にSSH -X/-Y接続を維持したままSPI実機側の見た目を確認したい場合のために、`FORCE_SPI_DISPLAY`環境変数
  でDISPLAY/WAYLAND_DISPLAYの判定を無視してSPI側を強制選択できるようにしている（`SDL_VIDEODRIVER`を
  直接指定した場合はそちらが最優先されるのは変わらない）。
- SPIパネルのDRMコネクタは`480x320`（`config.DISPLAY_WIDTH`/`DISPLAY_HEIGHT`）という1モードしか公開して
  いない。以前は呼び出し側（main.py）が表示直前に`cv2.resize`でこのサイズに合わせていたが、
  calibration.pyはカメラの生解像度（`CAPTURE_WIDTH`/`CAPTURE_HEIGHT`=640x480）のまま`display.show()`に
  渡していたため、パネルが対応しないサイズで`pygame.display.set_mode()`が呼ばれ、コンソール
  （ログインプロンプト）の内容と表示が競合してちらつく不具合が発生していた（実機での動作確認で発覚）。
  呼び出し側がリサイズを忘れると再発するため、`PygameDisplay.show()`内でこの解像度に強制リサイズする
  ようにし、main.py側の重複したリサイズ処理は削除した。

## 7. 描画ロジックも`annotation.py`に共有する

- 円・判定ラベルの描画（`draw_judgment`）は[annotation.py](annotation.py)にまとめ、`main.py`と`calibration.py`の
  両方から呼ぶ。以前は両ファイルに`_LABEL_COLORS`と描画コードがそれぞれ複製されており、片方だけ色やスタイルを
  変更すると気づかないうちにズレる状態だった（コードレビューで発覚し修正済み）。calibration.pyは本番の描画結果を
  確認するためのツールなので、描画ロジックが本番(main.py)と常に一致していることが重要という判断。

## まとめ

**変化する可能性が高い軸（カメラハードウェア、閾値）は抽象化・外出しし、変化する予定のない軸
（検出アルゴリズム自体）は素直に関数のままにする**、という基準でモジュールを分割している。

システム全体の構成図は [architecture.svg](architecture.svg)（[README.md](README.md) にも掲載）を参照。
