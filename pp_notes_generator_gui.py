import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import json
import urllib.request
import threading
import os
import tempfile

try:
    import pyperclip
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyperclip"])
    import pyperclip

# Application Details
APP_VERSION = "1.2.2"
# Raw URL to fetch version configuration from GitHub
VERSION_URL = "https://raw.githubusercontent.com/niels012/Hint-Notes-Generator-App/main/version.json"

WHATS_NEW = [
    "The app window now opens sized to fit the form, instead of leaving blank space below it.",
    "A slimmer, low-profile scrollbar that blends into the background.",
    "Fixed a bug where removing the last \"Standardize Others\" entry left blank space behind.",
    "The footer now shows the current app version at a glance.",
]

BG          = "#1E1E2E"
PANEL       = "#2A2A3E"
ACCENT      = "#7C6AF7"
ACCENT_HOV  = "#9B8FFF"
SUCCESS     = "#4ADE80"
TEXT        = "#E2E2F0"
TEXT_DIM    = "#8888AA"
BTN_SEL     = "#7C6AF7"
BTN_UNSEL   = "#3A3A52"
BTN_BORDER  = "#4A4A62"
DANGER      = "#FF6B6B"
FONT_HEAD   = ("Segoe UI", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)

FIELDS = {
    "1": "birthdate",
    "2": "birthplace",
    "3": "deathdate",
    "4": "deathplace",
}
FIELD_LABELS = [
    ("1", "Birthdate"),
    ("2", "Birthplace"),
    ("3", "Deathdate"),
    ("4", "Deathplace"),
]
ATTACHMENTS = [
    ("1", "PP"),
    ("2", "PP and parents"),
    ("3", "PP and spouse"),
    ("4", "Others"),
]


class AutoScrollbar(tk.Scrollbar):
    """A scrollbar that hides itself when not needed."""
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            if not self.winfo_ismapped():
                self.pack(side="right", fill="y")
        super().set(lo, hi)


class ToggleButton(tk.Frame):
    def __init__(self, master, text, bg_color=BG, command=None, **kwargs):
        super().__init__(master, bg=bg_color, **kwargs)
        self.selected = False
        self.command = command
        self.btn = tk.Label(
            self, text=text, font=FONT_BODY, fg=TEXT_DIM,
            bg=BTN_UNSEL, padx=10, pady=6, cursor="hand2", relief="flat",
        )
        self.btn.pack(fill="both", expand=True)
        self.btn.bind("<Button-1>", self._on_click)
        self.btn.bind("<Enter>", self._on_enter)
        self.btn.bind("<Leave>", self._on_leave)

    def _on_click(self, _=None):
        self.selected = not self.selected
        self._refresh()
        if self.command:
            self.command()

    def _on_enter(self, _=None):
        if not self.selected:
            self.btn.config(bg="#484860")

    def _on_leave(self, _=None):
        if not self.selected:
            self.btn.config(bg=BTN_UNSEL)

    def _refresh(self):
        if self.selected:
            self.btn.config(bg=BTN_SEL, fg="white")
        else:
            self.btn.config(bg=BTN_UNSEL, fg=TEXT_DIM)

    def deselect(self):
        self.selected = False
        self._refresh()


class RadioButton(tk.Frame):
    def __init__(self, master, text, value, var, command=None, **kwargs):
        super().__init__(master, bg=BG, **kwargs)
        self.value = value
        self.var = var
        self.command = command
        self.btn = tk.Label(
            self, text=text, font=FONT_BODY, fg=TEXT_DIM,
            bg=BTN_UNSEL, padx=14, pady=7, cursor="hand2", relief="flat",
        )
        self.btn.pack(fill="both", expand=True)
        self.btn.bind("<Button-1>", self._on_click)
        self.btn.bind("<Enter>", self._on_enter)
        self.btn.bind("<Leave>", self._on_leave)

    def _on_click(self, _=None):
        if self.var.get() == self.value:
            self.var.set("")
        else:
            self.var.set(self.value)
        self.refresh()
        if self.command:
            self.command()

    def _on_enter(self, _=None):
        if not self.var.get() == self.value:
            self.btn.config(bg="#484860")

    def _on_leave(self, _=None):
        if not self.var.get() == self.value:
            self.btn.config(bg=BTN_UNSEL)

    def refresh(self):
        if self.var.get() == self.value:
            self.btn.config(bg=BTN_SEL, fg="white")
        else:
            self.btn.config(bg=BTN_UNSEL, fg=TEXT_DIM)


