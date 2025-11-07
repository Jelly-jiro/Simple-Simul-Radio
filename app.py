#!/usr/bin/env python3
"""Simple Internet Radio GUI (Tkinter + python-vlc)

Rewritten to avoid PySimpleGUI compatibility issues on some systems.
Uses Tkinter for the GUI (stdlib) and python-vlc for playback.
"""
import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import requests

try:
    import vlc
except Exception as e:
    print("ERROR: python-vlc (libvlc) not available. Install VLC and python-vlc.")
    print("Exception:", e)
    sys.exit(1)


APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIONS_FILE = os.path.join(APP_DIR, "stations.json")


def load_stations(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def resolve_playlist(url, timeout=10):
    """Try to resolve a playlist (m3u/pls) to an actual stream URL.

    Returns the resolved URL or the original URL if it looks like an audio stream.
    """
    # Fast heuristics: known stream extensions -> return immediately
    try:
        if url.endswith((".mp3", ".aac", ".m3u8", ".pls", ".m3u")):
            return url

        # Try a HEAD first to obtain content-type without downloading body.
        content_type = ""
        r = None
        try:
            r = requests.head(url, timeout=timeout, allow_redirects=True)
            content_type = r.headers.get("content-type", "") or ""
        except Exception:
            # Some servers don't support HEAD properly; fall back to a streamed GET
            try:
                r = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
                content_type = r.headers.get("content-type", "") or ""
            except Exception:
                return url

        # If content-type indicates audio (stream), return original URL
        if "audio" in content_type.lower() or url.endswith((".mp3", ".aac", ".m3u8")):
            try:
                if r is not None:
                    r.close()
            except Exception:
                pass
            return url

        # Otherwise, attempt to read only a small amount of the response (playlist files)
        try:
            if r is None or not getattr(r, "iter_lines", None):
                r = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)

            # Read up to a limited number of lines to find first http(s) entry
            max_lines = 64
            lines_read = 0
            for raw in r.iter_lines(decode_unicode=True):
                if raw is None:
                    continue
                line = raw.strip()
                lines_read += 1
                if not line or line.startswith("#"):
                    pass
                elif line.startswith("http://") or line.startswith("https://"):
                    return line
                if lines_read >= max_lines:
                    break
        except Exception:
            # If anything goes wrong while inspecting, just return original URL
            return url
        finally:
            try:
                if r is not None:
                    r.close()
            except Exception:
                pass

        # If we couldn't find a redirect inside a small sample, assume original URL is the stream
        return url
    except Exception:
        return url


class RadioPlayer:
    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_url = None
        self.playing = False

    def play(self, url):
        try:
            if self.playing:
                self.stop()
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
            # small delay to allow state to change
            time.sleep(0.1)
            self.current_url = url
            self.playing = True
        except Exception:
            self.playing = False

    def stop(self):
        try:
            self.player.stop()
        finally:
            self.playing = False
            self.current_url = None

    def set_volume(self, v: int):
        try:
            self.player.audio_set_volume(int(v))
        except Exception:
            pass


