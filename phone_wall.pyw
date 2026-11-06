"""phone-wall: view many Android phones at once (scrcpy) and control one or all of them.

Settings live in config.json next to this file (copy config.example.json to start).
"""
import glob, json, os, shutil, subprocess, sys, threading, time, tkinter as tk
from tkinter import messagebox, simpledialog, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
NOWIN = 0x08000000 if os.name == "nt" else 0   # no console window flashes on Windows

TEXT = {
    "en": {
        "open_sel": "Open selected", "open_all": "Open all", "close_sel": "Close selected", "close_all": "Close all",
        "screen_off": "Turn phone screens off while controlling", "res": "Resolution",
        "select_all": "Select all", "view": "View only", "control": "Control",
        "pad": "Group control: click/drag here = sent to every ticked phone",
        "reconnect": "Reconnect adb", "add": "Add phone", "reconnected": "Reconnected",
        "sent": "Sent to {n} phone(s)", "none": "No phone ticked", "adb_ok": "adb ok", "adb_no": "adb offline",
        "open": "open", "quit": "Quit", "name": "Phone name", "addr": "ip:port (Wireless debugging)",
        "added": "Added. Restart the panel to show it.", "need_cfg": "config.json was created. Add your phones "
        "(or use the 'Add phone' button), then start again.",
        "no_scrcpy": "scrcpy not found. Put it in the 'scrcpy' folder next to this file or set scrcpy_path in config.json.",
        "no_adb": "adb not found. Install Android platform-tools or set adb_path in config.json.",
    },
    "th": {
        "open_sel": "เปิดที่เลือก", "open_all": "เปิดทั้งหมด", "close_sel": "ปิดที่เลือก", "close_all": "ปิดทั้งหมด",
        "screen_off": "ดับจอมือถือจริงตอนควบคุม", "res": "ความละเอียด",
        "select_all": "เลือกทั้งหมด", "view": "ดูอย่างเดียว", "control": "ควบคุม",
        "pad": "Group control: คลิก/ลากในกรอบ = ส่งไปทุกเครื่องที่ติ๊ก",
        "reconnect": "ต่อ adb ใหม่", "add": "เพิ่มเครื่อง", "reconnected": "ต่อใหม่แล้ว",
        "sent": "ส่งไป {n} เครื่อง", "none": "ยังไม่ได้ติ๊กเครื่อง", "adb_ok": "adb ok", "adb_no": "adb ไม่ต่อ",
        "open": "เปิดอยู่", "quit": "ออก", "name": "ชื่อเครื่อง", "addr": "ip:port (Wireless debugging)",
        "added": "เพิ่มแล้ว ปิดแล้วเปิดแผงใหม่เพื่อให้เห็นเครื่อง", "need_cfg": "สร้าง config.json ให้แล้ว ใส่เครื่องของคุณ "
        "(หรือกดปุ่ม 'เพิ่มเครื่อง') แล้วเปิดใหม่",
        "no_scrcpy": "ไม่พบ scrcpy วางไว้ในโฟลเดอร์ 'scrcpy' ข้างไฟล์นี้ หรือตั้ง scrcpy_path ใน config.json",
        "no_adb": "ไม่พบ adb ติดตั้ง Android platform-tools หรือตั้ง adb_path ใน config.json",
    },
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        example = os.path.join(HERE, "config.example.json")
        cfg = json.load(open(example)) if os.path.exists(example) else {"language": "en"}
        cfg["devices"] = {}          # the example phones are placeholders: start empty
        save_config(cfg)
        return cfg, True
    return json.load(open(CONFIG_PATH)), False


def save_config(cfg):
    json.dump(cfg, open(CONFIG_PATH, "w"), indent=2, ensure_ascii=False)


def find_tool(name, configured):
    exe = name + (".exe" if os.name == "nt" else "")
    if configured and os.path.exists(configured):
        return configured
    local = glob.glob(os.path.join(HERE, "scrcpy", "**", exe), recursive=True)
    if local:
        return local[0]
    return shutil.which(name)


CFG, FIRST_RUN = load_config()
T = TEXT.get(CFG.get("language", "en"), TEXT["en"])
SCRCPY = find_tool("scrcpy", CFG.get("scrcpy_path"))
ADB = find_tool("adb", CFG.get("adb_path"))
PHONES = list(CFG.get("devices", {}).items())
APPS = list(CFG.get("apps", {}).items())
RES = str(CFG.get("resolution", 480))
FPS = str(CFG.get("max_fps", 10))
BITRATE = str(CFG.get("bitrate_mbps", 1))
ENV = dict(os.environ, ADB=ADB or "")

holders = {}    # serial -> Popen (control-only scrcpy session that keeps the real screen off)
procs = {}      # name -> Popen (visible scrcpy window)
modes = {}      # name -> "view" | "control"
sizes = {}      # serial -> (w, h)


def adb(serial, *args, timeout=15):
    return subprocess.run([ADB, "-s", serial, *args], capture_output=True, text=True,
                          timeout=timeout, creationflags=NOWIN).stdout


def screen_size(serial):
    if serial not in sizes:
        out = adb(serial, "shell", "wm", "size")
        w, h = out.strip().split()[-1].split("x")
        sizes[serial] = (int(w), int(h))
    return sizes[serial]


class Panel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("phone-wall")
        self.checks, self.dots, self.btns = {}, {}, {}
        self.layout = self.compute_layout()
        ph = self.winfo_screenheight() - 40 - self.layout[4]
        self.geometry(f"{self.winfo_screenwidth()}x{ph}+0+{self.layout[4]}")
        sc = tk.Canvas(self, highlightthickness=0)
        bar = ttk.Scrollbar(self, orient="vertical", command=sc.yview)
        hbar = ttk.Scrollbar(self, orient="horizontal", command=sc.xview)
        sc.configure(yscrollcommand=bar.set, xscrollcommand=hbar.set)
        hbar.pack(side="bottom", fill="x")
        bar.pack(side="right", fill="y")
        sc.pack(side="left", fill="both", expand=True)
        body = ttk.Frame(sc)
        sc.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: sc.configure(scrollregion=sc.bbox("all")))
        self.bind_all("<MouseWheel>", lambda e: sc.yview_scroll(-1 * (e.delta // 120), "units"))
        self.bind_all("<Shift-MouseWheel>", lambda e: sc.xview_scroll(-1 * (e.delta // 120), "units"))

        top = ttk.Frame(body, padding=8)
        top.pack(fill="x")
        for key, cmd in [("open_sel", self.open_selected), ("open_all", self.open_all),
                         ("close_sel", self.close_selected), ("close_all", self.close_all)]:
            ttk.Button(top, text=T[key], command=cmd).pack(side="left", padx=2)
        self.screen_off = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text=T["screen_off"], variable=self.screen_off,
                        command=self.apply_screen_off).pack(side="left", padx=8)
        ttk.Label(top, text=T["res"]).pack(side="left", padx=(12, 2))
        self.res = tk.StringVar(value=RES)
        ttk.Combobox(top, textvariable=self.res, values=("480", "640", "720"), width=5,
                     state="readonly").pack(side="left")

        main = ttk.Frame(body, padding=(8, 0))
        main.pack(fill="x")
        rows = ttk.Frame(main)
        rows.pack(side="left", anchor="n")
        self.all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(rows, text=T["select_all"], variable=self.all_var, command=self.toggle_all).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 2))
        for i, (name, serial) in enumerate(PHONES):
            var = tk.BooleanVar(value=False)
            self.checks[name] = var
            ttk.Checkbutton(rows, text=name, variable=var, width=11).grid(row=i + 1, column=0, sticky="w")
            self.dots[name] = ttk.Label(rows, text="...", width=16)
            self.dots[name].grid(row=i + 1, column=1)
            b = ttk.Button(rows, text=T["view"], width=11, command=lambda n=name: self.toggle_mode(n))
            b.grid(row=i + 1, column=2, padx=4)
            self.btns[name] = b

        padbox = ttk.Frame(main, padding=(12, 0))
        padbox.pack(side="left", anchor="n")
        ttk.Label(padbox, text=T["pad"]).pack(anchor="w")
        ch = max(150, ph - 90)
        self.padh, self.padw = ch, int(ch * 0.46)
        self.canvas = tk.Canvas(padbox, width=self.padw, height=ch, bg="#222", highlightthickness=1)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<ButtonRelease-1>", self.release)

        keys = ttk.Frame(main, padding=(8, 14))
        keys.pack(side="left", anchor="n")
        for text, key in [("Back", "KEYCODE_BACK"), ("Home", "KEYCODE_HOME"), ("Recents", "KEYCODE_APP_SWITCH"),
                          ("Wake", "KEYCODE_WAKEUP"), ("Power", "KEYCODE_POWER")]:
            ttk.Button(keys, text=text, width=10, command=lambda c=key: self.group_key(c)).pack(pady=2)

        apps = ttk.Frame(main, padding=(8, 14))
        apps.pack(side="left", anchor="n")
        for name, pkg in APPS:
            r = ttk.Frame(apps)
            r.pack(pady=2)
            ttk.Button(r, text=name, width=9, command=lambda p=pkg: self.group_app(p)).pack(side="left")
            ttk.Button(r, text=T["quit"], width=5, command=lambda p=pkg: self.group_quit(p)).pack(side="left", padx=2)
        ttk.Separator(apps).pack(fill="x", pady=6)
        ttk.Button(apps, text=T["reconnect"], width=16, command=self.reconnect).pack(pady=2)
        ttk.Button(apps, text=T["add"], width=16, command=self.add_phone).pack(pady=2)
        self.status = ttk.Label(apps, text="", wraplength=140)
        self.status.pack(anchor="w", pady=4)
        self.down = None
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh()

    def on_close(self):
        self.close_all()
        self.destroy()

    def compute_layout(self):
        # tile all phones across the top of the screen, keeping a phone-like shape
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight() - 40
        n, best = max(1, len(PHONES)), None
        for rows in (1, 2, 3):
            cols = -(-n // rows)
            cw, ch = sw // cols, sh // rows
            h = min(ch, int(cw / 0.47))
            w = int(h * 0.47)
            if best is None or w * h > best[0]:
                best = (w * h, rows, cols, cw, ch, w, h)
        _, rows, cols, cw, ch, w, h = best
        return cols, cw, ch, w, h

    # ---- status
    def refresh(self):
        def work():
            out = subprocess.run([ADB, "devices"], capture_output=True, text=True, creationflags=NOWIN).stdout
            for name, serial in PHONES:
                up = f"{serial}\tdevice" in out
                p = procs.get(name)
                shown = p is not None and p.poll() is None
                txt = (T["adb_ok"] if up else T["adb_no"]) + (f" / {T['open']}" if shown else "")
                self.after(0, lambda n=name, t=txt: self.dots[n].config(text=t))
        threading.Thread(target=work, daemon=True).start()
        self.after(5000, self.refresh)

    # ---- windows
    def selected(self):
        return [(n, s) for n, s in PHONES if self.checks[n].get()]

    def launch(self, name, serial):
        self.stop(name)
        control = modes.get(name) == "control"
        idx = [x[0] for x in PHONES].index(name)
        cols, cw, ch, w, h = self.layout
        cmd = [SCRCPY, "-s", serial, "--window-title", f"{name} [{'CONTROL' if control else 'VIEW'}]",
               f"--max-size={self.res.get()}", f"--max-fps={FPS}", f"--video-bit-rate={BITRATE}M", "--no-audio",
               "--window-borderless", f"--window-x={(idx % cols) * cw}", f"--window-y={(idx // cols) * ch}",
               f"--window-width={w}", f"--window-height={h}"]
        cmd += ["--turn-screen-off"] if control and self.screen_off.get() else []
        cmd += [] if control else ["--no-control"]
        procs[name] = subprocess.Popen(cmd, env=ENV, creationflags=NOWIN,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop(self, name):
        p = procs.pop(name, None)
        if p and p.poll() is None:
            p.terminate()

    def open_list(self, items):
        for n, (name, s) in enumerate(items):
            modes.setdefault(name, "view")
            self.after(n * 1500, lambda name=name, s=s: self.launch(name, s))   # staggered: low-RAM friendly

    def open_selected(self): self.open_list(self.selected())
    def open_all(self): self.open_list(PHONES)

    def close_selected(self):
        for name, _ in self.selected():
            self.stop(name)

    def close_all(self):
        for name, _ in PHONES:
            self.stop(name)
        self.release_all()

    def toggle_mode(self, name):
        modes[name] = "view" if modes.get(name) == "control" else "control"
        if modes[name] == "control" and self.screen_off.get():
            self.hold_off(dict(PHONES)[name])
        self.btns[name].config(text=T["control"] if modes[name] == "control" else T["view"])
        if procs.get(name) and procs[name].poll() is None:
            self.launch(name, dict(PHONES)[name])

    def toggle_all(self):
        for v in self.checks.values():
            v.set(self.all_var.get())

    # ---- real screen off while controlling (control-only scrcpy session, no window)
    def hold_off(self, serial):
        p = holders.get(serial)
        if p is None or p.poll() is not None:
            holders[serial] = subprocess.Popen(
                [SCRCPY, "-s", serial, "--no-window", "--no-video", "--no-audio", "--turn-screen-off"], env=ENV,
                creationflags=NOWIN, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def release_all(self):
        for serial in list(holders):
            p = holders.pop(serial)
            if p.poll() is None:
                p.terminate()

    def apply_screen_off(self):
        # ticking = turn the real screens of the ticked phones off now; unticking = let them light up again
        if not self.screen_off.get():
            self.release_all()
            return
        for _, s in self.selected():
            self.hold_off(s)
        self.status.config(text=f"screens off: {len(self.selected())}")

    # ---- group control (adb input, scaled to each phone's screen)
    def press(self, e):
        self.down = (e.x, e.y, time.time())

    def release(self, e):
        if not self.down:
            return
        x0, y0, t0 = self.down
        ms = max(80, int((time.time() - t0) * 1000))
        fx0, fy0, fx1, fy1 = x0 / self.padw, y0 / self.padh, e.x / self.padw, e.y / self.padh
        moved = abs(e.x - x0) + abs(e.y - y0) > 8
        self.down = None
        self.broadcast(lambda s: self.send_touch(s, fx0, fy0, fx1, fy1, ms, moved))

    def send_touch(self, serial, fx0, fy0, fx1, fy1, ms, moved):
        w, h = screen_size(serial)
        if moved:
            adb(serial, "shell", "input", "swipe", str(int(fx0 * w)), str(int(fy0 * h)),
                str(int(fx1 * w)), str(int(fy1 * h)), str(ms))
        else:
            adb(serial, "shell", "input", "tap", str(int(fx0 * w)), str(int(fy0 * h)))

    def group_key(self, code):
        self.broadcast(lambda s: adb(s, "shell", "input", "keyevent", code))

    def group_app(self, pkg):
        def go(serial):
            w, h = screen_size(serial)
            adb(serial, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
            adb(serial, "shell", "input", "swipe", str(w // 2), str(int(h * 0.85)), str(w // 2), str(int(h * 0.25)), "250")
            adb(serial, "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1")
        self.broadcast(go)

    def group_quit(self, pkg):
        self.broadcast(lambda s: adb(s, "shell", "am", "force-stop", pkg))

    def broadcast(self, fn):
        targets = [s for _, s in self.selected()]
        if not targets:
            self.status.config(text=T["none"])
            return
        if self.screen_off.get():
            for s in targets:
                self.hold_off(s)
        self.status.config(text=T["sent"].format(n=len(targets)))
        for s in targets:
            threading.Thread(target=lambda s=s: self._safe(fn, s), daemon=True).start()

    def _safe(self, fn, s):
        try:
            fn(s)
        except Exception as ex:
            self.after(0, lambda: self.status.config(text=f"{s}: {ex}"))

    # ---- adb connections
    def reconnect(self):
        def go():
            for _, serial in PHONES:
                subprocess.run([ADB, "connect", serial], capture_output=True, timeout=15, creationflags=NOWIN)
            self.after(0, lambda: self.status.config(text=T["reconnected"]))
        threading.Thread(target=go, daemon=True).start()

    def add_phone(self):
        name = simpledialog.askstring(T["add"], T["name"], parent=self)
        addr = simpledialog.askstring(T["add"], T["addr"], parent=self) if name else None
        if name and addr:
            CFG.setdefault("devices", {})[name.strip()] = addr.strip()
            save_config(CFG)
            subprocess.run([ADB, "connect", addr.strip()], capture_output=True, timeout=15, creationflags=NOWIN)
            messagebox.showinfo("phone-wall", T["added"])


def main():
    if not SCRCPY or not ADB:
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("phone-wall", T["no_scrcpy"] if not SCRCPY else T["no_adb"])
        sys.exit(1)
    if FIRST_RUN and not PHONES:
        root = tk.Tk(); root.withdraw()
        messagebox.showinfo("phone-wall", T["need_cfg"])
    Panel().mainloop()


if __name__ == "__main__":
    main()
