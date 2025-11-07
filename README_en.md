# Simple Internet Radio (Python)

This is a simple internet radio player application. The GUI uses Tkinter and playback is handled by `python-vlc` (libVLC).

This project was created with assistance from an AI.

This repository contains the minimal files needed to publish on GitHub and allow others to use the app (`app.py`, `requirements.txt`, `README.md`, `LICENSE`, `stations.example.json`).

## Requirements
- Python 3.8+
- VLC (libVLC) installed on the system
- Python packages: `python-vlc`, `requests`

## Setup (recommended)

1. Create and activate a virtual environment in the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Upgrade pip and install dependencies:

```bash
python -m pip install --upgrade pip setuptools
python -m pip install -r requirements.txt
```

3. Install system VLC if needed (Debian/Ubuntu example):

```bash
sudo apt update
sudo apt install vlc
```

Note: `python-vlc` depends on libVLC (VLC). If libVLC is available from your OS package manager, `python -m pip install python-vlc` will use it.

## Run

```bash
source .venv/bin/activate
python app.py
```

Usage:
- Enter a keyword into the search box and press `Search` (you can change search mode: Name / Tag / Country / Language / Auto)
- Select a result and press `Add selected to Stations` to save it to `stations.json`
- Use `Play` / `Stop` and the volume slider to control playback

## stations.json
- User station lists are stored in `stations.json`. If you don't want to publish your personal stream URLs, use `stations.example.json` as a template and create a local `stations.json`.

## Notes & Troubleshooting
- Some streams require regional access or authentication (e.g., Radiko) and may not play.
- The search feature uses the Radio Browser public API (community-maintained), so not all stations are guaranteed to be present. If a station is missing, add it manually to `stations.json`.

## License
This project is released under the MIT License (`LICENSE`).

---
If you'd like further improvements to the README (screenshots, more examples, or CI instructions), tell me and I will add them.
