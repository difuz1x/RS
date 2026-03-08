import tkinter as tk
from tkinter import ttk, messagebox
import grpc
import random

from grpc_client import GRPCClient

BG       = "#1e1e2e"
SURFACE  = "#2a2a3e"
ACCENT   = "#7c6af7"
ACCENT2  = "#50fa7b"
DANGER   = "#ff5555"
WARNING  = "#f1fa8c"
TEXT     = "#cdd6f4"
SUBTEXT  = "#6c7086"
ENTRY_BG = "#313244"
FONT     = ("Courier New", 10)
FONT_B   = ("Courier New", 10, "bold")
FONT_H   = ("Courier New", 13, "bold")

def styled_btn(parent, text, cmd, color=ACCENT, fg=BG, **kw):
    return tk.Button(parent, text=text, command=cmd,
                     bg=color, fg=fg, font=FONT_B,
                     relief="flat", padx=8, pady=4,
                     activebackground=color, cursor="hand2", **kw)

def styled_entry(parent, show=None, width=22):
    return tk.Entry(parent, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                    font=FONT, relief="flat", width=width,
                    highlightthickness=1, highlightcolor=ACCENT,
                    highlightbackground=SURFACE, show=show)

def styled_label(parent, text, bold=False, color=TEXT, size=10):
    return tk.Label(parent, text=text,
                    bg=BG if parent.cget("bg") == BG else SURFACE,
                    fg=color, font=("Courier New", size, "bold" if bold else "normal"))

class CurrencyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NBU gRPC Converter")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.api        = GRPCClient()
        self.rates_dict = {}
        self.client_id  = None

        self._build_ui()

    # ─── UI BUILD ───────────────────────────────────────────
    def _build_ui(self):
        # Status bar
        self.status_label = tk.Label(self.root, text="● NOT CONNECTED",
                                     bg=BG, fg=SUBTEXT, font=FONT_B, anchor="w")
        self.status_label.pack(fill="x", padx=14, pady=(10, 0))

        tk.Frame(self.root, bg=ACCENT, height=1).pack(fill="x", padx=14, pady=4)

        # Login
        self._section("LOGIN", self._build_login)
        # Converter
        self._section("CONVERTER", self._build_converter)
        # Admin (hidden)
        self.admin_outer = self._section("ADMIN PANEL", self._build_admin, visible=False)

        tk.Frame(self.root, bg=BG, height=8).pack()

    def _section(self, title, builder, visible=True):
        outer = tk.Frame(self.root, bg=BG)
        if visible:
            outer.pack(fill="x", padx=14, pady=4)

        header = tk.Label(outer, text=f"  {title}",
                          bg=SURFACE, fg=ACCENT, font=FONT_B,
                          anchor="w", pady=5)
        header.pack(fill="x")

        inner = tk.Frame(outer, bg=SURFACE, padx=12, pady=10)
        inner.pack(fill="x")
        builder(inner)
        return outer

    def _build_login(self, f):
        for i, (lbl, attr, show) in enumerate([
            ("Username", "username_entry", None),
            ("Password", "password_entry", "●"),
        ]):
            tk.Label(f, text=lbl, bg=SURFACE, fg=SUBTEXT, font=FONT).grid(
                row=i, column=0, sticky="w", pady=3)
            entry = styled_entry(f, show=show)
            entry.grid(row=i, column=1, sticky="w", padx=(8, 0), pady=3)
            setattr(self, attr, entry)

        self.username_entry.insert(0, "user")
        self.password_entry.insert(0, "user123")

        self.login_btn = styled_btn(f, "  LOGIN  ", self.authenticate, color=ACCENT)
        self.login_btn.grid(row=2, column=0, columnspan=2, pady=(10, 0))

    def _build_converter(self, f):
        rows = [("Amount", "amount_entry"), ("From", "combo_from"), ("To", "combo_to")]
        for i, (lbl, attr) in enumerate(rows):
            tk.Label(f, text=lbl, bg=SURFACE, fg=SUBTEXT, font=FONT).grid(
                row=i, column=0, sticky="w", pady=3)
            if "combo" in attr:
                w = ttk.Combobox(f, width=19, state="readonly", font=FONT)
                w.grid(row=i, column=1, padx=(8, 0), pady=3)
            else:
                w = styled_entry(f)
                w.insert(0, "100")
                w.grid(row=i, column=1, padx=(8, 0), pady=3)
            setattr(self, attr, w)

        btn_row = tk.Frame(f, bg=SURFACE)
        btn_row.grid(row=3, column=0, columnspan=2, pady=(10, 4))
        styled_btn(btn_row, "CONVERT",      self.calculate_total, color=ACCENT2).pack(side="left", padx=4)
        styled_btn(btn_row, "UPDATE RATES", self.load_rates,      color=SURFACE, fg=TEXT).pack(side="left", padx=4)

        self.result_label = tk.Label(f, text="Result: —",
                                     bg=SURFACE, fg=ACCENT2,
                                     font=("Courier New", 14, "bold"))
        self.result_label.grid(row=4, column=0, columnspan=2, pady=(6, 0))

    def _build_admin(self, f):
        # Users table
        cols = ("username", "role")
        self.users_tree = ttk.Treeview(f, columns=cols, show="headings", height=5,
                                        selectmode="browse")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=ENTRY_BG, foreground=TEXT,
                         fieldbackground=ENTRY_BG, font=FONT, rowheight=24)
        style.configure("Treeview.Heading", background=SURFACE, foreground=ACCENT, font=FONT_B)
        style.map("Treeview", background=[("selected", ACCENT)])

        for col in cols:
            self.users_tree.heading(col, text=col.upper())
            self.users_tree.column(col, width=130)
        self.users_tree.pack(fill="x", pady=(0, 8))

        # Action buttons row
        btn_row = tk.Frame(f, bg=SURFACE)
        btn_row.pack(fill="x", pady=(0, 10))
        styled_btn(btn_row, "REFRESH",       self.load_users,        color=ACCENT).pack(side="left", padx=(0, 4))
        styled_btn(btn_row, "DELETE",         self.delete_user,       color=DANGER).pack(side="left", padx=4)
        styled_btn(btn_row, "TOGGLE ROLE",    self.toggle_role,       color=WARNING, fg=BG).pack(side="left", padx=4)

        tk.Frame(f, bg=ACCENT, height=1).pack(fill="x", pady=6)

        # Add user form
        tk.Label(f, text="ADD USER", bg=SURFACE, fg=ACCENT, font=FONT_B).pack(anchor="w")
        add_form = tk.Frame(f, bg=SURFACE)
        add_form.pack(fill="x", pady=6)

        for i, (lbl, attr, show) in enumerate([
            ("Username", "new_username", None),
            ("Password", "new_password", "●"),
        ]):
            tk.Label(add_form, text=lbl, bg=SURFACE, fg=SUBTEXT, font=FONT).grid(
                row=i, column=0, sticky="w", pady=2)
            e = styled_entry(add_form, show=show, width=18)
            e.grid(row=i, column=1, padx=(8, 0), pady=2)
            setattr(self, attr, e)

        tk.Label(add_form, text="Role", bg=SURFACE, fg=SUBTEXT, font=FONT).grid(
            row=2, column=0, sticky="w", pady=2)
        self.new_role = ttk.Combobox(add_form, values=["user", "admin"],
                                      width=17, state="readonly", font=FONT)
        self.new_role.set("user")
        self.new_role.grid(row=2, column=1, padx=(8, 0), pady=2)

        styled_btn(add_form, "ADD USER", self.add_user, color=ACCENT2, fg=BG).grid(
            row=3, column=0, columnspan=2, pady=(8, 0))

    # ─── LOGIC ──────────────────────────────────────────────
    def authenticate(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Warning", "Enter username and password!")
            return

        success, error = self.api.login(username, password)
        if not success:
            self.status_label.config(text=f"● AUTH FAILED: {error}", fg=DANGER)
            messagebox.showerror("Login failed", error)
            return

        self.register_client(username)

        if self.api.role == "admin":
            self.admin_outer.pack(fill="x", padx=14, pady=4)
            self.load_users()
        else:
            self.admin_outer.pack_forget()

    def register_client(self, username):
        try:
            for _ in range(5):
                cid = random.randint(1, 1000)
                response = self.api.connect(cid)
                if response.isRegistered:
                    self.client_id = response.clientID
                    role_tag = f"[{self.api.role}]"
                    self.status_label.config(
                        text=f"● {username} {role_tag}  ID:{self.client_id}",
                        fg=ACCENT2
                    )
                    self.load_rates()
                    return
        except grpc.RpcError as e:
            self.status_label.config(text=f"● SERVER UNAVAILABLE: {e.details()}", fg=DANGER)

    def load_rates(self):
        try:
            rates_list = self.api.get_rates()
            self.rates_dict = {"UAH": 1.0}
            for item in rates_list:
                self.rates_dict[item.fromCurrency] = item.trade_rate
            currencies = list(self.rates_dict.keys())
            self.combo_from["values"] = currencies
            self.combo_to["values"]   = currencies
            if currencies:
                self.combo_from.current(currencies.index("USD") if "USD" in currencies else 0)
                self.combo_to.current(currencies.index("UAH"))
        except grpc.RpcError as e:
            messagebox.showerror("Error", f"Failed to get rates: {e.details()}")

    def calculate_total(self):
        try:
            amount    = float(self.amount_entry.get())
            curr_from = self.combo_from.get()
            curr_to   = self.combo_to.get()
            if not curr_from or not curr_to:
                messagebox.showwarning("Warning", "Select currencies!")
                return
            response = self.api.convert_amount(curr_from, curr_to, amount)
            self.result_label.config(text=f"{response.result:.4f} {curr_to}")
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAUTHENTICATED:
                if self.api.refresh_access_token():
                    self.calculate_total()
                else:
                    self.authenticate()
            elif e.code() == grpc.StatusCode.NOT_FOUND:
                messagebox.showerror("Error", f"Unknown currency: {e.details()}")
            else:
                messagebox.showerror("Error", f"Server error: {e.details()}")
        except ValueError:
            messagebox.showerror("Error", "Invalid amount!")

    def load_users(self):
        for row in self.users_tree.get_children():
            self.users_tree.delete(row)
        for u in self.api.get_users():
            tag = "admin" if u["role"] == "admin" else ""
            self.users_tree.insert("", tk.END, values=(u["username"], u["role"]), tags=(tag,))
        self.users_tree.tag_configure("admin", foreground=WARNING)

    def _selected_user(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select a user first!")
            return None
        return self.users_tree.item(sel[0])["values"][0]

    def delete_user(self):
        username = self._selected_user()
        if not username:
            return
        if not messagebox.askyesno("Confirm", f"Delete user '{username}'?"):
            return
        ok, msg = self.api.delete_user(username)
        if ok:
            messagebox.showinfo("Done", msg)
            self.load_users()
        else:
            messagebox.showerror("Error", msg)

    def toggle_role(self):
        username = self._selected_user()
        if not username:
            return
        current = next((u["role"] for u in self.api.get_users() if u["username"] == username), "user")
        new_role = "admin" if current == "user" else "user"
        ok, msg = self.api.change_role(username, new_role)
        if ok:
            messagebox.showinfo("Done", msg)
            self.load_users()
        else:
            messagebox.showerror("Error", msg)

    def add_user(self):
        username = self.new_username.get().strip()
        password = self.new_password.get().strip()
        role     = self.new_role.get()
        if not username or not password:
            messagebox.showwarning("Warning", "Fill in username and password!")
            return
        ok, msg = self.api.add_user(username, password, role)
        if ok:
            messagebox.showinfo("Done", msg)
            self.new_username.delete(0, tk.END)
            self.new_password.delete(0, tk.END)
            self.load_users()
        else:
            messagebox.showerror("Error", msg)

    def on_closing(self):
        try:
            self.api.disconnect(self.client_id)
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app  = CurrencyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()