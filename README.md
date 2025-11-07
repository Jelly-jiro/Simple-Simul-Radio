# Simple Internet Radio (Python)

簡易的なインターネットラジオ再生アプリです。GUI は Tkinter、再生は `python-vlc`（libVLC）を利用します。

このプロジェクトは一部 AI による支援を受けて作成されました。

このリポジトリを GitHub に公開して他の人が使えるようにするための最小セットを同梱しています（`app.py`, `requirements.txt`, `README.md`, `LICENSE`, `stations.example.json`）。

## 必要条件
- Python 3.8+
- VLC（libVLC）: システムにインストールされている必要があります（Linux の例は下参照）
- Python パッケージ: `python-vlc`, `requests`

## セットアップ（推奨手順）

1. 仮想環境を作って有効化（プロジェクトルートで）:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. pip を更新して依存をインストール:

```bash
python -m pip install --upgrade pip setuptools
python -m pip install -r requirements.txt
```

3. システムに VLC が必要（例: Debian/Ubuntu）:

```bash
sudo apt update
sudo apt install vlc
```

注: `python-vlc` は libVLC （VLC 本体）に依存します。OS のパッケージマネージャで libVLC が提供されていれば `python -m pip install python-vlc` で Python から利用できます。

## 実行

```bash
source .venv/bin/activate
python app.py
```

GUI の使い方:
- 検索欄にキーワードを入れて `Search`（検索モードを切り替えられます: Name / Tag / Country / Language / Auto）
- 結果から選択して `Add selected to Stations` で `stations.json` に追加できます
- `Play` / `Stop` / 音量スライダーで再生を操作します

## stations.json
- 個人の局リストは `stations.json` に保存されます。公開リポジトリに個人のストリームURLを載せたくない場合は `stations.example.json` を参考にして手元で `stations.json` を作成してください。

## 注意とトラブルシュート
- いくつかのストリームは地域制限や認証が必要です（Radiko など）。その場合は再生できないことがあります。
- 検索機能は Radio Browser の公開 API（コミュニティ提供）を利用しており、全ての局が登録されているわけではありません。必要な局が見つからない場合は `stations.json` に手動追加してください。

## ライセンス
このプロジェクトは `LICENSE`（MIT）で公開されています。

---
もし README をさらに整備してほしい（手順の追記やスクリーンショット、コマンドの補足など）があれば教えてください。
