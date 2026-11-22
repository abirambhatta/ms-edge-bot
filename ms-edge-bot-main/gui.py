"""Desktop app: today's search progress per Edge profile, run controls, and settings."""

from __future__ import annotations

import queue
import threading
import tkinter.messagebox as messagebox
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

import edge
from edge_search_bot import Progress, run_searches
from keyword_fetcher import KeywordStore
from search_history import SearchHistory
from settings import Settings
from theme import C, Fonts, Pill, card, icon, panel, primary_button, quiet_button, segmented

HERE = Path(__file__).resolve().parent
MODES = {"PC and mobile": (False, True), "PC only": (False,), "Mobile only": (True,)}
PAD = 22
QUIET_SCROLL = {"scrollbar_button_color": C["surface"], "scrollbar_button_hover_color": C["line"]}


class InvalidEntry(Exception):
    def __init__(self, entry, message: str):
        super().__init__(message)
        self.entry, self.message = entry, message


def ago(when: datetime) -> str:
    mins = int((datetime.now().astimezone() - when).total_seconds() // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} min ago"
    hours = mins // 60
    return f"{hours} hour{'s' if hours != 1 else ''} ago" if hours < 48 else f"{hours // 24} days ago"


# ── Profile card ─────────────────────────────────────────────────────────────

class ProfileCard(ctk.CTkFrame):
    """One profile: name, state, a Run button, and today's PC and mobile progress."""

    def __init__(self, master, app: "App", folder: str):
        super().__init__(master, fg_color=C["card"], corner_radius=12)
        self.app, self.folder = app, folder
        f = app.fonts
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=app.name(folder), font=f.name, text_color=C["ink"],
                     anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", padx=(18, 0), pady=(14, 0))
        self.note = ctk.CTkLabel(self, text="", font=f.small, text_color=C["muted"], anchor="w")
        self.note.grid(row=1, column=0, columnspan=2, sticky="w", padx=(18, 0))
        self.pill = Pill(self, f)
        self.pill.grid(row=0, column=2, sticky="e", padx=(0, 8), pady=(14, 0))
        self.run_btn = ctk.CTkButton(
            self, text="", width=34, height=34, corner_radius=8, image=icon("play", "accent", 14),
            fg_color=C["surface"], hover_color=C["accent_bg"], command=lambda: app.start_run([folder]))
        self.run_btn.grid(row=0, column=3, rowspan=2, sticky="e", padx=(0, 14), pady=(12, 0))

        self.bars: dict[bool, tuple[ctk.CTkProgressBar, ctk.CTkLabel]] = {}
        for r, mobile in enumerate((False, True), start=2):
            pad_y = (10, 2) if not mobile else (2, 14)
            ctk.CTkLabel(self, text="Mobile" if mobile else "PC", font=f.small, text_color=C["muted"],
                         width=50, anchor="w").grid(row=r, column=0, sticky="w", padx=(18, 0), pady=pad_y)
            bar = ctk.CTkProgressBar(self, height=12, corner_radius=6, fg_color=C["track"],
                                     progress_color=C["accent"])
            bar.grid(row=r, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=pad_y)
            count = ctk.CTkLabel(self, text="", font=f.count, text_color=C["ink"], width=64, anchor="e")
            count.grid(row=r, column=3, sticky="e", padx=(0, 18), pady=pad_y)
            self.bars[mobile] = (bar, count)
        self.refresh()

    def refresh(self, activity: str = ""):
        remaining = 0
        for mobile, (bar, count) in self.bars.items():
            done = self.app.history.done_today(self.folder, mobile)
            target = self.app.settings.target(self.folder, mobile)
            remaining += max(target - done, 0)
            finished = done >= target
            bar.set(min(done / target, 1) if target else 1)
            bar.configure(progress_color=C["done"] if finished else C["accent"] if done else C["track"])
            count.configure(text=f"{done}/{target}", text_color=C["done"] if finished else C["ink"])

        info = self.app.edge_profiles.get(self.folder)
        signed_in = self.app.signed_in.get(self.folder)
        if activity:
            self.pill.show("Running", "accent")
            self.note.configure(text=activity, text_color=C["accent"])
            return
        if info is None:
            self.pill.show("Missing", "warn")
            self.note.configure(text=f"No Edge profile folder named {self.folder}", text_color=C["warn"])
            return
        if signed_in is False:
            self.pill.show("Sign in needed", "warn")
        elif remaining == 0:
            self.pill.show("Done", "done")
        else:
            self.pill.show(f"{remaining} left", "muted")
        parts = [f"Edge folder {info.folder}"] if info.name != info.folder else []
        if signed_in:
            parts.append("Rewards signed in")
        self.note.configure(text=",  ".join(parts), text_color=C["muted"])


# ── App ──────────────────────────────────────────────────────────────────────

class App:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.fonts = Fonts()
        self.settings = Settings(HERE / "settings.json")
        self.history = SearchHistory(HERE / "search_history.json")
        self.keywords = KeywordStore(HERE / "search_cache.json")
        self.edge_profiles = {p.folder: p for p in edge.list_profiles()}

        self.events: queue.Queue = queue.Queue()  # worker threads -> UI thread
        self.stop = threading.Event()
        self.busy = self.stoppable = False
        self.signed_in: dict[str, bool] = {}
        self.cards: dict[str, ProfileCard] = {}

        root.title("Edge Searches")
        root.minsize(980, 600)
        self._center(1200, 780)
        root.configure(fg_color=C["bg"])
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        self._build_header()
        self.today = self._build_today()
        self.settings_view = self._build_settings()
        self.show("Today")

        self.log("Ready.")
        root.after(100, self._pump)
        if self.keywords.stale or not self.keywords.keywords:
            self.refresh_keywords()

    def name(self, folder: str) -> str:
        """The profile name the user sees in Edge."""
        info = self.edge_profiles.get(folder)
        return info.name if info else folder

    # ── Layout ──
    def _center(self, width: int, height: int):
        """Open centered, and never taller than the screen minus the taskbar."""
        scale = self.root._get_window_scaling()
        screen_w = self.root.winfo_screenwidth() / scale
        screen_h = self.root.winfo_screenheight() / scale
        height = min(height, int(screen_h) - 100)
        x, y = int((screen_w - width) / 2), max(0, int((screen_h - height) / 2) - 30)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_header(self):
        f = self.fonts
        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PAD, pady=(PAD, 16))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Edge searches", font=f.title,
                     text_color=C["ink"]).grid(row=0, column=0, sticky="w")
        self.subtitle = ctk.CTkLabel(header, text="", font=f.body, text_color=C["muted"])
        self.subtitle.grid(row=1, column=0, sticky="w")

        tools = ctk.CTkFrame(header, fg_color="transparent")
        tools.grid(row=0, column=1, rowspan=2, sticky="e")
        self.tool_buttons = [
            quiet_button(tools, "Refresh keywords", self.refresh_keywords, f, "refresh"),
            quiet_button(tools, "Check sign-in", self.check_sign_in, f, "shield"),
            quiet_button(tools, "Close Edge", self.close_edge, f, "close"),
        ]
        for b in self.tool_buttons:
            b.pack(side="left", padx=(0, 4))
        self.view_switch = segmented(tools, ["Today", "Settings"], f, command=self.show)
        self.view_switch.pack(side="left", padx=(14, 0))
        self._update_subtitle()

    def _build_today(self) -> ctk.CTkFrame:
        f = self.fonts
        view = ctk.CTkFrame(self.root, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)
        view.grid_columnconfigure(1, weight=0, minsize=330)
        view.grid_rowconfigure(0, weight=1)

        board = panel(view)
        board.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        board.grid_columnconfigure(0, weight=1)
        board.grid_rowconfigure(1, weight=1)

        # Summary: today's total, overall bar, and the run controls.
        summary = ctk.CTkFrame(board, fg_color="transparent")
        summary.grid(row=0, column=0, sticky="ew", padx=PAD, pady=(PAD, 6))
        summary.grid_columnconfigure(0, weight=1)
        tally = ctk.CTkFrame(summary, fg_color="transparent")
        tally.grid(row=0, column=0, sticky="w")
        self.total_done = ctk.CTkLabel(tally, text="0", font=f.big, text_color=C["ink"])
        self.total_done.pack(side="left")
        self.total_of = ctk.CTkLabel(tally, text="", font=f.body, text_color=C["muted"])
        self.total_of.pack(side="left", padx=(10, 0), pady=(12, 0))

        controls = ctk.CTkFrame(summary, fg_color="transparent")
        controls.grid(row=0, column=1, sticky="e")
        self.mode = segmented(controls, list(MODES), f, height=38)
        self.mode.set("PC and mobile")
        self.mode.pack(side="left", padx=(0, 10))
        self.run_all_btn = primary_button(controls, "Run all profiles", self.run_or_stop, f, "play",
                                          width=170)
        self.run_all_btn.pack(side="left")

        self.overall = ctk.CTkProgressBar(summary, height=6, corner_radius=3, fg_color=C["track"],
                                          progress_color=C["accent"])
        self.overall.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 6))
        self.status = ctk.CTkLabel(summary, text="", font=f.small, text_color=C["muted"], anchor="w")
        self.status.grid(row=2, column=0, columnspan=2, sticky="w")

        self.cards_frame = ctk.CTkScrollableFrame(board, fg_color="transparent", **QUIET_SCROLL)
        self.cards_frame.grid(row=1, column=0, sticky="nsew", padx=(PAD - 8, 8), pady=(4, PAD - 6))
        self.cards_frame.grid_columnconfigure((0, 1), weight=1, uniform="cards")

        # Activity log
        logp = panel(view, width=330)
        logp.grid(row=0, column=1, sticky="nsew")
        logp.grid_columnconfigure(0, weight=1)
        logp.grid_rowconfigure(1, weight=1)
        lt = ctk.CTkFrame(logp, fg_color="transparent")
        lt.grid(row=0, column=0, sticky="ew", padx=(PAD, 12), pady=(PAD - 2, 8))
        ctk.CTkLabel(lt, text="Activity", font=f.h2, text_color=C["ink"]).pack(side="left")
        quiet_button(lt, "Clear", lambda: self.log_box.delete("1.0", "end"), f, "delete",
                     color="muted", width=70, height=30).pack(side="right")
        self.log_box = ctk.CTkTextbox(logp, font=f.log, wrap="word", fg_color="transparent",
                                      text_color=C["ink"], border_width=0, spacing1=3, spacing3=3)
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=(PAD - 6, 6), pady=(0, PAD - 6))
        dark = ctk.get_appearance_mode() == "Dark"
        self.log_box.tag_config("time", foreground=C["faint"][dark])

        self._build_cards()
        return view

    def _build_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        self.cards = {}
        profiles = self.settings.profiles
        if not profiles:
            ctk.CTkLabel(self.cards_frame, text="No profiles yet. Add one in Settings.",
                         font=self.fonts.body, text_color=C["muted"]).grid(sticky="w", padx=8, pady=8)
        for i, folder in enumerate(profiles):
            c = ProfileCard(self.cards_frame, self, folder)
            c.grid(row=i // 2, column=i % 2, sticky="nsew", padx=8, pady=8)
            self.cards[folder] = c
        self._update_totals()
        self._set_busy(self.busy, self.stoppable)

    def _build_settings(self) -> ctk.CTkFrame:
        f = self.fonts
        view = panel(self.root)
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(0, weight=1)
        self.settings_body = ctk.CTkScrollableFrame(view, fg_color="transparent", **QUIET_SCROLL)
        self.settings_body.grid(row=0, column=0, sticky="nsew", padx=PAD - 8, pady=(PAD - 8, 0))
        self.settings_body.grid_columnconfigure(0, weight=3, uniform="settings")
        self.settings_body.grid_columnconfigure(1, weight=2, uniform="settings")
        foot = ctk.CTkFrame(view, fg_color="transparent")
        foot.grid(row=1, column=0, sticky="ew", padx=PAD, pady=PAD)
        self.save_btn = primary_button(foot, "Save settings", self.save_settings, f, "check", width=150)
        self.save_btn.pack(side="left")
        self.settings_msg = ctk.CTkLabel(foot, text="", font=f.body, text_color=C["muted"])
        self.settings_msg.pack(side="left", padx=14)
        self._fill_settings()
        return view

    def _fill_settings(self):
        f, body = self.fonts, self.settings_body
        for w in body.winfo_children():
            w.destroy()

        def section(row: int, col: int, title: str, note: str) -> ctk.CTkFrame:
            box = card(body)
            box.grid(row=row, column=col, rowspan=2 if col == 0 else 1, sticky="new", padx=8, pady=8)
            box.grid_columnconfigure(4, weight=1)
            ctk.CTkLabel(box, text=title, font=f.h2, text_color=C["ink"]).grid(
                row=0, column=0, columnspan=5, sticky="w", padx=20, pady=(16, 0))
            ctk.CTkLabel(box, text=note, font=f.small, text_color=C["muted"], justify="left").grid(
                row=1, column=0, columnspan=5, sticky="w", padx=20, pady=(0, 10))
            return box

        def entry(box, row, col, value, placeholder=""):
            e = ctk.CTkEntry(box, width=84, height=34, corner_radius=8, font=f.body, justify="right",
                             placeholder_text=placeholder, fg_color=C["surface"],
                             border_color=C["line"], text_color=C["ink"],
                             placeholder_text_color=C["faint"])
            if value is not None:
                e.insert(0, str(value))
            e.grid(row=row, column=col, padx=6, pady=5)
            return e

        def label(box, row, text, font=None, width=260):
            ctk.CTkLabel(box, text=text, font=font or f.body, text_color=C["ink"], anchor="w",
                         width=width).grid(row=row, column=0, sticky="w", padx=(20, 6))

        # Searches per day
        box = section(0, 0, "Searches per day", "Leave a profile's box empty to use the default.")
        for col, text in ((1, "PC"), (2, "Mobile")):
            ctk.CTkLabel(box, text=text, font=f.small, text_color=C["muted"]).grid(
                row=2, column=col, sticky="e", padx=12)
        label(box, 3, "Default for every profile", f.button)
        self.default_entries = {m: entry(box, 3, 1 + m, self.settings.default_count(m)) for m in (False, True)}
        ctk.CTkFrame(box, height=1, fg_color=C["line"]).grid(
            row=4, column=0, columnspan=5, sticky="ew", padx=20, pady=8)

        self.override_entries: dict[tuple[str, bool], ctk.CTkEntry] = {}
        r = 5
        for folder in self.settings.profiles:
            info = self.edge_profiles.get(folder)
            label(box, r, f"{info.name}  (folder {folder})" if info and info.name != folder else folder)
            for m in (False, True):
                self.override_entries[(folder, m)] = entry(
                    box, r, 1 + m, self.settings.override(folder, m), str(self.settings.default_count(m)))
            quiet_button(box, "Remove", lambda p=folder: self.remove_profile(p), f, "delete",
                         color="danger", width=96).grid(row=r, column=3, padx=(6, 0))
            r += 1

        missing = [p for p in self.edge_profiles.values() if p.folder not in self.settings.profiles]
        if missing:
            add = ctk.CTkFrame(box, fg_color="transparent")
            add.grid(row=r, column=0, columnspan=5, sticky="w", padx=20, pady=(10, 0))
            labels = {f"{p.name}  (folder {p.folder})": p.folder for p in missing}
            pick = ctk.CTkOptionMenu(add, values=list(labels), font=f.body, dropdown_font=f.body,
                                     height=34, corner_radius=8, fg_color=C["surface"],
                                     button_color=C["track"], button_hover_color=C["line"],
                                     text_color=C["ink"], width=240)
            pick.pack(side="left")
            quiet_button(add, "Add profile", lambda: self.add_profile(labels[pick.get()]), f, "add",
                         color="accent").pack(side="left", padx=8)
            r += 1
        ctk.CTkFrame(box, height=12, fg_color="transparent").grid(row=r, column=0)

        # Keywords
        box = section(0, 1, "Keywords", "How many Wikipedia topics to fetch on each refresh.")
        label(box, 2, "Keywords to fetch", width=150)
        self.keyword_entry = entry(box, 2, 1, self.settings.keyword_count)
        ctk.CTkFrame(box, height=12, fg_color="transparent").grid(row=3, column=0)

        # History
        box = section(1, 1, "Search history",
                      "Profiles skip keywords they've searched before.\n"
                      "Clearing lets them reuse old keywords and resets today's progress.")
        quiet_button(box, "Clear search history", self.clear_history, f, "delete", color="danger").grid(
            row=2, column=0, sticky="w", padx=14, pady=(0, 16))

    def show(self, view: str):
        self.view_switch.set(view)
        (self.settings_view if view == "Today" else self.today).grid_forget()
        target = self.today if view == "Today" else self.settings_view
        target.grid(row=1, column=0, sticky="nsew", padx=PAD, pady=(0, PAD))
        if view == "Settings":
            self.settings_msg.configure(text="")

    # ── Messages from worker threads ──
    def emit(self, kind: str, *payload):
        self.events.put((kind, payload))

    def log(self, message: str):
        self.log_box.insert("end", f"{datetime.now():%H:%M}  ", "time")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")

    def _pump(self):
        while True:
            try:
                kind, payload = self.events.get_nowait()
            except queue.Empty:
                break
            getattr(self, f"_on_{kind}")(*payload)
        self.root.after(100, self._pump)

    def _on_log(self, message: str):
        self.log(message)

    def _on_progress(self, p: Progress):
        mode = "mobile" if p.mobile else "PC"
        if p.keyword:
            self.set_status(f"{self.name(p.profile)}: {mode} search {p.done + 1} of {p.planned}", "accent")
        if p.profile in self.cards:
            self.cards[p.profile].refresh(f"{mode} search {p.done + 1} of {p.planned}" if p.keyword else "")
        self._update_totals()

    def _on_finished(self, message: str, color: str):
        self._set_busy(False)
        self.set_status(message, color)
        for c in self.cards.values():
            c.refresh()
        self._update_totals()
        self._update_subtitle()

    def _on_signed_in(self, folder: str, ok: bool):
        self.signed_in[folder] = ok
        if folder in self.cards:
            self.cards[folder].refresh()

    # ── State ──
    def set_status(self, text: str, color: str = "muted"):
        self.status.configure(text=text, text_color=C[color])

    def _update_totals(self):
        done = target = 0
        for folder in self.settings.profiles:
            for mobile in (False, True):
                t = self.settings.target(folder, mobile)
                done += min(self.history.done_today(folder, mobile), t)
                target += t
        self.total_done.configure(text=str(done))
        self.total_of.configure(text=f"of {target} searches done today, {datetime.now():%A %d %B}")
        self.overall.set(done / target if target else 0)
        self.overall.configure(progress_color=C["done"] if target and done >= target
                               else C["accent"] if done else C["track"])

    def _set_busy(self, busy: bool, stoppable: bool = False):
        self.busy, self.stoppable = busy, stoppable
        state = "disabled" if busy else "normal"
        for c in self.cards.values():
            c.run_btn.configure(state=state, image=icon("play", "disabled" if busy else "accent", 14))
        for b in self.tool_buttons:
            b.configure(state=state)
        self.mode.configure(state=state)
        if stoppable:
            look = {"state": "normal", "text": "Stop", "fg_color": C["danger"],
                    "hover_color": C["danger_hi"], "image": icon("stop", "on_accent", 14)}
        elif busy:
            look = {"state": "disabled", "text": "Run all profiles", "fg_color": C["track"],
                    "image": icon("play", "disabled", 14)}
        else:
            look = {"state": "normal", "text": "Run all profiles", "fg_color": C["accent"],
                    "hover_color": C["accent_hi"], "image": icon("play", "on_accent", 14)}
        self.run_all_btn.configure(**look)

    def _update_subtitle(self):
        n = len(self.keywords.keywords)
        self.subtitle.configure(text=f"{n} keywords, refreshed {ago(self.keywords.fetched_at)}" if n
                                else "No keywords yet")

    def _background(self, work, start_status: str, stoppable: bool = False):
        """Run `work()` on a thread; it returns (message, color) for the status line."""
        self._set_busy(True, stoppable)
        self.stop.clear()
        self.set_status(start_status, "accent")

        def wrapper():
            try:
                message, color = work()
            except Exception as e:  # anything unexpected still has to unlock the UI
                self.emit("log", f"Error: {e}")
                message, color = "Something went wrong. See Activity.", "danger"
            self.emit("finished", message, color)

        threading.Thread(target=wrapper, daemon=True).start()

    def _confirm_close_edge(self, action: str) -> bool:
        if not edge.edge_is_running():
            return True
        return messagebox.askyesno(
            "Close Edge?",
            f"{action} closes every Edge window. Anything unsaved in Edge will be lost.\n\n"
            "Close Edge and continue?", icon="warning")

    # ── Actions ──
    def run_or_stop(self):
        if self.busy:
            self.stop.set()
            self.run_all_btn.configure(state="disabled", text="Stopping")
            self.set_status("Stopping after the current search", "warn")
        else:
            self.start_run(self.settings.profiles)

    def start_run(self, profiles: list[str]):
        if self.busy or not profiles:
            return
        if not self.keywords.keywords:
            self.log("No keywords yet. Refresh keywords first.")
            return
        if not self._confirm_close_edge("Running searches"):
            return
        modes = MODES[self.mode.get()]

        def work():
            total = 0
            for folder in profiles:
                for mobile in modes:
                    if self.stop.is_set():
                        break
                    remaining = self.settings.target(folder, mobile) - self.history.done_today(folder, mobile)
                    total += run_searches(
                        folder, mobile, self.keywords.keywords, self.history, remaining,
                        label=self.name(folder), log=lambda m: self.emit("log", m),
                        on_progress=lambda p: self.emit("progress", p),
                        should_stop=self.stop.is_set)
            if self.stop.is_set():
                return f"Stopped after {total} searches", "warn"
            return f"Finished: {total} searches", "done"

        self._background(work, "Starting Edge", stoppable=True)

    def check_sign_in(self):
        if self.busy or not self._confirm_close_edge("Checking sign-in"):
            return

        def work():
            bad = 0
            for folder in self.settings.profiles:
                if self.stop.is_set():
                    break
                self.emit("log", f"{self.name(folder)}: opening Rewards.")
                with edge.open_browser(folder, headless=True, log=lambda m: self.emit("log", m)) as d:
                    ok = edge.rewards_signed_in(d)
                bad += not ok
                self.emit("signed_in", folder, ok)
                self.emit("log", f"{self.name(folder)}: {'signed in' if ok else 'not signed in'} to Rewards.")
            if bad:
                return f"{bad} profile{'s' if bad > 1 else ''} not signed in to Rewards", "warn"
            return "All profiles signed in to Rewards", "done"

        self._background(work, "Checking sign-in", stoppable=True)

    def refresh_keywords(self):
        if self.busy:
            return
        count = self.settings.keyword_count

        def work():
            self.emit("log", f"Fetching {count} keywords from Wikipedia.")
            n = len(self.keywords.refresh(count, log=lambda m: self.emit("log", m)))
            self.emit("log", f"Keywords refreshed: {n}.")
            return f"Keywords refreshed: {n}", "done"

        self._background(work, "Refreshing keywords")

    def close_edge(self):
        if messagebox.askyesno("Close Edge?", "Close every Edge window? Anything unsaved will be lost.",
                               icon="warning"):
            edge.close_edge()
            self.log("Edge closed.")

    def save_settings(self):
        def number(e: ctk.CTkEntry, minimum: int, blank_ok: bool = False) -> int | None:
            text = e.get().strip()
            if blank_ok and not text:
                return None
            if text.isdigit() and int(text) >= minimum:
                return int(text)
            raise InvalidEntry(e, f"Enter a whole number, {minimum} or more.")

        try:
            defaults = {m: number(e, 1) for m, e in self.default_entries.items()}
            overrides = {k: number(e, 0, blank_ok=True) for k, e in self.override_entries.items()}
            keyword_count = number(self.keyword_entry, 10)
        except InvalidEntry as bad:
            bad.entry.focus_set()
            self.settings_msg.configure(text=bad.message, text_color=C["danger"])
            return
        for m, n in defaults.items():
            self.settings.set_default_count(m, n)
        for (folder, m), n in overrides.items():
            self.settings.set_override(folder, m, n)
        self.settings.keyword_count = keyword_count
        self.settings.save()
        self._fill_settings()
        self._build_cards()
        self.settings_msg.configure(text="Settings saved.", text_color=C["done"])

    def add_profile(self, folder: str):
        self.settings.add_profile(folder)
        self.settings.save()
        self._fill_settings()
        self._build_cards()
        self.settings_msg.configure(text=f"Added {self.name(folder)}.", text_color=C["done"])

    def remove_profile(self, folder: str):
        if messagebox.askyesno("Remove profile?", f"Stop running searches for {self.name(folder)}?\n\n"
                               "This doesn't change anything in Edge."):
            self.settings.remove_profile(folder)
            self.settings.save()
            self._fill_settings()
            self._build_cards()
            self.settings_msg.configure(text=f"Removed {self.name(folder)}.", text_color=C["muted"])

    def clear_history(self):
        if messagebox.askyesno("Clear search history?",
                               "Every profile will be able to search keywords it has used before, "
                               "and today's progress resets to zero.", icon="warning"):
            self.history.clear()
            self._build_cards()
            self.settings_msg.configure(text="Search history cleared.", text_color=C["muted"])


def main():
    ctk.set_appearance_mode("system")
    root = ctk.CTk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
