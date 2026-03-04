# flightsClientGUI.py

import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from flightsClientLogic import (
    ip_validate, port_validate,
    create_udp_socket, register_client, unregister_client,
    receive_update, format_timestamp,
    discover_server,
    SERVER_PORT_DEFAULT,
)

STATUS_COLORS = {
    'BOARDING':  '#27ae60',
    'ONTIME':    '#2980b9',
    'COMPLETED': '#7f8c8d',
    'DELAYED':   '#e67e22',
    'CANCELLED': '#c0392b',
}


class FlightBoardApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.sock = None
        self.server_addr = None
        self.running = False

        root.title('✈ Табло аеропорту')
        root.geometry('560x600')
        root.resizable(False, False)
        root.configure(bg='#1a1a2e')

        self._build_ui()
        root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _build_ui(self):
        tk.Label(self.root, text='✈  FLIGHT STATUS BOARD',
                 bg='#1a1a2e', fg='#e0e0e0',
                 font=('Consolas', 16, 'bold')).pack(pady=(14, 4))

        self.status_lbl = tk.Label(
            self.root, text='● Відключено',
            bg='#1a1a2e', fg='#e74c3c', font=('Consolas', 10))
        self.status_lbl.pack()

        # ── Поля вводу IP / порту ──
        input_frame = tk.Frame(self.root, bg='#1a1a2e')
        input_frame.pack(pady=8)

        tk.Label(input_frame, text='IP сервера:',
                 bg='#1a1a2e', fg='#bdc3c7',
                 font=('Consolas', 10)).grid(row=0, column=0, padx=4)
        self.ip_entry = tk.Entry(input_frame, width=16,
                                 font=('Consolas', 11),
                                 bg='#16213e', fg='white',
                                 insertbackground='white')
        self.ip_entry.insert(0, '127.0.0.1')
        self.ip_entry.grid(row=0, column=1, padx=4)

        tk.Label(input_frame, text='Порт:',
                 bg='#1a1a2e', fg='#bdc3c7',
                 font=('Consolas', 10)).grid(row=0, column=2, padx=4)
        self.port_entry = tk.Entry(input_frame, width=7,
                                   font=('Consolas', 11),
                                   bg='#16213e', fg='white',
                                   insertbackground='white')
        self.port_entry.insert(0, str(SERVER_PORT_DEFAULT))
        self.port_entry.grid(row=0, column=3, padx=4)

        # ── Кнопка автопошуку ── НОВА
        self.discover_btn = tk.Button(
            input_frame, text='🔍 Знайти',
            command=self._on_discover,
            bg='#8e44ad', fg='white',
            font=('Consolas', 10, 'bold'), width=9, relief='flat')
        self.discover_btn.grid(row=0, column=4, padx=6)

        # Підказка під полями
        self.hint_lbl = tk.Label(
            self.root, text='',
            bg='#1a1a2e', fg='#95a5a6', font=('Consolas', 9))
        self.hint_lbl.pack()

        # ── Таблиця рейсів ──
        cols = ('flight', 'status', 'updated')
        self.tree = ttk.Treeview(self.root, columns=cols,
                                 show='headings', height=11)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview',
                        background='#16213e', foreground='white',
                        fieldbackground='#16213e', rowheight=28,
                        font=('Consolas', 11))
        style.configure('Treeview.Heading',
                        background='#0f3460', foreground='white',
                        font=('Consolas', 11, 'bold'))

        self.tree.heading('flight',  text='Рейс')
        self.tree.heading('status',  text='Статус')
        self.tree.heading('updated', text='Оновлено')
        self.tree.column('flight',  width=110, anchor='center')
        self.tree.column('status',  width=160, anchor='center')
        self.tree.column('updated', width=130, anchor='center')
        self.tree.pack(padx=20, pady=10, fill='x')

        for status, color in STATUS_COLORS.items():
            self.tree.tag_configure(status, foreground=color)

        # ── Кнопки підключення ──
        btn_frame = tk.Frame(self.root, bg='#1a1a2e')
        btn_frame.pack(pady=8)

        self.connect_btn = tk.Button(
            btn_frame, text='Підключитись',
            command=self._on_connect,
            bg='#27ae60', fg='white',
            font=('Consolas', 11, 'bold'), width=16, relief='flat')
        self.connect_btn.grid(row=0, column=0, padx=6)

        self.disconnect_btn = tk.Button(
            btn_frame, text='Відключитись',
            command=self._on_disconnect,
            bg='#c0392b', fg='white',
            font=('Consolas', 11, 'bold'), width=16,
            relief='flat', state='disabled')
        self.disconnect_btn.grid(row=0, column=1, padx=6)

    # ── Автопошук сервера ────────────────────────────────────────────────────

    def _on_discover(self):
        """Запускає пошук в окремому потоці щоб не заморозити GUI."""
        self.hint_lbl.config(text='🔍 Шукаю сервер у мережі (до 5 сек)...',
                             fg='#f39c12')
        self.discover_btn.config(state='disabled')

        def _search():
            result = discover_server(timeout=5.0)
            self.root.after(0, self._on_discover_result, result)

        threading.Thread(target=_search, daemon=True).start()

    def _on_discover_result(self, result):
        self.discover_btn.config(state='normal')
        if result:
            ip, port = result
            # Автоматично заповнюємо поля
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, ip)
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, str(port))
            self.hint_lbl.config(
                text=f' Сервер знайдено: {ip}:{port}', fg='#2ecc71')
        else:
            self.hint_lbl.config(
                text=' Сервер не знайдено. Введіть IP вручну.', fg='#e74c3c')

    # ── Підключення / відключення ────────────────────────────────────────────

    def _on_connect(self):
        ip   = ip_validate(self.ip_entry.get())
        port = port_validate(self.port_entry.get())

        if ip is None:
            messagebox.showerror('Помилка', 'Некоректна IP-адреса.')
            return
        if port is None:
            messagebox.showerror('Помилка', 'Порт має бути числом від 1024 до 65535.')
            return

        self.server_addr = (ip, port)
        self.sock = create_udp_socket(timeout=1.0)

        if not register_client(self.sock, self.server_addr):
            messagebox.showerror('Помилка', 'Не вдалося надіслати запит реєстрації.')
            self.sock.close()
            self.sock = None
            return

        self.running = True
        self._set_connected(True)
        threading.Thread(target=self._receive_loop, daemon=True).start()

    def _on_disconnect(self):
        self.running = False
        if self.sock:
            unregister_client(self.sock, self.server_addr)
            self.sock.close()
            self.sock = None
        self._set_connected(False)

    # ── Фоновий потік прийому ────────────────────────────────────────────────

    def _receive_loop(self):
        while self.running:
            try:
                msg = receive_update(self.sock)
                if msg and msg.get('command') == 'FLIGHT_UPDATE':
                    self.root.after(
                        0, self._update_table,
                        msg['flights'],
                        format_timestamp(msg.get('timestamp', ''))
                    )
            except socket.timeout:
                continue
            except OSError:
                self.root.after(0, self._on_server_lost)
                break

    # ── Оновлення UI ─────────────────────────────────────────────────────────

    def _update_table(self, flights: dict, time_str: str):
        self.tree.delete(*self.tree.get_children())
        for race, status in flights.items():
            tag = status if status in STATUS_COLORS else ''
            self.tree.insert('', 'end',
                             values=(race, status, time_str), tags=(tag,))

    def _set_connected(self, connected: bool):
        if connected:
            self.status_lbl.config(text='● Підключено', fg='#2ecc71')
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
        else:
            self.status_lbl.config(text='● Відключено', fg='#e74c3c')
            self.connect_btn.config(state='normal')
            self.disconnect_btn.config(state='disabled')
            self.tree.delete(*self.tree.get_children())

    def _on_server_lost(self):
        self._set_connected(False)
        messagebox.showwarning('З\'єднання',
                               'Сервер недоступний.\nСпробуйте підключитись знову.')

    def _on_close(self):
        self._on_disconnect()
        self.root.destroy()


"""
**Як тепер виглядає повна схема роботи:**
```
СЕРВЕР запускається
  │
  ├─ Потік 1: слухає CLIENT_REGISTER / CLIENT_DISCONNECT
  ├─ Потік 2: кожну сек розсилає FLIGHT_UPDATE зареєстрованим
  └─ Потік 3: кожні 2 сек broadcast SERVER_ANNOUNCE → 255.255.255.255:9998
                    {"command":"SERVER_ANNOUNCE","ip":"192.168.1.5","port":9999}

КЛІЄНТ відкривається
  │
  ├─ [🔍 Знайти] → слухає порт 9998 → отримує SERVER_ANNOUNCE
  │                → автоматично заповнює поля IP і порт
  │
  └─ [Підключитись] → надсилає CLIENT_REGISTER → потрапляє до розсилки

"""