class RadioApp(tk.Tk):
    def __init__(self, stations):
        super().__init__()
        self.title("Simple Radio")
        self.geometry("600x360")
        self.stations = stations
        self.player = RadioPlayer()
        self._search_results = []

        self._build_ui()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        # Search area (Radio Browser)
        search_frame = ttk.Frame(frm)
        search_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(search_frame, text="Search Radio Browser:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 6))

        # Search mode selector (Name / Tag / Country / Language / Auto)
        self.search_mode = tk.StringVar(value="Name")
        self.search_mode_cb = ttk.Combobox(search_frame, textvariable=self.search_mode, width=10, state="readonly")
        self.search_mode_cb['values'] = ("Name", "Tag", "Country", "Language", "Auto")
        self.search_mode_cb.pack(side=tk.LEFT, padx=(0,6))

        self.search_btn = ttk.Button(search_frame, text="Search", command=self.on_search)
        self.search_btn.pack(side=tk.LEFT)

        ttk.Label(frm, text="Stations").pack(anchor=tk.W)
        list_frame = ttk.Frame(frm)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, height=12)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # vertical scrollbar for stations listbox
        self.station_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.station_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.config(yscrollcommand=self.station_scroll.set)
        for s in self.stations:
            name = s.get("name", "(no name)")
            info = s.get("info", "")
            self.listbox.insert(tk.END, f"{name} - {info}")

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0))
        self.add_btn = ttk.Button(btn_frame, text="Add", width=12, command=self.on_add)
        self.add_btn.pack(pady=(0, 6))
        self.edit_btn = ttk.Button(btn_frame, text="Edit", width=12, command=self.on_edit)
        self.edit_btn.pack(pady=(0, 6))
        self.delete_btn = ttk.Button(btn_frame, text="Delete", width=12, command=self.on_delete)
        self.delete_btn.pack(pady=(0, 6))
        self.save_btn = ttk.Button(btn_frame, text="Save", width=12, command=self.on_save)
        self.save_btn.pack(pady=(6, 0))

        # Search results
        results_frame = ttk.Frame(frm)
        results_frame.pack(fill=tk.BOTH, expand=False, pady=(8, 0))
        ttk.Label(results_frame, text="Search results:").pack(anchor=tk.W)
        # results listbox with scrollbar
        self.results_listbox = tk.Listbox(results_frame, height=6)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.results_listbox.config(yscrollcommand=self.results_scroll.set)
        self.add_search_btn = ttk.Button(results_frame, text="Add selected to Stations", command=self.on_add_search)
        self.add_search_btn.pack(pady=(6, 0))

        ctrl = ttk.Frame(frm)
        ctrl.pack(fill=tk.X, pady=8)

        self.play_btn = ttk.Button(ctrl, text="Play", command=self.on_play)
        self.play_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(ctrl, text="Stop", command=self.on_stop)
        self.stop_btn.pack(side=tk.LEFT, padx=(6, 0))

        vol_lbl = ttk.Label(ctrl, text="Volume")
        vol_lbl.pack(side=tk.LEFT, padx=(12, 4))
        self.vol_scale = ttk.Scale(ctrl, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_volume)
        self.vol_scale.set(80)
        self.vol_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        status_frm = ttk.Frame(frm)
        status_frm.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(status_frm, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(status_frm, textvariable=self.status_var).pack(side=tk.LEFT)

        tip = ttk.Label(frm, text="Tip: Edit stations.json to add/remove stations.")
        tip.pack(anchor=tk.W, pady=(6, 0))

    def on_play(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Select station", "Please select a station first.")
            return
        idx = sel[0]
        url = self.stations[idx].get("url")
        if not url:
            messagebox.showinfo("No URL", "Station has no URL configured.")
            return

        self.status_var.set("Connecting...")
        t = threading.Thread(target=self._play_thread, args=(url,), daemon=True)
        t.start()

    def _play_thread(self, url):
        self.player.play(url)
        # after attempting to play, update status on main thread
        self.after(100, lambda: self.status_var.set("Playing" if self.player.playing else "Stopped"))

    def on_stop(self):
        self.player.stop()
        self.status_var.set("Stopped")

    def on_volume(self, v):
        try:
            vol = int(float(v))
            self.player.set_volume(vol)
        except Exception:
            pass

    # Station management
    def on_add(self):
        self._open_station_editor()

    def on_edit(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Edit station", "Please select a station first.")
            return
        idx = sel[0]
        self._open_station_editor(index=idx)

    def on_delete(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("Delete station", "Please select a station first.")
            return
        idx = sel[0]
        name = self.stations[idx].get("name", "(no name)")
        if messagebox.askyesno("Delete", f"Delete station '{name}'?"):
            # stop if currently playing this
            if self.player.current_url == self.stations[idx].get("url"):
                self.player.stop()
                self.status_var.set("Stopped")
            del self.stations[idx]
            self.listbox.delete(idx)
            self.save_stations()

    def on_save(self):
        self.save_stations()
        messagebox.showinfo("Saved", "stations.json saved")

    def save_stations(self):
        try:
            with open(STATIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.stations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Save error", f"Failed to save stations.json: {e}")

    def _open_station_editor(self, index: int | None = None):
        # If index is None -> add new, else edit existing
        win = tk.Toplevel(self)
        win.title("Station")
        win.geometry("480x200")
        frm = ttk.Frame(win, padding=10)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="Name").pack(anchor=tk.W)
        name_var = tk.StringVar(value=self.stations[index].get("name", "") if index is not None else "")
        name_entry = ttk.Entry(frm, textvariable=name_var)
        name_entry.pack(fill=tk.X)

        ttk.Label(frm, text="Info").pack(anchor=tk.W, pady=(8, 0))
        info_var = tk.StringVar(value=self.stations[index].get("info", "") if index is not None else "")
        info_entry = ttk.Entry(frm, textvariable=info_var)
        info_entry.pack(fill=tk.X)

        ttk.Label(frm, text="Stream URL").pack(anchor=tk.W, pady=(8, 0))
        url_var = tk.StringVar(value=self.stations[index].get("url", "") if index is not None else "")
        url_entry = ttk.Entry(frm, textvariable=url_var)
        url_entry.pack(fill=tk.X)

        btn_frm = ttk.Frame(frm)
        btn_frm.pack(fill=tk.X, pady=(12, 0))

        def on_ok():
            name = name_var.get().strip()
            info = info_var.get().strip()
            url = url_var.get().strip()
            if not name or not url:
                messagebox.showinfo("Validation", "Name and URL are required.")
                return
            entry = {"name": name, "info": info, "url": url}
            if index is None:
                self.stations.append(entry)
                self.listbox.insert(tk.END, f"{name} - {info}")
            else:
                self.stations[index] = entry
                self.listbox.delete(index)
                self.listbox.insert(index, f"{name} - {info}")
            self.save_stations()
            win.destroy()

        def on_cancel():
            win.destroy()

        ttk.Button(btn_frm, text="OK", command=on_ok).pack(side=tk.RIGHT)
        ttk.Button(btn_frm, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=(0, 6))

    # Radio Browser search
    def on_search(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showinfo("Search", "Enter search text")
            return
        mode = self.search_mode.get() if hasattr(self, 'search_mode') else "Name"
        try:
            self.search_btn.config(state=tk.DISABLED)
        except Exception:
            pass
        self.results_listbox.delete(0, tk.END)
        t = threading.Thread(target=self._search_thread, args=(query, mode), daemon=True)
        t.start()

    def _search_thread(self, query, mode="Name"):
        try:
            # build search modes list for fallback if Auto selected
            modes = []
            if mode == "Auto":
                modes = ["name", "tag", "country", "language"]
            else:
                modes = [mode.lower()]

            items = []
            for m in modes:
                params = {m: query, "limit": 50, "hidebroken": True}
                try:
                    r = requests.get("https://all.api.radio-browser.info/json/stations/search", params=params, timeout=10)
                    r.raise_for_status()
                    items = r.json()
                except Exception as e:
                    # try next fallback mode
                    print(f"[debug] search mode {m} failed: {e}")
                    items = []
                if items:
                    break
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Search error", f"Search failed: {e}"))
            items = []
        # store raw results for selection
        self._search_results = items
        self.after(0, lambda: self._display_search_results(items))
        try:
            self.after(0, lambda: self.search_btn.config(state=tk.NORMAL))
        except Exception:
            pass

    def _display_search_results(self, items):
        self.results_listbox.delete(0, tk.END)
        for it in items:
            name = it.get("name", "(no name)")
            country = it.get("country", "")
            url = it.get("url_resolved") or it.get("url") or ""
            self.results_listbox.insert(tk.END, f"{name} [{country}] - {url}")

    def on_add_search(self):
        sel = self.results_listbox.curselection()
        if not sel:
            messagebox.showinfo("Add", "Select a search result first")
            return
        idx = sel[0]
        item = self._search_results[idx]
        url = item.get("url_resolved") or item.get("url") or ""

        # Resolve playlist in a background thread to avoid blocking the GUI
        try:
            # show resolving status and disable button
            self._add_search_prev_status = self.status_var.get()
            self.status_var.set("Resolving...")
            self.add_search_btn.config(state=tk.DISABLED)
        except Exception:
            pass

        def _add_search_thread(item, url):
            # Run resolve + prepare entry in background, but ensure any exception
            # is reported and the button is re-enabled on the main thread.
            try:
                print(f"[debug] add_search: resolving url={url}")
                try:
                    # Use a shorter timeout to avoid long blocking on slow streams
                    resolved = resolve_playlist(url, timeout=5)
                    print(f"[debug] resolve_playlist returned: {resolved}")
                except Exception as e:
                    print(f"[debug] resolve_playlist failed: {e}")
                    resolved = url

                entry = {"name": item.get("name", "(no name)"), "info": item.get("tags", ""), "url": resolved}

                def _finish():
                    try:
                        print(f"[debug] _finish: adding entry name={entry.get('name')} url={entry.get('url')}")
                        self.stations.append(entry)
                        self.listbox.insert(tk.END, f"{entry['name']} - {entry['info']}")
                        self.save_stations()
                        print("[debug] _finish: save_stations done")
                        try:
                            messagebox.showinfo("Added", f"Added station: {entry['name']}")
                        except Exception as e:
                            print(f"[debug] messagebox.showinfo failed: {e}")
                    except Exception as e:
                        # Show error to user if UI update/save failed
                        print(f"[debug] _finish exception: {e}")
                        try:
                            messagebox.showerror("Add failed", f"Failed to add station: {e}")
                        except Exception:
                            print(f"[debug] messagebox.showerror failed: {e}")
                    finally:
                        try:
                            # restore previous status
                            try:
                                self.status_var.set(self._add_search_prev_status)
                            except Exception:
                                pass
                            self.add_search_btn.config(state=tk.NORMAL)
                            print("[debug] add_search_btn re-enabled")
                        except Exception as e:
                            print(f"[debug] failed to re-enable button: {e}")

                # Schedule UI updates on main thread
                self.after(0, _finish)

            except Exception as e:
                # Unexpected error in thread - schedule an error dialog and re-enable button
                print(f"[debug] unexpected error in add_search thread: {e}")

                def _error():
                    try:
                        messagebox.showerror("Error", f"An error occurred: {e}")
                    except Exception:
                        print(f"[debug] could not show error dialog: {e}")
                    try:
                        self.add_search_btn.config(state=tk.NORMAL)
                    except Exception:
                        pass

                self.after(0, _error)

        t = threading.Thread(target=_add_search_thread, args=(item, url), daemon=True)
        t.start()


def main():
    stations = load_stations(STATIONS_FILE)
    app = RadioApp(stations)
    app.mainloop()


if __name__ == "__main__":
    main()