class OtherPersonRow(tk.Frame):
    def __init__(self, master, on_remove, on_interaction=None, **kwargs):
        super().__init__(master, bg=PANEL, **kwargs)
        self._toggles: list[ToggleButton] = []
        self._on_remove = on_remove
        self._on_interaction = on_interaction
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=PANEL)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Name:", font=FONT_SMALL,
                 fg=TEXT_DIM, bg=PANEL).pack(side="left")

        self._name_var = tk.StringVar()
        self._name_var.trace_add("write", lambda *_: self._interact())
        name_entry = tk.Entry(
            top, textvariable=self._name_var,
            font=FONT_BODY, fg=TEXT, bg="#16162A",
            insertbackground=TEXT, relief="flat",
            width=24,
        )
        name_entry.pack(side="left", padx=6, ipady=4, fill="x", expand=True)
        name_entry.focus_set()

        remove_btn = tk.Label(top, text="✕", font=FONT_BODY,
                              fg=DANGER, bg=PANEL, cursor="hand2", padx=6)
        remove_btn.pack(side="right")
        remove_btn.bind("<Button-1>", lambda _: self._on_remove(self))
        remove_btn.bind("<Enter>", lambda _: remove_btn.config(fg="#FF9999"))
        remove_btn.bind("<Leave>", lambda _: remove_btn.config(fg=DANGER))

        grid = tk.Frame(self, bg=PANEL)
        grid.pack(fill="x", padx=10, pady=(0, 10))

        for col, (key, label) in enumerate(FIELD_LABELS):
            tb = ToggleButton(grid, f"{key}. {label}", bg_color=PANEL,
                              command=self._interact)
            tb.grid(row=0, column=col, padx=3, pady=2, sticky="ew")
            grid.columnconfigure(col, weight=1)
            self._toggles.append(tb)

    def _interact(self):
        if self._on_interaction:
            self._on_interaction()

    def get_name(self):
        return self._name_var.get().strip()

    def get_fields(self):
        return [
            FIELDS[str(i + 1)]
            for i, tb in enumerate(self._toggles)
            if tb.selected
        ]

    def reset(self):
        self._name_var.set("")
        for tb in self._toggles:
            tb.deselect()


class PPNotesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Updated Title
        self.title("Hint Notes Generator")
        self.resizable(True, True)
        self.minsize(480, 500)
        self.configure(bg=BG)

        # Set App Icon (PNG or ICO)
        try:
            self.iconbitmap("logo.ico")
        except Exception:
            try:
                icon = tk.PhotoImage(file="logo.png")
                self.iconphoto(False, icon)
            except Exception:
                pass

        self._field_toggles: list[ToggleButton] = []
        self._attach_radios: list[RadioButton] = []
        self._attach_var = tk.StringVar(value="")
        self._other_rows: list[OtherPersonRow] = []
        
        self._history: list[str] = []

        # ── settings state ────────────────────────────────────────────────────
        self._sw_enabled       = tk.BooleanVar(value=True)
        self._history_enabled  = tk.BooleanVar(value=True)
        
        # ── stopwatch state ───────────────────────────────────────────────────
        self._sw_seconds   = 0
        self._sw_running   = False
        self._sw_job       = None
        self._sw_blink_job = None
        self._sw_blink_on  = False

        self._build_ui()
        self._size_to_content()

    def _size_to_content(self):
        """Sizes the window to show content up through the Generated Note box;
        everything below (history, reset, footer) stays reachable by scrolling."""
        self.update_idletasks()
        w = 540
        header_h = self._header.winfo_reqheight()
        footer_h = self._footer.winfo_reqheight()
        visible_body_h = self._out_frame.winfo_y() + self._out_frame.winfo_height() + 16
        h = header_h + visible_body_h + footer_h
        h = min(h, self.winfo_screenheight() - 80)
        h = max(h, self.minsize()[1])
        sx, sy = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sx-w)//2}+{(sy-h)//2}")

    # ══════════════════════════════════════════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # ── sticky header bar (never scrolls) ─────────────────────────────────
        hdr = tk.Frame(self, bg=ACCENT)
        hdr.pack(fill="x", side="top")
        self._header = hdr

        # hamburger (left)
        ham = tk.Label(hdr, text="☰", font=("Segoe UI", 14),
                       fg="white", bg=ACCENT, cursor="hand2", padx=10, pady=14)
        ham.pack(side="left")
        ham.bind("<Button-1>", lambda _: self._toggle_settings())
        ham.bind("<Enter>", lambda _: ham.config(bg=ACCENT_HOV))
        ham.bind("<Leave>", lambda _: ham.config(bg=ACCENT))

        # title (center)
        tk.Label(hdr, text="Hint Notes Generator",
                 font=("Segoe UI", 14, "bold"),
                 fg="white", bg=ACCENT, pady=14).pack(side="left", expand=True)
        
        # stopwatch (right)
        self._sw_label = tk.Label(
            hdr, text="00:00",
            font=("Consolas", 12, "bold"),
            fg="white", bg=ACCENT, padx=12, pady=14,
        )
        self._sw_label.pack(side="right")

        # ── settings panel (hidden by default) ───────────────────────────────
        self._settings_frame = tk.Frame(self, bg=PANEL)

        sw_row = tk.Frame(self._settings_frame, bg=PANEL)
        sw_row.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(sw_row, text="Show Stopwatch",
                 font=FONT_BODY, fg=TEXT, bg=PANEL).pack(side="left")

        self._sw_toggle_btn = tk.Label(
            sw_row, text="ON",
            font=("Segoe UI", 9, "bold"),
            fg="white", bg=ACCENT,
            padx=10, pady=3, cursor="hand2",
        )
        self._sw_toggle_btn.pack(side="right")
        self._sw_toggle_btn.bind("<Button-1>", lambda _: self._toggle_sw_enabled())

        hist_row = tk.Frame(self._settings_frame, bg=PANEL)
        hist_row.pack(fill="x", padx=16, pady=(4, 4))
        tk.Label(hist_row, text="Show Previously Generated",
                 font=FONT_BODY, fg=TEXT, bg=PANEL).pack(side="left")

        self._hist_toggle_btn = tk.Label(
            hist_row, text="ON",
            font=("Segoe UI", 9, "bold"),
            fg="white", bg=ACCENT,
            padx=10, pady=3, cursor="hand2",
        )
        self._hist_toggle_btn.pack(side="right")
        self._hist_toggle_btn.bind("<Button-1>", lambda _: self._toggle_history_enabled())

        # Check for Updates button in Settings
        update_row = tk.Frame(self._settings_frame, bg=PANEL)
        update_row.pack(fill="x", padx=16, pady=(4, 4))
        tk.Label(update_row, text=f"App Version: v{APP_VERSION}",
                 font=FONT_BODY, fg=TEXT_DIM, bg=PANEL).pack(side="left")

        self._check_update_btn = tk.Label(
            update_row, text="Check for Updates",
            font=("Segoe UI", 9, "bold"),
            fg="white", bg=BTN_UNSEL,
            padx=10, pady=3, cursor="hand2",
        )
        self._check_update_btn.pack(side="right")
        self._check_update_btn.bind("<Button-1>", lambda _: self._check_for_updates())

        # "What's New" link in Settings — expands inline, right below the link
        whats_new_row = tk.Frame(self._settings_frame, bg=PANEL)
        whats_new_row.pack(fill="x", padx=16, pady=(4, 10))

        self._whats_new_link = tk.Label(
            whats_new_row, text="✨ What's New in this version  ▾",
            font=("Segoe UI", 9, "underline"),
            fg=ACCENT_HOV, bg=PANEL, cursor="hand2",
        )
        self._whats_new_link.pack(side="left")
        self._whats_new_link.bind("<Button-1>", lambda _: self._toggle_whats_new())
        self._whats_new_link.bind("<Enter>", lambda _: self._whats_new_link.config(fg="white"))
        self._whats_new_link.bind("<Leave>", lambda _: self._whats_new_link.config(fg=ACCENT_HOV))

        self._whats_new_panel = tk.Frame(self._settings_frame, bg="#22223A")
        self._whats_new_expanded = False

        list_frame = tk.Frame(self._whats_new_panel, bg="#22223A")
        list_frame.pack(fill="x", padx=16, pady=(4, 12))
        for item in WHATS_NEW:
            row = tk.Frame(list_frame, bg="#22223A")
            row.pack(fill="x", pady=3, anchor="n")
            tk.Label(row, text="•", font=FONT_SMALL, fg=ACCENT_HOV,
                     bg="#22223A").pack(side="left", anchor="n")
            tk.Label(row, text=item, font=FONT_SMALL, fg=TEXT, bg="#22223A",
                     wraplength=420, justify="left",
                     anchor="w").pack(side="left", padx=(8, 0), fill="x")

        # ── scrollable canvas ──────────────────────────────────────────────────
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, side="top")

        scrollbar = AutoScrollbar(
            container, orient="vertical",
            width=8, bd=0, relief="flat", elementborderwidth=0,
            highlightthickness=0,
            troughcolor=BG, bg="#4A4A62",
            activebackground=ACCENT_HOV,
        )

        canvas = tk.Canvas(container, bg=BG, highlightthickness=0,
                            yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)
        self._canvas = canvas

        self._body = tk.Frame(canvas, bg=BG, padx=24, pady=16)
        self._body_win = canvas.create_window(
            (0, 0), window=self._body, anchor="nw"
        )

        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(self._body_win, width=e.width))
        self._body.bind("<Configure>", self._on_body_resize)
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        body = self._body

        # ── Section 1 ─────────────────────────────────────────────────────────
        lbl_frame = tk.Frame(body, bg=BG)
        lbl_frame.pack(fill="x", pady=8)
        tk.Label(lbl_frame, text="1  What did you standardize on PP?",
                 font=FONT_HEAD, fg=TEXT, bg=BG).pack(side="left")
        tk.Label(lbl_frame, text="optional",
                 font=FONT_SMALL, fg=TEXT_DIM, bg=BG).pack(side="left", padx=8)

        field_grid = tk.Frame(body, bg=BG)
        field_grid.pack(fill="x", pady=4)
        for col, (key, label) in enumerate(FIELD_LABELS):
            tb = ToggleButton(field_grid, f"{key}. {label}",
                              command=self._on_interaction)
            tb.grid(row=0, column=col, padx=4, pady=4, sticky="ew")
            field_grid.columnconfigure(col, weight=1)
            self._field_toggles.append(tb)

        self._divider(body)

        # ── Section 2 ─────────────────────────────────────────────────────────
        sec2_hdr = tk.Frame(body, bg=BG)
        sec2_hdr.pack(fill="x", pady=4)
        tk.Label(sec2_hdr, text="2  What did you attach?", font=FONT_HEAD,
                 fg=TEXT, bg=BG).pack(side="left")
        tk.Label(sec2_hdr, text="optional", font=FONT_SMALL,
                 fg=TEXT_DIM, bg=BG).pack(side="left", padx=8)

        attach_grid = tk.Frame(body, bg=BG)
        attach_grid.pack(fill="x", pady=4)
        for col, (val, label) in enumerate(ATTACHMENTS):
            rb = RadioButton(attach_grid, f"{val}. {label}",
                             value=val, var=self._attach_var,
                             command=self._on_attach_change)
            rb.grid(row=0, column=col, padx=4, pady=4, sticky="ew")
            attach_grid.columnconfigure(col, weight=1)
            self._attach_radios.append(rb)

        self._divider(body)

        # ── Section 3 ─────────────────────────────────────────────────────────
        sec3_hdr = tk.Frame(body, bg=BG)
        sec3_hdr.pack(fill="x", pady=4)

        lbl3 = tk.Frame(sec3_hdr, bg=BG)
        lbl3.pack(side="left")
        tk.Label(lbl3, text="3  Standardize Others?",
                 font=FONT_HEAD, fg=TEXT, bg=BG).pack(side="left")
        tk.Label(lbl3, text="optional",
                 font=FONT_SMALL, fg=TEXT_DIM, bg=BG).pack(side="left", padx=8)

        add_btn = tk.Label(sec3_hdr, text="  +  ",
                           font=("Segoe UI", 13, "bold"),
                           fg="white", bg=ACCENT, cursor="hand2")
        add_btn.pack(side="right", pady=2)
        add_btn.bind("<Button-1>", lambda _: self._add_person())
        add_btn.bind("<Enter>", lambda _: add_btn.config(bg=ACCENT_HOV))
        add_btn.bind("<Leave>", lambda _: add_btn.config(bg=ACCENT))

        self._others_body = body
        self._others_container = tk.Frame(body, bg=BG)
        self._others_container.pack(fill="x")

        self._sec3_divider = tk.Frame(body, bg=BTN_BORDER, height=1)
        self._sec3_divider.pack(fill="x", pady=10)

        # ── Generate button ────────────────────────────────────────────────────
        gen_btn = tk.Label(
            body, text="Generate Note",
            font=("Segoe UI", 11, "bold"), fg="white", bg=ACCENT,
            padx=20, pady=10, cursor="hand2", relief="flat",
        )
        gen_btn.pack(fill="x", pady=4)
        gen_btn.bind("<Button-1>", self._generate)
        gen_btn.bind("<Enter>", lambda _: gen_btn.config(bg=ACCENT_HOV))
        gen_btn.bind("<Leave>", lambda _: gen_btn.config(bg=ACCENT))

        # ── Output box ─────────────────────────────────────────────────────────
        out_frame = tk.Frame(body, bg=PANEL)
        out_frame.pack(fill="x", pady=12)
        self._out_frame = out_frame

        out_hdr = tk.Frame(out_frame, bg=PANEL)
        out_hdr.pack(fill="x", padx=14, pady=8)
        tk.Label(out_hdr, text="Generated Note",
                 font=FONT_HEAD, fg=TEXT, bg=PANEL).pack(side="left")
        self._copy_lbl = tk.Label(out_hdr, text="",
                                  font=FONT_SMALL, fg=SUCCESS, bg=PANEL)
        self._copy_lbl.pack(side="right")

        self._output = tk.Text(
            out_frame, font=FONT_MONO, fg=TEXT, bg="#16162A",
            relief="flat", height=4, wrap="word",
            state="disabled", padx=10, pady=8,
        )
        self._output.pack(fill="x", padx=14, pady=(0, 10))

        # ── Previously Generated Notes Frame ──────────────────────────────────
        self._history_frame = tk.Frame(body, bg=BG)
        self._history_frame.pack(fill="x", pady=(0, 8))

        # ── Reset button ───────────────────────────────────────────────────────
        reset_btn = tk.Label(body, text="↺  Reset", font=FONT_SMALL,
                             fg=TEXT_DIM, bg=BG, cursor="hand2", pady=8)
        reset_btn.pack()
        reset_btn.bind("<Button-1>", lambda _: self._reset_form_and_timer())
        reset_btn.bind("<Enter>", lambda _: reset_btn.config(fg=TEXT))
        reset_btn.bind("<Leave>", lambda _: reset_btn.config(fg=TEXT_DIM))

        # ── Sticky Footer (bottom of app window) ──────────────────────────────
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill="x", side="bottom", pady=8)
        self._footer = footer
        tk.Label(
            footer,
            text=f"by: Nilo A. Urmeneta Jr | © 2026 | v{APP_VERSION}",
            font=FONT_SMALL,
            fg=TEXT_DIM,
            bg=BG
        ).pack(anchor="center")

    # ══════════════════════════════════════════════════════════════════════════
    # MANUAL & SILENT AUTO UPDATE LOGIC
    # ══════════════════════════════════════════════════════════════════════════

    def _check_for_updates(self):
        """Allows users to check for updates manually from the settings panel."""
        self._check_update_btn.config(text="Checking...", bg=BTN_UNSEL)

        def _fetch():
            try:
                req = urllib.request.Request(
                    VERSION_URL,
                    headers={"User-Agent": "HintNotesGeneratorApp/1.0.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    latest_version = data.get("version", APP_VERSION)
                    download_url = data.get("download_url", "")
                    
                    self.after(0, lambda: self._handle_update_response(latest_version, download_url))
            except Exception as err:
                self.after(0, lambda: self._handle_update_response(None, "", str(err)))

        threading.Thread(target=_fetch, daemon=True).start()

    def _handle_update_response(self, latest_version, download_url="", error=None):
        self._check_update_btn.config(text="Check for Updates", bg=BTN_UNSEL)
        if error:
            messagebox.showerror("Update Error", f"Failed to check for updates.\n\nError: {error}")
            return

        if latest_version and latest_version > APP_VERSION:
            answer = messagebox.askyesno(
                "Update Available",
                f"A new version is available!\n\n"
                f"Current Version: {APP_VERSION}\n"
                f"Latest Version: {latest_version}\n\n"
                f"Would you like to update now?"
            )
            if answer and download_url:
                self._download_and_install_update(download_url)
        else:
            messagebox.showinfo("Up to Date", f"You are using the latest version (v{APP_VERSION}).")

    def _download_and_install_update(self, download_url):
        """Downloads the installer to %TEMP% and runs it silently."""
        self._check_update_btn.config(text="Updating...", bg=BTN_UNSEL)

        def _download_thread():
            try:
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, "Hint_Notes_Generator_Update.exe")

                req = urllib.request.Request(
                    download_url,
                    headers={"User-Agent": "HintNotesGeneratorApp/1.0.0"}
                )
                with urllib.request.urlopen(req, timeout=30) as response, open(installer_path, "wb") as out_file:
                    out_file.write(response.read())

                # Force-kill any running instances of the app executable first
                if sys.platform == "win32":
                    os.system("taskkill /f /im Hint_Notes_Generator.exe")

                # Launch installer silently
                subprocess.Popen([installer_path, "/SILENT", "/NORESTART", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])
                self.after(100, self.destroy)

            except Exception as err:
                self.after(0, lambda: messagebox.showerror("Update Failed", f"Could not download update.\n\nError: {err}"))
                self.after(0, lambda: self._check_update_btn.config(text="Check for Updates", bg=BTN_UNSEL))

        threading.Thread(target=_download_thread, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # SETTINGS PANEL
    # ══════════════════════════════════════════════════════════════════════════

    def _toggle_settings(self):
        if self._settings_frame.winfo_ismapped():
            self._settings_frame.pack_forget()
        else:
            self._settings_frame.pack(fill="x", after=self.winfo_children()[0])

    def _toggle_sw_enabled(self):
        self._sw_enabled.set(not self._sw_enabled.get())
        if self._sw_enabled.get():
            self._sw_toggle_btn.config(text="ON", bg=ACCENT)
            self._sw_label.pack(side="right")
        else:
            self._sw_stop()
            self._sw_label.pack_forget()
            self._sw_toggle_btn.config(text="OFF", bg=BTN_UNSEL)

    def _toggle_history_enabled(self):
        self._history_enabled.set(not self._history_enabled.get())
        if self._history_enabled.get():
            self._hist_toggle_btn.config(text="ON", bg=ACCENT)
            self._history_frame.pack(fill="x", pady=(0, 8), before=self.winfo_children()[-1])
        else:
            self._hist_toggle_btn.config(text="OFF", bg=BTN_UNSEL)
            self._history_frame.pack_forget()

    def _toggle_whats_new(self):
        """Expands/collapses the What's New list directly under its link."""
        self._whats_new_expanded = not self._whats_new_expanded
        if self._whats_new_expanded:
            self._whats_new_link.config(text="✨ What's New in this version  ▴")
            self._whats_new_panel.pack(fill="x")
        else:
            self._whats_new_link.config(text="✨ What's New in this version  ▾")
            self._whats_new_panel.pack_forget()

    # ══════════════════════════════════════════════════════════════════════════
    # STOPWATCH
    # ══════════════════════════════════════════════════════════════════════════

    def _sw_start(self):
        if not self._sw_enabled.get():
            return
        if self._sw_running:
            return
        self._sw_seconds = 0
        self._sw_running = True
        self._sw_tick()

    def _sw_stop(self):
        self._sw_running = False
        if self._sw_job:
            self.after_cancel(self._sw_job)
            self._sw_job = None

    def _sw_reset_and_stop(self):
        self._sw_stop()
        self._sw_seconds = 0
        self._sw_label.config(text="00:00", fg="white")

    def _sw_tick(self):
        if not self._sw_running:
            return
        self._sw_seconds += 1
        m, s = divmod(self._sw_seconds, 60)
        self._sw_label.config(text=f"{m:02d}:{s:02d}", fg="white")
        self._sw_job = self.after(1000, self._sw_tick)

    def _sw_blink(self, count=6):
        if count <= 0:
            self._sw_label.config(fg="white")
            self._sw_stop()
            return
        self._sw_blink_on = not self._sw_blink_on
        self._sw_label.config(fg="white" if self._sw_blink_on else ACCENT)
        self._sw_blink_job = self.after(500, lambda: self._sw_blink(count - 1))

    def _archive_current_output(self):
        """Clears the output field and shifts existing text to the history area."""
        current_text = self._output.get("1.0", "end-1c").strip()
        if current_text:
            self._history.insert(0, current_text)
            self._history = self._history[:2]
            self._update_history_display()
            self._output.config(state="normal")
            self._output.delete("1.0", "end")
            self._output.config(state="disabled")

    def _on_interaction(self):
        self._archive_current_output()

        if not self._sw_enabled.get():
            return
        if self._sw_blink_job:
            self.after_cancel(self._sw_blink_job)
            self._sw_blink_job = None
        self._sw_label.config(fg="white")
        
        if not self._sw_running:
            self._sw_start()

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_body_resize(self, _event=None):
        """Keeps the scroll view clamped to the (possibly shrunk) content,
        so removing a row doesn't leave dangling blank space below it."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._canvas.yview_moveto(self._canvas.yview()[0])

    def _divider(self, parent):
        tk.Frame(parent, bg=BTN_BORDER, height=1).pack(fill="x", pady=10)

    def _on_attach_change(self):
        for rb in self._attach_radios:
            rb.refresh()
        self._on_interaction()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 LOGIC
    # ══════════════════════════════════════════════════════════════════════════

    def _add_person(self):
        row = OtherPersonRow(
            self._others_container,
            on_remove=self._remove_person,
            on_interaction=self._on_interaction,
        )
        row.pack(fill="x", pady=(0, 6))
        self._other_rows.append(row)
        self._on_interaction()

    def _remove_person(self, row):
        row.destroy()
        self._other_rows.remove(row)
        if not self._other_rows:
            # Tk quirk: a frame doesn't re-shrink when its last child is
            # destroyed, so rebuild it fresh to reclaim the space.
            self._others_container.destroy()
            self._others_container = tk.Frame(self._others_body, bg=BG)
            self._others_container.pack(fill="x", before=self._sec3_divider)
        self._on_interaction()

    # ══════════════════════════════════════════════════════════════════════════
    # GENERATE & HISTORY
    # ══════════════════════════════════════════════════════════════════════════

    def _generate(self, _=None):
        parts = []

        attach_val = self._attach_var.get()
        if attach_val:
            attachment = dict(ATTACHMENTS)[attach_val]
            parts.append(f"Attached {attachment}.")

        pp_fields = [
            FIELDS[str(i + 1)]
            for i, tb in enumerate(self._field_toggles)
            if tb.selected
        ]
        if pp_fields:
            parts.append(f"Standardized PP's {self._join_fields(pp_fields)}.")

        for row in self._other_rows:
            name = row.get_name()
            fields = row.get_fields()
            if name and fields:
                parts.append(f"Standardized {name}'s {self._join_fields(fields)}.")

        note = " ".join(parts)

        self._archive_current_output()

        self._output.config(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("1.0", note)
        self._output.config(state="disabled")

        if note:
            try:
                pyperclip.copy(note)
                self._copy_lbl.config(text="✓ Copied!")
                self.after(2500, lambda: self._copy_lbl.config(text=""))
            except Exception:
                pass

        if self._sw_enabled.get():
            self._sw_stop()
            self._sw_blink(count=6)

        self.after(300, self._reset_form)

    def _copy_history_item(self, text, btn_label):
        """Copies a specific history entry and gives visual feedback on the button."""
        try:
            pyperclip.copy(text)
            btn_label.config(text="✓ Copied", fg=SUCCESS)
            self.after(2000, lambda: btn_label.config(text="Copy", fg="white"))
        except Exception:
            pass

    def _update_history_display(self):
        """Refreshes the history UI box with up to 2 items including copy buttons."""
        for child in self._history_frame.winfo_children():
            child.destroy()

        if not self._history:
            return

        tk.Label(self._history_frame, text="Previously Generated", font=FONT_SMALL,
                 fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(0, 4))

        for text in self._history:
            row_frame = tk.Frame(self._history_frame, bg=PANEL)
            row_frame.pack(fill="x", pady=2)

            box = tk.Label(
                row_frame, text=text, font=FONT_MONO,
                fg=TEXT_DIM, bg=PANEL, anchor="w", justify="left",
                padx=10, pady=6, wraplength=380
            )
            box.pack(side="left", fill="x", expand=True)

            copy_btn = tk.Label(
                row_frame, text="Copy", font=FONT_SMALL,
                fg="white", bg=BTN_UNSEL, padx=10, pady=4, cursor="hand2"
            )
            copy_btn.pack(side="right", padx=8, pady=4)

            copy_btn.bind(
                "<Button-1>",
                lambda _, t=text, b=copy_btn: self._copy_history_item(t, b)
            )
            copy_btn.bind("<Enter>", lambda _, b=copy_btn: b.config(bg=ACCENT) if b.cget("text") == "Copy" else None)
            copy_btn.bind("<Leave>", lambda _, b=copy_btn: b.config(bg=BTN_UNSEL) if b.cget("text") == "Copy" else None)

    def _join_fields(self, fields):
        if len(fields) == 1:
            return fields[0]
        elif len(fields) == 2:
            return f"{fields[0]} and {fields[1]}"
        else:
            return ", ".join(fields[:-1]) + ", and " + fields[-1]

    def _reset_form(self):
        for tb in self._field_toggles:
            tb.deselect()
        self._attach_var.set("")
        for rb in self._attach_radios:
            rb.refresh()
        self._others_container.destroy()
        self._other_rows.clear()
        self._others_container = tk.Frame(self._others_body, bg=BG)
        self._others_container.pack(fill="x", before=self._sec3_divider)

    def _reset_form_and_timer(self):
        self._archive_current_output()
        self._reset_form()
        self._sw_reset_and_stop()


if __name__ == "__main__":
    app = PPNotesApp()
    app.mainloop()