import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading

BASE_URL = "http://127.0.0.1:8000/api/habits"

BG       = "#0f0f13"
BG2      = "#1a1a24"
BG3      = "#23232f"
ACCENT   = "#7c6af7"
ACCENT2  = "#a78bfa"
SUCCESS  = "#4ade80"
DANGER   = "#f87171"
WARNING  = "#fbbf24"
TEXT     = "#e2e8f0"
TEXT_DIM = "#64748b"
BORDER   = "#2e2e3e"


def api_get(path, params=None):
    return requests.get(BASE_URL + path, params=params, timeout=5)

def api_post(path, data):
    return requests.post(BASE_URL + path, json=data, timeout=5)

def api_patch(path):
    return requests.patch(BASE_URL + path, timeout=5)

def api_delete(path):
    return requests.delete(BASE_URL + path, timeout=5)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Habit Tracker")
        self.geometry("960x660")
        self.minsize(800, 580)
        self.configure(bg=BG)
        self._style()
        self._build()
        self.refresh_habits()

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure(".", background=BG, foreground=TEXT,
                    fieldbackground=BG3, bordercolor=BORDER,
                    troughcolor=BG2, font=("Segoe UI", 10))

        s.configure("Treeview", background=BG2, foreground=TEXT,
                    fieldbackground=BG2, rowheight=32,
                    bordercolor=BORDER, relief="flat")
        s.configure("Treeview.Heading", background=BG3, foreground=ACCENT2,
                    font=("Segoe UI", 9, "bold"), relief="flat")
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "#fff")])

        s.configure("TEntry", padding=6, relief="flat",
                    fieldbackground=BG3, foreground=TEXT,
                    insertcolor=ACCENT2, bordercolor=BORDER)
        s.map("TEntry", bordercolor=[("focus", ACCENT)])

        s.configure("TCombobox", padding=6, relief="flat",
                    fieldbackground=BG3, foreground=TEXT,
                    selectbackground=ACCENT, arrowcolor=ACCENT2)

        s.configure("TScrollbar", background=BG3, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TEXT_DIM, relief="flat")

        s.configure("TLabel", background=BG, foreground=TEXT)

    def _build(self):
        hdr = tk.Frame(self, bg=BG2, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Habit Tracker", bg=BG2,
                 fg=ACCENT2, font=("Segoe UI", 16, "bold")).pack(side="left", padx=20)
        self.status_var = tk.StringVar(value="")
        tk.Label(hdr, textvariable=self.status_var, bg=BG2,
                 fg=TEXT_DIM, font=("Segoe UI", 9)).pack(side="right", padx=20)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        top_bar = tk.Frame(left, bg=BG)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        tk.Label(top_bar, text="Категорія:", bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 9)).pack(side="left")
        self.filter_var = tk.StringVar()
        fe = ttk.Entry(top_bar, textvariable=self.filter_var, width=14)
        fe.pack(side="left", padx=(4, 10))
        fe.bind("<Return>", lambda e: self.refresh_habits())

        self._btn(top_bar, "Оновити",    self.refresh_habits,   ACCENT).pack(side="left", padx=2)
        self._btn(top_bar, "Лідерборд",  self.show_leaderboard, WARNING).pack(side="left", padx=2)
        self._btn(top_bar, "Check-in",   self.do_checkin,       SUCCESS).pack(side="right", padx=2)
        self._btn(top_bar, "Видалити",   self.do_delete,        DANGER).pack(side="right", padx=2)
        self._btn(top_bar, "Редагувати", self.open_edit,        BG3).pack(side="right", padx=2)

        cols = ("id", "name", "category", "frequency", "streak", "last_check_in")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        headers = {
            "id":            ("ID",               40),
            "name":          ("Назва",            200),
            "category":      ("Категорія",        100),
            "frequency":     ("Частота",           80),
            "streak":        ("Streak",            70),
            "last_check_in": ("Останній check-in", 130),
        }
        for c, (h, w) in headers.items():
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center" if c != "name" else "w")
        self.tree.grid(row=1, column=0, sticky="nsew")

        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.grid(row=1, column=1, sticky="ns")

        right = tk.Frame(body, bg=BG2, width=240)
        right.grid(row=0, column=1, sticky="nsew")
        right.pack_propagate(False)
        right.columnconfigure(0, weight=1)

        tk.Label(right, text="Нова звичка", bg=BG2, fg=ACCENT2,
                 font=("Segoe UI", 12, "bold")).pack(pady=(18, 12), padx=16, anchor="w")

        def lbl(text):
            tk.Label(right, text=text, bg=BG2, fg=TEXT_DIM,
                     font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(6, 2))

        lbl("Назва *")
        self.new_name = ttk.Entry(right)
        self.new_name.pack(fill="x", padx=16)

        lbl("Категорія")
        self.new_cat = ttk.Entry(right)
        self.new_cat.pack(fill="x", padx=16)

        lbl("Частота *")
        self.new_freq = ttk.Combobox(right, values=["daily", "weekly"], state="readonly")
        self.new_freq.set("daily")
        self.new_freq.pack(fill="x", padx=16)

        self._btn(right, "Додати звичку", self.do_create, ACCENT,
                  full=True).pack(fill="x", padx=16, pady=(20, 4))

        log_frame = tk.Frame(self, bg=BG2)
        log_frame.pack(fill="x", padx=16, pady=(0, 12))
        tk.Label(log_frame, text="Лог", bg=BG2, fg=TEXT_DIM,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=8, pady=(4, 0))
        self.log = tk.Text(log_frame, height=4, bg=BG2, fg=TEXT_DIM,
                           font=("Consolas", 9), relief="flat", state="disabled",
                           insertbackground=ACCENT2, wrap="word")
        self.log.pack(fill="x", padx=8, pady=(0, 6))

    def _btn(self, parent, text, cmd, color, full=False):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=color, fg="#fff" if color != BG3 else TEXT,
                      activebackground=ACCENT2, activeforeground="#fff",
                      font=("Segoe UI", 9, "bold"), relief="flat",
                      bd=0, padx=10, pady=6, cursor="hand2")
        if full:
            b.configure(pady=10)
        return b

    def log_msg(self, msg, color=TEXT_DIM):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.status_var.set(msg)

    def refresh_habits(self):
        def task():
            try:
                cat = self.filter_var.get().strip() or None
                r = api_get("", {"category": cat} if cat else None)
                habits = r.json()
                self.after(0, lambda: self._fill_table(habits))
                self.after(0, lambda: self.log_msg(
                    f"Завантажено {len(habits)} звичок  [{r.status_code}]", SUCCESS))
            except Exception as e:
                self.after(0, lambda: self.log_msg(f"Помилка: {e}", DANGER))
        threading.Thread(target=task, daemon=True).start()

    def _fill_table(self, habits):
        self.tree.delete(*self.tree.get_children())
        for h in habits:
            self.tree.insert("", "end", iid=str(h["id"]), values=(
                h["id"], h["name"], h.get("category", ""),
                h.get("frequency", ""), h.get("streak", 0),
                h.get("last_check_in") or "—"
            ))

    def do_create(self):
        name = self.new_name.get().strip()
        cat  = self.new_cat.get().strip() or "general"
        freq = self.new_freq.get()
        if not name:
            messagebox.showwarning("Увага", "Введіть назву звички!")
            return
        def task():
            try:
                r = api_post("", {"name": name, "category": cat, "frequency": freq})
                if r.status_code == 201:
                    self.after(0, lambda: [
                        self.new_name.delete(0, "end"),
                        self.new_cat.delete(0, "end"),
                        self.refresh_habits(),
                        self.log_msg(f"Створено: «{name}»  [201]", SUCCESS)
                    ])
                else:
                    self.after(0, lambda: self.log_msg(
                        f"Помилка: {r.json()}  [{r.status_code}]", DANGER))
            except Exception as e:
                self.after(0, lambda: self.log_msg(f"Помилка: {e}", DANGER))
        threading.Thread(target=task, daemon=True).start()

    def do_checkin(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Підказка", "Оберіть звичку в таблиці!")
            return
        hid  = sel[0]
        name = self.tree.item(hid, "values")[1]
        def task():
            try:
                r = api_patch(f"/{hid}/check-in")
                if r.status_code == 200:
                    streak = r.json().get("streak", "?")
                    self.after(0, lambda: [
                        self.refresh_habits(),
                        self.log_msg(f"Check-in: «{name}» — streak {streak}  [200]", SUCCESS)
                    ])
                else:
                    msg = r.json().get("detail", str(r.status_code))
                    self.after(0, lambda: self.log_msg(f"{msg}  [{r.status_code}]", WARNING))
            except Exception as e:
                self.after(0, lambda: self.log_msg(f"Помилка: {e}", DANGER))
        threading.Thread(target=task, daemon=True).start()

    def do_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Підказка", "Оберіть звичку в таблиці!")
            return
        hid  = sel[0]
        name = self.tree.item(hid, "values")[1]
        if not messagebox.askyesno("Підтвердження", f"Видалити «{name}»?"):
            return
        def task():
            try:
                r = api_delete(f"/{hid}")
                self.after(0, lambda: [
                    self.refresh_habits(),
                    self.log_msg(f"Видалено: «{name}»  [{r.status_code}]", DANGER)
                ])
            except Exception as e:
                self.after(0, lambda: self.log_msg(f"Помилка: {e}", DANGER))
        threading.Thread(target=task, daemon=True).start()

    def open_edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Підказка", "Оберіть звичку в таблиці!")
            return
        hid  = sel[0]
        vals = self.tree.item(hid, "values")
        EditDialog(self, hid, vals[1], vals[2], vals[3])

    def show_leaderboard(self):
        def task():
            try:
                r = api_get("/leaderboard", {"limit": 10})
                habits = r.json()
                self.after(0, lambda: LeaderboardDialog(self, habits))
                self.log_msg(f"Лідерборд завантажено  [{r.status_code}]", WARNING)
            except Exception as e:
                self.after(0, lambda: self.log_msg(f"Помилка: {e}", DANGER))
        threading.Thread(target=task, daemon=True).start()


class EditDialog(tk.Toplevel):
    def __init__(self, master, hid, name, category, frequency):
        super().__init__(master)
        self.master = master
        self.hid = hid
        self.title(f"Редагувати звичку #{hid}")
        self.geometry("320x280")
        self.resizable(False, False)
        self.configure(bg=BG2)
        self.grab_set()

        tk.Label(self, text=f"Редагувати: #{hid}", bg=BG2, fg=ACCENT2,
                 font=("Segoe UI", 12, "bold")).pack(pady=(16, 10), padx=20, anchor="w")

        def lbl(t):
            tk.Label(self, text=t, bg=BG2, fg=TEXT_DIM,
                     font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(6, 2))

        lbl("Назва *")
        self.e_name = ttk.Entry(self)
        self.e_name.insert(0, name)
        self.e_name.pack(fill="x", padx=20)

        lbl("Категорія")
        self.e_cat = ttk.Entry(self)
        self.e_cat.insert(0, category)
        self.e_cat.pack(fill="x", padx=20)

        lbl("Частота *")
        self.e_freq = ttk.Combobox(self, values=["daily", "weekly"], state="readonly")
        self.e_freq.set(frequency)
        self.e_freq.pack(fill="x", padx=20)

        tk.Button(self, text="Зберегти", command=self.save,
                  bg=ACCENT, fg="#fff", font=("Segoe UI", 10, "bold"),
                  relief="flat", pady=8, cursor="hand2").pack(
                  fill="x", padx=20, pady=(20, 4))

    def save(self):
        n = self.e_name.get().strip()
        c = self.e_cat.get().strip() or "general"
        f = self.e_freq.get()
        if not n:
            messagebox.showwarning("Увага", "Назва не може бути порожньою!", parent=self)
            return
        def task():
            try:
                r = requests.put(f"{BASE_URL}/{self.hid}",
                                 json={"name": n, "category": c, "frequency": f}, timeout=5)
                self.after(0, lambda: [
                    self.master.refresh_habits(),
                    self.master.log_msg(
                        f"Оновлено #{self.hid}: «{n}»  [{r.status_code}]", SUCCESS),
                    self.destroy()
                ])
            except Exception as e:
                self.after(0, lambda: self.master.log_msg(f"Помилка: {e}", DANGER))
        threading.Thread(target=task, daemon=True).start()


class LeaderboardDialog(tk.Toplevel):
    def __init__(self, master, habits):
        super().__init__(master)
        self.title("Лідерборд")
        self.geometry("480x360")
        self.configure(bg=BG)
        self.grab_set()

        tk.Label(self, text="Топ звичок за Streak", bg=BG, fg=WARNING,
                 font=("Segoe UI", 14, "bold")).pack(pady=(16, 10))

        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        cols = ("rank", "name", "category", "frequency", "streak")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c, h, w in [("rank", "#", 40), ("name", "Назва", 180),
                         ("category", "Категорія", 100),
                         ("frequency", "Частота", 80), ("streak", "Streak", 70)]:
            tree.heading(c, text=h)
            tree.column(c, width=w, anchor="center" if c != "name" else "w")

        for i, h in enumerate(habits, 1):
            tree.insert("", "end", values=(
                i, h["name"], h.get("category", ""),
                h.get("frequency", ""), h.get("streak", 0)
            ))

        tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")


if __name__ == "__main__":
    app = App()
    app.mainloop()