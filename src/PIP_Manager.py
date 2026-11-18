#!/usr/bin/env python3
"""PIP Manager App 5.1 - rewritten for modern Python (3.9+ incl. 3.13/3.14/3.15-dev).

Changes vs 5.0:
* pkg_resources (removed from modern setuptools) -> importlib.metadata
* pywin32 no longer required (ctypes is used to hide the console on Windows)
* pip is run as `sys.executable -m pip` with an argument list (no shell, no injection),
  output is streamed live into the console panel
* All work happens in worker threads; the UI is only touched from the Tk thread (queue)
* Recursive cli() replaced by a loop, bad `upgradepip` command fixed
* Config file is validated, merged with defaults and written atomically
* Faster autocomplete (bisect + on-disk PyPI cache), Treeview package list with sorting
"""
from __future__ import annotations

import ast
import json
import os
import platform
import queue
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from bisect import bisect_left
from importlib import metadata
from importlib.util import find_spec
from pathlib import Path

VERSION = "5.1"
BASE = Path(__file__).resolve().parent
SRC = BASE / "src"
COGS = SRC / "cogs.json"
PYPI_CACHE = SRC / "pypi_names.json"
RELEASE_URL = "https://blaze005.github.io/items.json"
UPDATE_URL = "https://raw.githubusercontent.com/blaze005/PIP-Manager-App/main/src/PIP_Manager.py"
DEFAULTS = {"darkmode": "on", "cmd": "off", "cli": "off", "install_auto": "yes", "pypi": "off"}
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
IS_WIN = os.name == "nt"


# --------------------------------------------------------------------------- config
def load_cogs() -> dict:
    cfg = dict(DEFAULTS)
    try:
        with open(COGS, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for k, default in DEFAULTS.items():
                if isinstance(data.get(k), str):
                    cfg[k] = data[k]
    except FileNotFoundError:
        print("Building cogs.json....")
    except (OSError, ValueError) as e:
        print(f"ERROR: {e} - rebuilding cogs.json")
    save_cogs(cfg)
    return cfg


def save_cogs(cfg: dict) -> None:
    try:
        SRC.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=SRC, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, COGS)  # atomic: never leaves a half-written file
    except OSError as e:
        print(f"Could not save settings: {e}")


# --------------------------------------------------------------------------- helpers
PKG_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-\[\],<>=!~;:'\"*+@/\\ ]*$")


def parse_packages(text: str) -> list[str]:
    """Split user input into pip arguments; refuse empty input and option injection."""
    try:
        tokens = shlex.split(text)
    except ValueError as e:
        raise ValueError(f"Cannot parse input: {e}") from None
    if not tokens:
        raise ValueError("Please enter a package name.")
    for t in tokens:
        if t.startswith("-") or not PKG_TOKEN.match(t):
            raise ValueError(f"Invalid package name: {t!r}")
    return tokens


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def vtuple(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4])


def run_pip(args: list[str], emit, timeout: float | None = None) -> int:
    """Run pip, streaming each output line to emit(). Returns the exit code (-1 on failure to start)."""
    cmd = [sys.executable, "-m", "pip", *args]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", creationflags=NO_WINDOW)
    except (OSError, ValueError) as e:
        emit(f"[!] Could not start pip: {e}")
        return -1
    timer = threading.Timer(timeout, proc.kill) if timeout else None
    if timer:
        timer.start()
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            emit(line.rstrip())
        return proc.wait()
    except Exception as e:  # noqa: BLE001 - never let a worker thread die silently
        emit(f"[!] pip error: {e}")
        proc.kill()
        return -1
    finally:
        if timer:
            timer.cancel()


def installed_packages() -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for d in metadata.distributions():
            try:
                name = d.metadata["Name"]
                if name:
                    out.setdefault(name, d.version or "?")
            except Exception:  # noqa: BLE001 - one broken dist-info must not break the list
                continue
    except Exception as e:  # noqa: BLE001
        print(f"Could not read installed packages: {e}")
    return dict(sorted(out.items(), key=lambda kv: kv[0].lower()))


