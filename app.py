import csv
import time
from datetime import date
from tkinter import messagebox, filedialog

import customtkinter as ctk
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

import theme
from theme import MONO, UI, MONTHS, _apply_theme
from data import load_data, save_data, fmt
from calendar_popup import CalendarPopup


def _panel(parent, **kw):
    defaults = dict(fg_color=theme.PANEL, border_color=theme.BORDER,
                    border_width=1, corner_radius=6)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Monthly Commitment Calculator")
        self.geometry("880x800")
        self.minsize(780, 680)
        self.configure(fg_color=theme.BG)
        self.data = load_data()
        self._dark_mode = True

        today = date.today()
        self._view_month = today.month
        self._view_year  = today.year

        self._build_ui()
        self._refresh()

    # ── UI construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        # ── HEADER ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=theme.STRIP, border_color=theme.BLUE,
                            border_width=1, corner_radius=6)
        hdr.grid(row=0, column=0, padx=16, pady=(16, 6), sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="◈  MONTHLY COMMITMENT CALCULATOR",
                     font=ctk.CTkFont(family=MONO, size=13, weight="bold"),
                     text_color=theme.BLUE).grid(row=0, column=0, padx=16, pady=10, sticky="w")

        mode_lbl = "☀  LIGHT" if self._dark_mode else "☾  DARK"
        ctk.CTkButton(hdr, text=mode_lbl, width=96, height=28,
                      fg_color=theme.STRIP, hover_color=theme.BLUE_D, border_width=1,
                      border_color=theme.BLUE, text_color=theme.BLUE, corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=10, weight="bold"),
                      command=self._toggle_mode
                      ).grid(row=0, column=1, padx=0, pady=10, sticky="e")

        ctk.CTkLabel(hdr, text=date.today().strftime("%a, %d %b %Y").upper(),
                     font=ctk.CTkFont(family=MONO, size=11),
                     text_color=theme.MUTED).grid(row=0, column=2, padx=16, pady=10, sticky="e")

        # ── INCOME PANEL ──────────────────────────────────────────────────────
        inc = _panel(self)
        inc.grid(row=1, column=0, padx=16, pady=4, sticky="ew")
        inc.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(inc, text="MONTHLY INCOME",
                     font=ctk.CTkFont(family=UI, size=10, weight="bold"),
                     text_color=theme.MUTED
                     ).grid(row=0, column=0, columnspan=3, padx=16, pady=(12, 2), sticky="w")

        ctk.CTkLabel(inc, text="RM",
                     font=ctk.CTkFont(family=MONO, size=24, weight="bold"),
                     text_color=theme.BLUE
                     ).grid(row=1, column=0, padx=(16, 8), pady=(0, 14))

        self.income_entry = ctk.CTkEntry(
            inc, placeholder_text="0.00",
            font=ctk.CTkFont(family=MONO, size=24, weight="bold"),
            fg_color=theme.STRIP, border_color=theme.BORDER, text_color=theme.TEXT,
            placeholder_text_color=theme.MUTED, height=46, corner_radius=4)
        self.income_entry.grid(row=1, column=1, padx=(0, 10), pady=(0, 14), sticky="ew")
        if self.data["income"]:
            self.income_entry.insert(0, str(self.data["income"]))
        self.income_entry.bind("<KeyRelease>", self._on_income_change)

        ctk.CTkButton(
            inc, text="⟳  RESET ALL", width=120, height=46,
            fg_color=theme.STRIP, hover_color="#280010", border_width=1,
            border_color=theme.PINK, text_color=theme.PINK,
            font=ctk.CTkFont(family=MONO, size=11, weight="bold"),
            corner_radius=4, command=self._reset_all
        ).grid(row=1, column=2, padx=(0, 16), pady=(0, 14))

        # ── STATS CARDS ───────────────────────────────────────────────────────
        stats = _panel(self)
        stats.grid(row=2, column=0, padx=16, pady=4, sticky="ew")
        stats.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_income = self._stat_card(stats, "INCOME",    theme.BLUE,  col=0)
        self.lbl_commit = self._stat_card(stats, "COMMITTED", theme.PINK,  col=1)
        self.lbl_remain = self._stat_card(stats, "REMAINING", theme.GREEN, col=2)

        prog_row = ctk.CTkFrame(stats, fg_color="transparent")
        prog_row.grid(row=2, column=0, columnspan=3, padx=14, pady=(2, 4), sticky="ew")
        prog_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(prog_row, text="LOAD",
                     font=ctk.CTkFont(family=MONO, size=9, weight="bold"),
                     text_color=theme.MUTED, width=38, anchor="w").grid(row=0, column=0, padx=(0, 8))

        self.progress = ctk.CTkProgressBar(prog_row, height=8, corner_radius=4,
                                            fg_color=theme.STRIP, progress_color=theme.BLUE)
        self.progress.grid(row=0, column=1, sticky="ew")
        self.progress.set(0)

        self.lbl_pct = ctk.CTkLabel(prog_row, text="0.0%",
                                     font=ctk.CTkFont(family=MONO, size=10, weight="bold"),
                                     text_color=theme.TEXT, width=48, anchor="e")
        self.lbl_pct.grid(row=0, column=2, padx=(8, 0))

        self.lbl_status = ctk.CTkLabel(stats, text="",
                                        font=ctk.CTkFont(family=MONO, size=10),
                                        text_color=theme.MUTED)
        self.lbl_status.grid(row=3, column=0, columnspan=3, padx=14, pady=(0, 12), sticky="e")

        # ── MONTH / EXPORT BAR ────────────────────────────────────────────────
        mb = _panel(self)
        mb.grid(row=3, column=0, padx=16, pady=4, sticky="ew")
        mb.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(mb, fg_color="transparent")
        top.grid(row=0, column=0, padx=14, pady=(8, 4), sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top, text="VIEW PERIOD",
                     font=ctk.CTkFont(family=UI, size=10, weight="bold"),
                     text_color=theme.MUTED).grid(row=0, column=0, sticky="w")

        exp = ctk.CTkFrame(top, fg_color="transparent")
        exp.grid(row=0, column=1, sticky="e")
        ctk.CTkButton(exp, text="↓  CSV", width=88, height=28,
                      fg_color=theme.STRIP, hover_color=theme.BLUE_D, border_width=1,
                      border_color=theme.BLUE, text_color=theme.BLUE, corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=10, weight="bold"),
                      command=self._export_csv).pack(side="left", padx=(0, 6))
        ctk.CTkButton(exp, text="↓  PDF", width=88, height=28,
                      fg_color=theme.PINK, hover_color=theme.PINK_D,
                      text_color="white", corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=10, weight="bold"),
                      command=self._export_pdf).pack(side="left")

        yr = ctk.CTkFrame(mb, fg_color="transparent")
        yr.grid(row=1, column=0, padx=14, pady=(0, 3), sticky="ew")
        yr.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(yr, text="◂", width=28, height=26, fg_color=theme.STRIP,
                      hover_color=theme.BLUE_D, text_color=theme.BLUE, border_width=1,
                      border_color=theme.BORDER, corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=12),
                      command=self._prev_year).grid(row=0, column=0)
        self.year_label = ctk.CTkLabel(yr, text=str(self._view_year),
                                        font=ctk.CTkFont(family=MONO, size=13, weight="bold"),
                                        text_color=theme.TEXT)
        self.year_label.grid(row=0, column=1)
        ctk.CTkButton(yr, text="▸", width=28, height=26, fg_color=theme.STRIP,
                      hover_color=theme.BLUE_D, text_color=theme.BLUE, border_width=1,
                      border_color=theme.BORDER, corner_radius=4,
                      font=ctk.CTkFont(family=MONO, size=12),
                      command=self._next_year).grid(row=0, column=2)

        pills = ctk.CTkFrame(mb, fg_color="transparent")
        pills.grid(row=2, column=0, padx=14, pady=(0, 8), sticky="ew")
        for col in range(12):
            pills.grid_columnconfigure(col, weight=1)

        self.month_btns = []
        for i, m in enumerate(MONTHS):
            btn = ctk.CTkButton(
                pills, text=m[:3].upper(), height=26, corner_radius=4,
                font=ctk.CTkFont(family=MONO, size=10, weight="bold"),
                command=lambda idx=i+1: self._set_month(idx))
            btn.grid(row=0, column=i, padx=2)
            self.month_btns.append(btn)
        self._highlight_month_btn()

        # ── ADD FORM ──────────────────────────────────────────────────────────
        af = _panel(self)
        af.grid(row=4, column=0, padx=16, pady=4, sticky="ew")
        af.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(af, text="NEW COMMITMENT",
                     font=ctk.CTkFont(family=UI, size=10, weight="bold"),
                     text_color=theme.MUTED
                     ).grid(row=0, column=0, columnspan=5, padx=16, pady=(8, 2), sticky="w")

        for col, lbl in enumerate(["NAME", "AMOUNT (RM)", "DUE DATE"]):
            ctk.CTkLabel(af, text=lbl,
                         font=ctk.CTkFont(family=MONO, size=9, weight="bold"),
                         text_color=theme.MUTED
                         ).grid(row=1, column=col, padx=(16 if col == 0 else 0, 4),
                                pady=(0, 2), sticky="w")

        entry_kw = dict(fg_color=theme.STRIP, border_color=theme.BORDER,
                        text_color=theme.TEXT, placeholder_text_color=theme.MUTED,
                        corner_radius=4, height=34)

        self.entry_name   = ctk.CTkEntry(af, placeholder_text="e.g. Car loan, Rent...",
                                          width=220, **entry_kw)
        self.entry_amount = ctk.CTkEntry(af, placeholder_text="0.00", width=130, **entry_kw)

        self.entry_name.grid(row=2, column=0, padx=(16, 8), pady=(0, 8), sticky="ew")
        self.entry_amount.grid(row=2, column=1, padx=(0, 8), pady=(0, 8), sticky="ew")

        self._new_due_date: date | None = None
        self.due_btn = ctk.CTkButton(
            af, text="  PICK DATE", width=130, height=34,
            fg_color=theme.STRIP, hover_color=theme.BLUE_D, border_width=1,
            border_color=theme.BORDER, text_color=theme.MUTED, corner_radius=4,
            font=ctk.CTkFont(family=MONO, size=10),
            command=self._open_due_picker)
        self.due_btn.grid(row=2, column=2, padx=(0, 8), pady=(0, 8))

        ctk.CTkButton(
            af, text="+ ADD", width=90, height=34,
            fg_color=theme.BLUE, hover_color=theme.BLUE_D, text_color="white",
            corner_radius=4, font=ctk.CTkFont(family=MONO, size=11, weight="bold"),
            command=self._add_commitment
        ).grid(row=2, column=3, padx=(0, 16), pady=(0, 8))

        for entry in (self.entry_name, self.entry_amount):
            entry.bind("<Return>", lambda e: self._add_commitment())

        # ── COMMITMENTS LIST ──────────────────────────────────────────────────
        lf = _panel(self)
        lf.grid(row=5, column=0, padx=16, pady=(6, 16), sticky="nsew")
        lf.grid_columnconfigure(0, weight=1)
        lf.grid_rowconfigure(1, weight=1)

        self.list_header_lbl = ctk.CTkLabel(
            lf, text="COMMITMENTS",
            font=ctk.CTkFont(family=UI, size=10, weight="bold"), text_color=theme.MUTED)
        self.list_header_lbl.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.scroll = ctk.CTkScrollableFrame(lf, corner_radius=0, fg_color="transparent")
        self.scroll.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

    # ── Stat card ──────────────────────────────────────────────────────────────
    def _stat_card(self, parent, label, accent, col):
        frame = ctk.CTkFrame(parent, fg_color=theme.STRIP, border_color=accent,
                              border_width=1, corner_radius=6)
        frame.grid(row=1, column=col,
                   padx=(14 if col == 0 else 6, 6 if col < 2 else 14),
                   pady=(8, 8), sticky="nsew")
        ctk.CTkLabel(frame, text=label,
                     font=ctk.CTkFont(family=MONO, size=9, weight="bold"),
                     text_color=accent).pack(pady=(10, 2))
        val_lbl = ctk.CTkLabel(frame, text="RM 0.00",
                                font=ctk.CTkFont(family=MONO, size=17, weight="bold"),
                                text_color=theme.TEXT)
        val_lbl.pack(pady=(0, 10))
        return val_lbl

    # ── Month navigation ───────────────────────────────────────────────────────
    def _set_month(self, month: int):
        self._view_month = month
        self._highlight_month_btn()
        self._refresh()

    def _prev_year(self):
        self._view_year -= 1
        self.year_label.configure(text=str(self._view_year))
        self._refresh()

    def _next_year(self):
        self._view_year += 1
        self.year_label.configure(text=str(self._view_year))
        self._refresh()

    def _highlight_month_btn(self):
        for i, btn in enumerate(self.month_btns):
            if i + 1 == self._view_month:
                btn.configure(fg_color=theme.BLUE, hover_color=theme.BLUE_D,
                               text_color="white", border_width=0)
            else:
                btn.configure(fg_color=theme.STRIP, hover_color=theme.BLUE_D,
                               text_color=theme.MUTED, border_width=1,
                               border_color=theme.BORDER)

    # ── Date picker ────────────────────────────────────────────────────────────
    def _open_due_picker(self):
        CalendarPopup(self, initial=self._new_due_date, callback=self._on_due_picked)

    def _on_due_picked(self, d: date | None):
        self._new_due_date = d
        if d:
            self.due_btn.configure(text=d.strftime("%d %b %Y"),
                                    text_color=theme.BLUE, border_color=theme.BLUE)
        else:
            self.due_btn.configure(text="  PICK DATE",
                                    text_color=theme.MUTED, border_color=theme.BORDER)

    # ── Theme toggle ───────────────────────────────────────────────────────────
    def _toggle_mode(self):
        self._dark_mode = not self._dark_mode
        _apply_theme("dark" if self._dark_mode else "light")
        self.configure(fg_color=theme.BG)
        for w in self.winfo_children():
            w.destroy()
        self._new_due_date = None
        self._build_ui()
        self._refresh()

    # ── Reset all ──────────────────────────────────────────────────────────────
    def _reset_all(self):
        if not messagebox.askyesno(
            "Reset All",
            "This will delete ALL commitments and reset your income to zero.\n\nAre you sure?",
            icon="warning"
        ):
            return
        self.data = {"income": 0, "commitments": []}
        save_data(self.data)
        self.income_entry.delete(0, "end")
        self._new_due_date = None
        self.due_btn.configure(text="  PICK DATE",
                                text_color=theme.MUTED, border_color=theme.BORDER)
        self.entry_name.delete(0, "end")
        self.entry_amount.delete(0, "end")
        self._refresh()

    # ── Income change ──────────────────────────────────────────────────────────
    def _on_income_change(self, event=None):
        try:
            val = float(self.income_entry.get().replace(",", ""))
        except ValueError:
            val = 0
        self.data["income"] = val
        save_data(self.data)
        self._refresh()

    # ── Add / remove commitment ────────────────────────────────────────────────
    def _add_commitment(self):
        name = self.entry_name.get().strip()
        amount_str = self.entry_amount.get().strip()

        if not name:
            messagebox.showwarning("Missing field", "Please enter a commitment name.")
            self.entry_name.focus()
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid amount", "Please enter a valid amount greater than 0.")
            self.entry_amount.focus()
            return

        self.data["commitments"].append({
            "id":       int(time.time() * 1000),
            "name":     name,
            "amount":   amount,
            "due":      self._new_due_date.day if self._new_due_date else None,
            "due_date": self._new_due_date.isoformat() if self._new_due_date else None,
        })
        save_data(self.data)

        self.entry_name.delete(0, "end")
        self.entry_amount.delete(0, "end")
        self._new_due_date = None
        self.due_btn.configure(text="  PICK DATE",
                                text_color=theme.MUTED, border_color=theme.BORDER)
        self.entry_name.focus()
        self._refresh()

    def _remove_commitment(self, cid):
        self.data["commitments"] = [c for c in self.data["commitments"] if c["id"] != cid]
        # also remove from any paid lists
        for lst in self.data.get("paid", {}).values():
            if cid in lst:
                lst.remove(cid)
        save_data(self.data)
        self._refresh()

    def _toggle_paid(self, cid):
        key = f"{self._view_year}-{self._view_month:02d}"
        paid_map  = self.data.setdefault("paid", {})
        paid_list = paid_map.setdefault(key, [])
        if cid in paid_list:
            paid_list.remove(cid)
        else:
            paid_list.append(cid)
        save_data(self.data)
        self._refresh()

    # ── Filter for view month ──────────────────────────────────────────────────
    def _commitments_for_view(self):
        # All commitments are monthly recurring — show every one in every month.
        # The due date indicates which day of the month, not a one-time occurrence.
        return list(self.data["commitments"])

    # ── Refresh UI ─────────────────────────────────────────────────────────────
    def _refresh(self):
        income  = self.data["income"]
        visible = self._commitments_for_view()
        total   = sum(c["amount"] for c in visible)
        remain  = income - total
        pct     = min(total / income, 1.0) if income > 0 else 0

        self.lbl_income.configure(text=fmt(income))
        self.lbl_commit.configure(text=fmt(total))
        self.lbl_remain.configure(text=fmt(remain),
                                   text_color=theme.GREEN if remain >= 0 else theme.PINK)
        self.progress.set(pct)
        self.lbl_pct.configure(text=f"{pct*100:.1f}%")

        if pct >= 1.0:
            self.progress.configure(progress_color=theme.PINK)
            self.lbl_status.configure(
                text="[!] OVERLOADED — commitments exceed income", text_color=theme.PINK)
        elif pct >= 0.75:
            self.progress.configure(progress_color=theme.AMBER)
            self.lbl_status.configure(
                text=f"[!] HIGH LOAD — {(1-pct)*100:.1f}% of income remaining",
                text_color=theme.AMBER)
        else:
            self.progress.configure(progress_color=theme.BLUE)
            self.lbl_status.configure(
                text=f"[OK] {(1-pct)*100:.1f}% free  ({fmt(remain)})" if visible
                     else "[ ] no commitments for this period",
                text_color=theme.MUTED)

        self.list_header_lbl.configure(
            text=f"{MONTHS[self._view_month-1].upper()} {self._view_year}  /  COMMITMENTS")

        for w in self.scroll.winfo_children():
            w.destroy()

        sorted_list = sorted(
            visible, key=lambda c: c.get("due") or 99)

        if not sorted_list:
            ctk.CTkLabel(self.scroll, text="— no commitments for this period —",
                         text_color=theme.MUTED,
                         font=ctk.CTkFont(family=MONO, size=12)).pack(pady=30)
            return

        # ── Excel-style table ──────────────────────────────────────────────────
        CELL_H  = 20
        HDR_SEP = "#5a9bff"
        fh = ctk.CTkFont(family=MONO, size=11, weight="bold")
        fm = ctk.CTkFont(family=MONO, size=11)
        fn = ctk.CTkFont(family=UI,   size=12, weight="bold")
        fa = ctk.CTkFont(family=MONO, size=11, weight="bold")

        tbl = ctk.CTkFrame(self.scroll, fg_color=theme.BORDER, corner_radius=4)
        tbl.pack(fill="x", padx=6, pady=(6, 4))

        def vsep(parent, colour):
            ctk.CTkFrame(parent, fg_color=colour, width=1,
                         corner_radius=0).pack(side="left", fill="y")

        month_key = f"{self._view_year}-{self._view_month:02d}"
        paid_ids  = set(self.data.get("paid", {}).get(month_key, []))

        def _build_row(parent, bg, num_txt, name_txt, amt_txt, due_txt,
                       is_hdr=False, cid=None):
            is_paid = (not is_hdr) and (cid in paid_ids)
            r = ctk.CTkFrame(parent, fg_color=bg, corner_radius=0, height=CELL_H)
            r.pack(fill="x", pady=(0, 1))
            r.pack_propagate(False)
            sep_clr = HDR_SEP if is_hdr else theme.BORDER
            fg      = "white"      if is_hdr else (theme.MUTED if is_paid else theme.TEXT)
            fg_m    = "white"      if is_hdr else theme.MUTED
            fg_a    = "white"      if is_hdr else (theme.MUTED if is_paid else theme.PINK)
            f_name  = fh if is_hdr else fn
            f_num   = fh if is_hdr else fm
            f_amt   = fh if is_hdr else fa
            f_due   = fh if is_hdr else fm

            P = 0

            if is_hdr:
                ctk.CTkLabel(r, text="", width=90, height=CELL_H,
                             fg_color="transparent", font=fh,
                             text_color="white").pack(side="right", pady=P)
            else:
                ctk.CTkButton(r, text="✕  REMOVE", width=90, height=CELL_H,
                              fg_color="transparent", border_width=0,
                              text_color=theme.PINK, hover_color="#280010",
                              font=ctk.CTkFont(family=MONO, size=10, weight="bold"),
                              corner_radius=0,
                              command=lambda _id=cid: self._remove_commitment(_id)
                              ).pack(side="right", pady=P)
            vsep(r, sep_clr)
            ctk.CTkLabel(r, text=due_txt, width=120, height=CELL_H,
                         anchor="center", fg_color="transparent",
                         font=f_due, text_color=fg_m).pack(side="right", pady=P)
            vsep(r, sep_clr)
            ctk.CTkLabel(r, text=amt_txt, width=130, height=CELL_H,
                         anchor="center", fg_color="transparent",
                         font=f_amt, text_color=fg_a).pack(side="right", pady=P)
            vsep(r, sep_clr)

            ctk.CTkLabel(r, text=num_txt, width=46, height=CELL_H,
                         anchor="center", fg_color="transparent",
                         font=f_num, text_color=fg_m).pack(side="left", pady=P)
            vsep(r, sep_clr)

            # ── PAID tick column ──
            if is_hdr:
                ctk.CTkLabel(r, text="PAID", width=50, height=CELL_H,
                             anchor="center", fg_color="transparent",
                             font=fh, text_color="white").pack(side="left", pady=P)
            else:
                tick_txt   = "✔" if is_paid else "○"
                tick_color = theme.GREEN if is_paid else theme.MUTED
                ctk.CTkButton(r, text=tick_txt, width=50, height=CELL_H,
                              fg_color="transparent", border_width=0,
                              text_color=tick_color,
                              hover_color=theme.STRIP,
                              font=ctk.CTkFont(family=MONO, size=11, weight="bold"),
                              corner_radius=0,
                              command=lambda _id=cid: self._toggle_paid(_id)
                              ).pack(side="left", pady=P)
            vsep(r, sep_clr)

            ctk.CTkLabel(r, text=name_txt, height=CELL_H,
                         anchor="w", fg_color="transparent",
                         font=f_name, text_color=fg).pack(
                             side="left", fill="x", expand=True,
                             padx=(10, 0), pady=P)

        _build_row(tbl, theme.BLUE, "#", "NAME", "AMOUNT", "DUE DATE", is_hdr=True)

        for i, c in enumerate(sorted_list):
            bg = theme.STRIP if i % 2 == 0 else theme.PANEL

            due_day = c.get("due")
            due_str = f"Day {due_day:02d}" if due_day else "—"

            _build_row(tbl, bg,
                       num_txt=f"{i+1:02d}",
                       name_txt=c["name"],
                       amt_txt=fmt(c["amount"]),
                       due_txt=due_str,
                       cid=c["id"])

    # ── Export helpers ─────────────────────────────────────────────────────────
    def _export_rows(self):
        income  = self.data["income"]
        visible = self._commitments_for_view()
        sorted_list = sorted(
            visible, key=lambda c: c.get("due") or 99)
        rows = []
        for i, c in enumerate(sorted_list):
            due_day = c.get("due")
            due_str = f"Day {due_day}" if due_day else "—"
            rows.append((i+1, c["name"], fmt(c["amount"]), due_str))
        return rows, sum(c["amount"] for c in visible), income

    def _export_csv(self):
        month_str = f"{MONTHS[self._view_month-1]}_{self._view_year}"
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile=f"commitments_{month_str}.csv")
        if not path:
            return
        rows, total, income = self._export_rows()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([f"MONTHLY COMMITMENT REPORT — {MONTHS[self._view_month-1].upper()} {self._view_year}"])
            w.writerow([f"Monthly Income: {fmt(income)}"])
            w.writerow([])
            w.writerow(["#", "Name", "Amount", "Due Date"])
            w.writerows(rows)
            w.writerow([])
            w.writerow(["", "TOTAL",     fmt(total),          ""])
            w.writerow(["", "REMAINING", fmt(income - total), ""])
        messagebox.showinfo("Export Complete", f"CSV saved:\n{path}")

    def _export_pdf(self):
        month_str = f"{MONTHS[self._view_month-1]}_{self._view_year}"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")],
            initialfile=f"commitments_{month_str}.pdf")
        if not path:
            return
        rows, total, income = self._export_rows()
        doc = SimpleDocTemplate(path, pagesize=A4,
                                leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Monthly Commitment Report", styles["Title"]),
            Paragraph(f"{MONTHS[self._view_month-1]} {self._view_year}", styles["Heading2"]),
            Spacer(1, 10),
            Paragraph(f"<b>Monthly Income:</b> {fmt(income)}", styles["Normal"]),
            Spacer(1, 14),
        ]
        table_data = [["#", "Name", "Amount", "Due Date"]]
        for r in rows:
            table_data.append(list(r))
        table_data.append(["", "TOTAL",     fmt(total),          ""])
        table_data.append(["", "REMAINING", fmt(income - total), ""])

        t = Table(table_data, colWidths=[30, 220, 120, 120], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0),  (-1, 0),  rl_colors.HexColor("#3d8bff")),
            ("TEXTCOLOR",      (0, 0),  (-1, 0),  rl_colors.white),
            ("FONTNAME",       (0, 0),  (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0),  (-1, 0),  11),
            ("ROWBACKGROUNDS", (0, 1),  (-1, -3), [rl_colors.HexColor("#f0f4ff"),
                                                    rl_colors.white]),
            ("BACKGROUND",     (0, -2), (-1, -1), rl_colors.HexColor("#ffe0f0")),
            ("FONTNAME",       (0, -2), (-1, -1), "Helvetica-Bold"),
            ("TEXTCOLOR",      (0, -2), (-1, -1), rl_colors.HexColor("#cc1060")),
            ("ALIGN",          (0, 0),  (-1, -1), "CENTER"),
            ("ALIGN",          (1, 0),  (1, -1),  "LEFT"),
            ("GRID",           (0, 0),  (-1, -1), 0.5, rl_colors.HexColor("#cccccc")),
            ("ROWHEIGHT",      (0, 0),  (-1, -1), 20),
            ("VALIGN",         (0, 0),  (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        doc.build(story)
        messagebox.showinfo("Export Complete", f"PDF saved:\n{path}")
