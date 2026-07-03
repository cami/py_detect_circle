# detect_circle

ベルトコンベアを流れてくる丸い物体をカメラで検出し、物体の色（白=OK / オレンジ=NG）を判定するツール。

最終ターゲットはRaspberry Pi 4/5 + Picamera2だが、カメラ入力層以外（検出・判定・トリガー制御）は共通コードを使う想定のため、まずDebian13 + USBカメラで作り込んでいる。設計方針の詳細は [DESIGN.md](DESIGN.md) を参照。

## システム構成図

![system architecture](architecture.svg)

## セットアップ

[uv](https://docs.astral.sh/uv/) を使う。

```bash
uv add opencv-python numpy pygame   # 初回のみ
```

## 使い方

```bash
# 本番動作: 常時カメラを監視し、判定ゾーンに丸い物体が来たら1回だけ判定する
uv run python main.py

# キャリブレーション: Up/Down/Left/Rightキーで閾値を調整しながらライブプレビューで確認する
# ('h'キーでヘルプ画面（各パラメータの説明・最小値・最大値・調整中の値・main.pyが実際に使っている値を表示。Escで戻る）
#  's'キーで現在値をconfig.py貼り付け用の形式で出力、'q'/Escキーで終了)
# pygame表示なのでX11/Waylandがなくても動く(RPiの本番と同じ表示方式)
uv run python calibration.py
```

キー操作はevdev（`/dev/input/eventN`）経由で直接読み取るため、**RPi本体に物理キーボードを接続しておく必要がある**。
SSH経由で`calibration.py`を起動すること自体は問題ないが、SSHターミナルへのキー入力はevdevイベントにならず
pygameには届かないため、操作はできない。SSH接続元のPCのキーボードで操作したい場合は後述のX11フォワーディング
モードを使う。

判定結果はコンソール出力・`output/`への注釈付き画像保存・プレビューウィンドウ表示の3通りで確認できる。

### ログを止めたいとき

デフォルトでは起動時に libcamera の INFO ログ（`camera_manager` / `pipeline_base` / `IPAProxy` など）と
pygame の起動バナーがコンソールに出る。起動オプション（環境変数）で抑制できる。

```bash
LIBCAMERA_LOG_LEVELS='*:ERROR' PYGAME_HIDE_SUPPORT_PROMPT=1 uv run python main.py
```

- `LIBCAMERA_LOG_LEVELS='*:ERROR'`: libcamera の INFO ログを抑制し、ERROR のみ表示する（`*:WARN` にすると WARN 以上を表示）
- `PYGAME_HIDE_SUPPORT_PROMPT=1`: pygame の `Hello from the pygame community` バナーを抑制する

判定結果の `print()`（`judgment=...` の行）はアプリ自体のログなので、これらのオプションでは消えない。

### SSH接続元のPCの画面に表示したいとき

本番はpygame(SDL)がX11/Wayland無しでDRMに直接描画する設計（[DESIGN.md](DESIGN.md)参照）だが、
開発中にSSH接続元のPC側で画面を見たい場合はX11フォワーディングで飛ばせる。

```bash
# PC側（クライアント）: -X（または -Y）を付けてSSH接続
ssh -X pi@<RaspberryPiのIP>

# Pi側: SDLにEGL経由のX11描画を強制しないと動かない
SDL_VIDEO_X11_FORCE_EGL=1 python main.py
```

- `SDL_VIDEO_X11_FORCE_EGL=1` を付けないと、X11フォワーディング越しでは描画に失敗する。
- 上記は `uv run` を使わず、システムの `python` で動かした場合に動作確認済み。

### SSH接続時でもSPI実機ディスプレイに表示したいとき

SSH -X/-Y接続時はDISPLAYが設定されているため、デフォルトではSSH接続元のPC側に表示される
（[DESIGN.md](DESIGN.md)参照）。X11フォワーディングは維持したまま、SPI実機ディスプレイ側で
見た目を確認したい場合は`FORCE_SPI_DISPLAY=1`を付ける。

```bash
FORCE_SPI_DISPLAY=1 python calibration.py
```

## ディレクトリ構成

| パス | 役割 |
|---|---|
| `config.py` | 解像度・閾値・判定ゾーンなど調整可能な設定値 |
| `camera/base.py` | `CameraSource` 抽象基底クラス |
| `camera/factory.py` | `open_camera_source()`。CSI（Picamera2）を優先し、無ければUSBにフォールバック |
| `camera/csi_camera.py` | CSIカメラ実装（Picamera2ベース、RPi本番向け） |
| `camera/usb_camera.py` | USBカメラ実装（`cv2.VideoCapture`ベース） |
| `detection/circle_detector.py` | 円検出（輪郭の真円度ベース） |
| `detection/color_classifier.py` | 円内領域のHSV平均色からOK/NG/Errorを判定 |
| `trigger.py` | 判定ゾーン進入とクールダウンを管理するステートマシン |
| `display.py` | pygameによる画面表示（`PygameDisplay`）。main.py/calibration.py共通、X11/Wayland不要 |
| `annotation.py` | 円・判定ラベルの描画（`draw_judgment`）。main.py/calibration.py共通 |
| `main.py` | 本番用の常時監視ループ |
| `calibration.py` | 閾値調整用のインタラクティブツール（pygame表示・キーボード操作） |
| `output/` | 判定イベント発生時の注釈付き画像の保存先（実行時に自動作成） |
