import calendar
from datetime import date

import customtkinter as ctk

import theme
from theme import MONO, MONTHS


class CalendarPopup(ctk.CTkToplevel):
    def __init__(self, parent, initial: date = None, callback=None):
        super().__init__(parent)
        self.title("SELECT DATE")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=theme.BG)
        self.callback = callback

        today = date.today()
        self._year  = (initial or today).year
        self._month = (initial or today).month
        self._selected: date | None = initial

        self._build()
        self._render()

        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - self.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{px}+{py}")

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(self, fg_color=theme.STRIP, corner_radius=6,
                            border_color=theme.BLUE, border_width=1)
        nav.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        nav.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(nav, text="◂", width=32, height=28, fg_color=theme.PANEL,
                      hover_color=theme.BLUE_D, text_color=theme.BLUE, border_width=1,
                      border_color=theme.BORDER, corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=12),
                      command=self._prev_month).grid(row=0, column=0, padx=8, pady=6)

        self.nav_label = ctk.CTkLabel(nav, text="",
                                       font=ctk.CTkFont(family=MONO, size=13, weight="bold"),
                                       text_color=theme.TEXT)
        self.nav_label.grid(row=0, column=1)

        ctk.CTkButton(nav, text="▸", width=32, height=28, fg_color=theme.PANEL,
                      hover_color=theme.BLUE_D, text_color=theme.BLUE, border_width=1,
                      border_color=theme.BORDER, corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=12),
                      command=self._next_month).grid(row=0, column=2, padx=8, pady=6)

        days_frame = ctk.CTkFrame(self, fg_color="transparent")
        days_frame.grid(row=1, column=0, padx=12, pady=(0, 2), sticky="ew")
        for col, d in enumerate(["Mo","Tu","We","Th","Fr","Sa","Su"]):
            ctk.CTkLabel(days_frame, text=d, width=38,
                         font=ctk.CTkFont(family=MONO, size=10, weight="bold"),
                         text_color=theme.MUTED).grid(row=0, column=col, padx=1)

        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.grid(row=2, column=0, padx=12, pady=(0, 6), sticky="ew")

        action = ctk.CTkFrame(self, fg_color="transparent")
        action.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")
        action.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(action, text="CLEAR", height=32, fg_color="transparent",
                      border_width=1, border_color=theme.BORDER, text_color=theme.MUTED,
                      hover_color=theme.STRIP, corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=11),
                      command=self._clear).grid(row=0, column=0, padx=(0,4), sticky="ew")
        ctk.CTkButton(action, text="CONFIRM", height=32, fg_color=theme.BLUE,
                      hover_color=theme.BLUE_D, text_color="white", corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=11, weight="bold"),
                      command=self._ok).grid(row=0, column=1, padx=(4,0), sticky="ew")

    def _render(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.nav_label.configure(text=f"{MONTHS[self._month-1].upper()} {self._year}")

        weeks = calendar.monthcalendar(self._year, self._month)
        today = date.today()
        for r, week in enumerate(weeks):
            for c, day in enumerate(week):
                if day == 0:
                    ctk.CTkLabel(self.grid_frame, text="", width=38
                                 ).grid(row=r, column=c, padx=1, pady=1)
                    continue
                d = date(self._year, self._month, day)
                is_sel   = (d == self._selected)
                is_today = (d == today)
                if is_sel:
                    fg, txt = theme.BLUE, "white"
                elif is_today:
                    fg, txt = theme.STRIP, theme.PINK
                else:
                    fg, txt = "transparent", theme.TEXT
                ctk.CTkButton(
                    self.grid_frame, text=str(day), width=38, height=32,
                    fg_color=fg, hover_color=theme.BLUE_D, corner_radius=4, text_color=txt,
                    font=ctk.CTkFont(family=MONO, size=11),
                    command=lambda _d=d: self._pick(_d)
                ).grid(row=r, column=c, padx=1, pady=1)

    def _pick(self, d: date):
        self._selected = d
        self._render()

    def _prev_month(self):
        if self._month == 1:
            self._month, self._year = 12, self._year - 1
        else:
            self._month -= 1
        self._render()

    def _next_month(self):
        if self._month == 12:
            self._month, self._year = 1, self._year + 1
        else:
            self._month += 1
        self._render()

    def _clear(self):
        self._selected = None
        if self.callback:
            self.callback(None)
        self.destroy()

    def _ok(self):
        if self.callback:
            self.callback(self._selected)
        self.destroy()