def outdated_packages() -> dict[str, str]:
    """name(normalised) -> latest version."""
    try:
        r = subprocess.run([sys.executable, "-m", "pip", "list", "-o", "--format=json",
                            "--disable-pip-version-check"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180, creationflags=NO_WINDOW)
        return {norm(p["name"]): p["latest_version"] for p in json.loads(r.stdout or "[]")}
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as e:
        print(f"Could not check outdated packages: {e}")
        return {}


def fetch_release() -> str:
    try:
        with urllib.request.urlopen(RELEASE_URL, timeout=8) as r:
            return str(json.loads(r.read().decode("utf-8"))["PM-release"])
    except Exception as e:  # noqa: BLE001 - network, JSON, key errors all mean "offline"
        print(f"No connection to {RELEASE_URL}: {e}")
        return "ERROR [NoI]"


def load_pypi_names(emit=print) -> list[str]:
    """PyPI project names (cached for 7 days on disk -> fast start)."""
    try:
        if PYPI_CACHE.exists() and time.time() - PYPI_CACHE.stat().st_mtime < 7 * 86400:
            with open(PYPI_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    try:
        emit("Fetching package names from PyPI.....")
        req = urllib.request.Request("https://pypi.org/simple/",
                                     headers={"Accept": "application/vnd.pypi.simple.v1+json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            names = sorted((p["name"] for p in json.loads(r.read())["projects"]), key=str.lower)
        try:
            SRC.mkdir(parents=True, exist_ok=True)
            with open(PYPI_CACHE, "w", encoding="utf-8") as f:
                json.dump(names, f)
        except OSError:
            pass
        return names
    except Exception as e:  # noqa: BLE001
        emit(f"PyPI fetch failed: {e}")
        return []


# --------------------------------------------------------------------------- CLI
def cli() -> None:
    if IS_WIN:
        os.system("")  # enables ANSI colours in cmd.exe
    G, C, R, Y, W = "\033[32m", "\033[36m", "\033[31m", "\033[33m", "\033[37m"
    helptext = (f"{Y}\n  Commands:\n  install [package]   -> installs package(s)\n"
                "  uninstall [package] -> uninstalls package(s)\n  upgrade [package]   -> upgrades package(s)\n"
                "  list / outdated     -> list installed / outdated packages\n  clear               -> clear screen\n"
                "  cli off             -> turn CLI mode off (start GUI next time)\n  exit                -> quit\n")
    while True:
        try:
            line = input(f"\n {G}┌──({C}PIP-Manager{G})\n └─${W} ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        try:
            parts = shlex.split(line)
        except ValueError as e:
            print(f"{R}{e}")
            continue
        if not parts:
            continue
        cmd, rest = parts[0].lower(), parts[1:]
        if cmd in ("install", "uninstall", "upgrade"):
            try:
                pk = parse_packages(" ".join(shlex.quote(p) for p in rest))
            except ValueError:
                print(f"{R}cmd {cmd} needs package {G}>> {Y}{cmd} [package]")
                continue
            args = {"install": ["install"], "uninstall": ["uninstall", "-y"],
                    "upgrade": ["install", "--upgrade"]}[cmd] + pk
            print("===" * 20)
            run_pip(args, print)
            print("===" * 20)
        elif cmd == "list":
            run_pip(["list"], print)
        elif cmd == "outdated":
            run_pip(["list", "-o"], print)
        elif cmd == "clear":
            os.system("cls" if IS_WIN else "clear")
        elif cmd == "help":
            print(helptext)
        elif cmd == "exit":
            return
        elif cmd == "cli" and rest[:1] == ["off"]:
            cfg = load_cogs()
            cfg["cli"] = "off"
            save_cogs(cfg)
            print(f"{G} CLI Mode is now off")
        else:
            print(f"{R}cmd error: {Y}'{cmd}'{R} not found")


# --------------------------------------------------------------------------- GUI
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    HAS_TK = True
except Exception:  # noqa: BLE001 - tkinter missing / no display
    HAS_TK = False

try:
    from ttkthemes import ThemedTk
except Exception:  # noqa: BLE001
    ThemedTk = None


def console_window():
    """Handle of the console window we were started from (Windows only, via ctypes - no pywin32)."""
    if not IS_WIN:
        return 0
    try:
        import ctypes
        return ctypes.windll.kernel32.GetConsoleWindow()
    except Exception:  # noqa: BLE001
        return 0


def show_console(show: bool) -> None:
    hwnd = console_window()
    if hwnd:
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(hwnd, 5 if show else 0)
        except Exception:  # noqa: BLE001
            pass


class App:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.root = ThemedTk(theme="breeze") if ThemedTk else tk.Tk()
        self.root.geometry("640x560")
        self.root.minsize(560, 480)
        self.q: queue.Queue = queue.Queue()
        self.busy = threading.Lock()
        self.pkgs: dict[str, str] = {}
        self.outdated: dict[str, str] = {}
        self.pypi: list[str] = []
        self.pypi_lower: list[str] = []
        self.buttons: list = []
        self.sort_rev = False
        self.release = "…"
        self.search_job = None

        self.dark = tk.IntVar(value=int(cfg["darkmode"] == "on"))
        self.hide_cmd = tk.IntVar(value=int(cfg["cmd"] == "off"))
        self.cli_var = tk.IntVar(value=int(cfg["cli"] == "on"))
        self.pypi_var = tk.IntVar(value=int(cfg["pypi"] == "on"))

        self.build_ui()
        self.apply_theme()
        self.set_title()
        show_console(self.hide_cmd.get() == 0)
        self.root.after(50, self.pump)
        self.refresh_packages()
        self.bg(self.check_release)
        if cfg["pypi"] == "on":
            self.bg(self.load_pypi)

    # ---- threading helpers
    def bg(self, fn, *a) -> None:
        def wrap():
            try:
                fn(*a)
            except Exception as e:  # noqa: BLE001
                self.log(f"[!] Unexpected error: {e}")
        threading.Thread(target=wrap, daemon=True).start()

    def ui(self, fn, *a) -> None:
        self.q.put((fn, a))

    def pump(self) -> None:
        try:
            for _ in range(200):  # bounded batch keeps the UI responsive
                fn, a = self.q.get_nowait()
                try:
                    fn(*a)
                except tk.TclError:
                    pass
        except queue.Empty:
            pass
        try:
            self.root.after(50, self.pump)
        except tk.TclError:
            pass

    def log(self, text: str) -> None:
        self.ui(self._log, text)

    def _log(self, text: str) -> None:
        self.console.config(state="normal")
        self.console.insert("end", text + "\n")
        if int(self.console.index("end-1c").split(".")[0]) > 2000:
            self.console.delete("1.0", "500.0")
        self.console.see("end")
        self.console.config(state="disabled")

    # ---- UI
    def build_ui(self) -> None:
        r = self.root
        menubar = tk.Menu(r)
        m = tk.Menu(menubar, tearoff=False)
        m.add_command(label="Auto-Py-To-EXE", accelerator="F1", command=self.auto_py_to_exe)
        m.add_command(label="Refresh Package List", accelerator="Ctrl+Shift+U", command=self.refresh_packages)
        m.add_command(label="App Info", command=self.app_info)
        m.add_separator()
        m.add_command(label="Clear Console", accelerator="Ctrl+X", command=self.clear_console)
        m.add_command(label="Exit", accelerator="Ctrl+Q", command=r.destroy)
        menubar.add_cascade(label="Quick Access", menu=m)
        r.config(menu=menubar)

        self.tabs = ttk.Notebook(r)
        t1, t2, t3 = ttk.Frame(self.tabs, padding=12), ttk.Frame(self.tabs, padding=8), ttk.Frame(self.tabs, padding=16)
        for t, n in ((t1, "Manager"), (t2, "Package List"), (t3, "Settings")):
            self.tabs.add(t, text=n)
        self.tabs.pack(fill="both", expand=True, padx=6, pady=(6, 0))

        # Manager tab
        ttk.Label(t1, text="PIP Manager App", font=("Segoe UI", 18, "bold")).pack(pady=(4, 2))
        ttk.Label(t1, text="Package name(s), e.g.  requests  or  numpy pandas==2.2").pack()
        self.entry = ttk.Combobox(t1, width=40)
        self.entry.pack(pady=10, ipady=3)
        self.entry.bind("<KeyRelease>", self.filter_names)
        self.entry.bind("<Return>", lambda e: self.do_install())
        bar = ttk.Frame(t1)
        bar.pack()
        for i, (txt, fn) in enumerate((("Install", self.do_install), ("Uninstall", self.do_uninstall),
                                       ("Upgrade", self.do_upgrade), ("Check Import", self.do_import))):
            b = ttk.Button(bar, text=txt, command=fn, width=12)
            b.grid(row=0, column=i, padx=4)
            self.buttons.append(b)
        b = ttk.Button(t1, text="Upgrade PIP", command=self.do_upgrade_pip)
        b.pack(pady=10)
        self.buttons.append(b)
        self.progress = ttk.Progressbar(t1, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 4))

        # Package list tab
        top = ttk.Frame(t2)
        top.pack(fill="x")
        ttk.Label(top, text="Search:").pack(side="left")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *_: self.debounce_filter())
        ttk.Entry(top, textvariable=self.search).pack(side="left", fill="x", expand=True, padx=6)
        self.count = ttk.Label(top, text="")
        self.count.pack(side="right")
        cols = ("name", "version", "latest")
        self.tree = ttk.Treeview(t2, columns=cols, show="headings", selectmode="extended", height=10)
        for c, w in zip(cols, (260, 120, 120)):
            self.tree.heading(c, text=c.title(), command=lambda c=c: self.sort_by(c))
            self.tree.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(t2, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=6)
        self.tree.pack(fill="both", expand=True, pady=6)
        self.menu = tk.Menu(self.tree, tearoff=0)
        self.menu.add_command(label="Upgrade", command=self.sel_upgrade)
        self.menu.add_command(label="Uninstall", command=self.sel_uninstall)
        self.menu.add_separator()
        self.menu.add_command(label="Package Info", command=self.sel_info)
        self.tree.bind("<Button-3>", self.popup)
        self.tree.bind("<Button-2>", self.popup)  # macOS
        self.tree.bind("<Double-1>", lambda e: self.sel_info())

        # Settings tab
        for i, (txt, var, cmd) in enumerate((("Dark mode", self.dark, self.toggle_dark),
                                             ("Hide console window (Windows)", self.hide_cmd, self.toggle_cmd),
                                             ("Start in CLI mode", self.cli_var, self.toggle_cli),
                                             ("PyPI autocomplete (uses more RAM)", self.pypi_var, self.toggle_pypi))):
            ttk.Checkbutton(t3, text=txt, variable=var, command=cmd).grid(row=i, column=0, sticky="w", pady=4)
        ttk.Button(t3, text="Auto Py to EXE", command=self.auto_py_to_exe).grid(row=5, column=0, sticky="w", pady=(14, 4))
        ttk.Button(t3, text="App Info", command=self.app_info).grid(row=6, column=0, sticky="w", pady=4)

        # Console
        fr = ttk.LabelFrame(r, text="Console")
        fr.pack(fill="both", padx=8, pady=8)
        self.console = tk.Text(fr, height=9, bg="black", fg="#33ff66", insertbackground="#33ff66",
                               state="disabled", wrap="word", font=("Consolas", 9))
        cs = ttk.Scrollbar(fr, command=self.console.yview)
        self.console.configure(yscrollcommand=cs.set)
        cs.pack(side="right", fill="y")
        self.console.pack(fill="both", expand=True)

        r.bind("<Control-q>", lambda e: r.destroy())
        r.bind("<Control-x>", lambda e: self.clear_console())
        r.bind("<Control-U>", lambda e: self.refresh_packages())
        r.bind("<F1>", lambda e: self.auto_py_to_exe())
        r.after(0, self.entry.focus_set)

    def set_title(self) -> None:
        t = f"PIP Manager App {VERSION}"
        if self.release == "ERROR [NoI]":
            t += " (offline)"
        elif self.release not in ("…", VERSION) and vtuple(self.release) > vtuple(VERSION):
            t += f" (Update available: {self.release})"
        self.root.title(t)

    def apply_theme(self) -> None:
        dark = self.dark.get() == 1
        try:
            if ThemedTk:
                self.root.set_theme("equilux" if dark else "breeze")
            else:
                ttk.Style().theme_use("clam")
        except tk.TclError:
            pass
        bg, fg, sel = ("#1e1e1e", "#33ff66", "#7b3fbf") if dark else ("#ffffff", "#111111", "#19849E")
        st = ttk.Style()
        st.configure("Treeview", background=bg, fieldbackground=bg, foreground=fg, rowheight=22)
        st.map("Treeview", background=[("selected", sel)], foreground=[("selected", "#ffffff")])
        self.tree.tag_configure("old", foreground="#ff6b6b" if dark else "#c00000")
        self.menu.config(background=bg, foreground=fg, activebackground=sel)

    # ---- busy / tasks
    def set_busy(self, on: bool) -> None:
        for b in self.buttons:
            b.config(state="disabled" if on else "normal")
        (self.progress.start if on else self.progress.stop)(*([12] if on else []))

    def task(self, label: str, batches: list[list[str]], refresh: bool = True) -> None:
        if not self.busy.acquire(blocking=False):
            messagebox.showinfo("Busy", "Another operation is still running.")
            return
        self.ui(self.set_busy, True)

        def work():
            try:
                self.log(f"[/] {label}")
                ok = True
                for args in batches:
                    ok &= run_pip(args + ["--disable-pip-version-check"], self.log) == 0
                self.log(f"[+] Done: {label}" if ok else f"[!] Finished with errors: {label}")
            finally:
                self.busy.release()
                self.ui(self.set_busy, False)
                if refresh:
                    self.ui(self.refresh_packages)
        self.bg(work)

    def pkg_input(self) -> list[str] | None:
        try:
            return parse_packages(self.entry.get())
        except ValueError as e:
            messagebox.showwarning("Input", str(e))
            return None

    def do_install(self):
        if (p := self.pkg_input()):
            self.task(f"Installing: {' '.join(p)}", [["install", *p]])

    def do_upgrade(self):
        if (p := self.pkg_input()):
            self.task(f"Upgrading: {' '.join(p)}", [["install", "--upgrade", *p]])

    def do_uninstall(self):
        if (p := self.pkg_input()) and messagebox.askyesno("Uninstall", f"Uninstall {', '.join(p)}?"):
            self.task(f"Uninstalling: {' '.join(p)}", [["uninstall", "-y", *p]])

    def do_upgrade_pip(self):
        self.task("Upgrading PIP", [["install", "--upgrade", "pip"]])

    def do_import(self):
        p = self.entry.get().strip()
        try:
            found = bool(p) and find_spec(p) is not None
        except (ImportError, ValueError, AttributeError) as e:
            self.log(f"[-] Cannot check '{p}': {e}")
            return
        self.log(f"Module Found: {p}" if found else f"[-] Module Not Found: {p}")

    # ---- package list
    def refresh_packages(self) -> None:
        def work():
            pk = installed_packages()
            self.ui(self.set_pkgs, pk, self.outdated)
            old = outdated_packages()
            self.ui(self.set_pkgs, pk, old)
        self.bg(work)

    def set_pkgs(self, pk: dict, old: dict) -> None:
        self.pkgs, self.outdated = pk, old
        self.fill_tree()

    def debounce_filter(self) -> None:
        if self.search_job:
            self.root.after_cancel(self.search_job)
        self.search_job = self.root.after(150, self.fill_tree)

    def fill_tree(self) -> None:
        q = self.search.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        n = 0
        for name, ver in self.pkgs.items():
            if q and q not in name.lower():
                continue
            latest = self.outdated.get(norm(name), "")
            self.tree.insert("", "end", iid=name, values=(name, ver, latest), tags=("old",) if latest else ())
            n += 1
        self.count.config(text=f"{n} packages, {len(self.outdated)} outdated")

    def sort_by(self, col: str) -> None:
        self.sort_rev = not self.sort_rev
        idx = {"name": 0, "version": 1, "latest": 2}[col]
        rows = sorted(((self.tree.item(i, "values")[idx].lower(), i) for i in self.tree.get_children()),
                      reverse=self.sort_rev)
        for pos, (_, iid) in enumerate(rows):
            self.tree.move(iid, "", pos)

    def selected(self) -> list[str]:
        return list(self.tree.selection())

    def popup(self, e) -> None:
        row = self.tree.identify_row(e.y)
        if row and row not in self.tree.selection():
            self.tree.selection_set(row)
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def sel_upgrade(self):
        if (s := self.selected()):
            self.task(f"Upgrading: {' '.join(s)}", [["install", "--upgrade", *s]])

    def sel_uninstall(self):
        if (s := self.selected()) and messagebox.askyesno("Uninstall", f"Uninstall {', '.join(s)}?"):
            self.task(f"Uninstalling: {' '.join(s)}", [["uninstall", "-y", *s]])

    def sel_info(self):
        if (s := self.selected()):
            self.info_window(s[0])

    def info_window(self, pkg: str) -> None:
        try:
            md = metadata.metadata(pkg)
        except metadata.PackageNotFoundError:
            messagebox.showerror("Package Info", f"No metadata found for {pkg}")
            return
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Package Info", str(e))
            return
        g = lambda k: md.get(k) or "N/A"  # noqa: E731
        w = tk.Toplevel(self.root)
        w.title(f"MetaData on {pkg}")
        w.geometry("440x240")
        t = tk.Text(w, wrap="word", padx=8, pady=8)
        t.insert("1.0", f"Name:      {g('Name')}\nVersion:   {g('Version')}\nHome Page: {g('Home-page')}\n"
                        f"Author:    {g('Author')}\nEmail:     {g('Author-email')}\nLicense:   {g('License')[:200]}\n\n"
                        f"Python Version Required: {g('Requires-Python')}")
        t.config(state="disabled")
        t.pack(fill="both", expand=True)

    # ---- autocomplete
    def load_pypi(self) -> None:
        names = load_pypi_names(self.log)
        self.pypi, self.pypi_lower = names, [n.lower() for n in names]
        self.log(f"PyPI names loaded: {len(names)}")

    def filter_names(self, e=None) -> None:
        if e is not None and e.keysym in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape"):
            return
        word = self.entry.get().split(" ")[-1].lower()
        if not word or not self.pypi_lower:
            return
        i = bisect_left(self.pypi_lower, word)
        out = []
        while i < len(self.pypi_lower) and len(out) < 30 and self.pypi_lower[i].startswith(word):
            out.append(self.pypi[i])
            i += 1
        self.entry["values"] = out

    # ---- settings
    def _set(self, key: str, val: str) -> None:
        self.cfg[key] = val
        save_cogs(self.cfg)

    def toggle_dark(self):
        self._set("darkmode", "on" if self.dark.get() else "off")
        self.apply_theme()

    def toggle_cmd(self):
        self._set("cmd", "off" if self.hide_cmd.get() else "on")
        show_console(not self.hide_cmd.get())

    def toggle_cli(self):
        self._set("cli", "on" if self.cli_var.get() else "off")

    def toggle_pypi(self):
        on = self.pypi_var.get() == 1
        self._set("pypi", "on" if on else "off")
        if on:
            messagebox.showwarning("Performance", "Autocomplete loads ~600k names; RAM use rises while enabled.")
            self.bg(self.load_pypi)
        else:
            self.pypi, self.pypi_lower = [], []

    # ---- misc
    def clear_console(self) -> None:
        self.console.config(state="normal")
        self.console.delete("1.0", "end")
        self.console.config(state="disabled")

    def check_release(self) -> None:
        self.release = fetch_release()
        self.ui(self.set_title)
        if self.release == "ERROR [NoI]":
            self.log(f"[!] Cannot reach {RELEASE_URL}")

    def auto_py_to_exe(self) -> None:
        exe = shutil.which("auto-py-to-exe")
        if exe:
            try:
                subprocess.Popen([exe], creationflags=NO_WINDOW)
            except OSError as e:
                messagebox.showerror("Auto-Py-to-EXE", str(e))
        elif messagebox.askyesno("Auto-Py-to-EXE", "Not installed. Install it now?"):
            self.task("Installing auto-py-to-exe", [["install", "--upgrade", "auto-py-to-exe"]])

    def app_info(self) -> None:
        w = tk.Toplevel(self.root)
        w.title("App Info")
        w.resizable(False, False)
        f = ttk.Frame(w, padding=16)
        f.pack()
        for line in ("PIP Manager App Info", f"App Version: {VERSION}", f"Current Release: {self.release}",
                     f"Python Version: {platform.python_version()}"):
            ttk.Label(f, text=line).pack(anchor="w")
        if self.release not in ("…", "ERROR [NoI]") and vtuple(self.release) > vtuple(VERSION):
            ttk.Button(f, text="Update", command=lambda: self.update_app(w)).pack(pady=8)
        else:
            ttk.Label(f, text="You are up to date" if self.release != "ERROR [NoI]" else "Offline").pack(pady=8)

    def update_app(self, win) -> None:
        if not messagebox.askyesno("Update", "Download the latest version and replace this file?"):
            return
        try:
            with urllib.request.urlopen(UPDATE_URL, timeout=20) as r:
                code = r.read()
            ast.parse(code.decode("utf-8"))  # refuse to install a corrupt/partial download
            me = Path(__file__).resolve()
            shutil.copy2(me, me.with_suffix(".bak"))
            me.write_bytes(code)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Update failed", str(e))
            return
        messagebox.showinfo("Complete", f"Updated to {self.release}. PIP Manager will now close; please restart it.")
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    cfg = load_cogs()
    if cfg["cli"] == "on" or not HAS_TK:
        if not HAS_TK:
            print("tkinter is not available - starting CLI mode.")
        cli()
        return
    try:
        App(cfg).run()
    except tk.TclError as e:  # e.g. no display
        print(f"GUI could not start ({e}) - falling back to CLI.")
        cli()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)