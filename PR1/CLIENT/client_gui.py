import customtkinter as ctk
from tkinter import filedialog, messagebox
import client_logic

class FileClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TCP File Sender")
        self.geometry("800x600") 
        self.resizable(False, False)

        self.save_path = ""
        self.saved_ip = ""
        self.saved_port = 0

        FONT_LABEL = ("Arial", 20, "bold")
        FONT_ENTRY = ("Arial", 14, "bold")
        FONT_STATUS = ("Arial", 30, "bold", "italic")

        # --- Server IP ---
        self.ip_label = ctk.CTkLabel(self, text="Enter server IP:", font=FONT_LABEL)
        self.ip_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        
        self.server_ip = ctk.CTkEntry(self, placeholder_text="127.0.0.1", font=FONT_ENTRY)
        self.server_ip.grid(row=0, column=1, padx=(0, 20), pady=10, sticky="we")

        # --- Server Port ---
        self.port_label = ctk.CTkLabel(self, text="Enter server Port:", font=FONT_LABEL)
        self.port_label.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="w")
        
        self.server_port = ctk.CTkEntry(self, placeholder_text="7777", font=FONT_ENTRY)
        self.server_port.grid(row=1, column=1, padx=(0, 20), pady=10, sticky="we")

        # --- Connect Button ---
        self.connect_button = ctk.CTkButton(
            self, text="Connect", command=self.test_connection,
            fg_color="#28a745", hover_color="#218838", font=FONT_LABEL
        )
        self.connect_button.grid(row=2, column=0, columnspan=2, pady=(20, 40))

        # --- Folder selection ---
        self.folder_label = ctk.CTkLabel(self, text="Select folder to save files:", font=FONT_LABEL)
        self.folder_label.grid(row=3, column=0, padx=(20, 10), pady=10, sticky="w")
        
        self.choose_folder_button = ctk.CTkButton(self, text="Select folder", command=self.choose_folder, font=FONT_LABEL)
        self.choose_folder_button.grid(row=3, column=1, padx=(0, 20), pady=10, sticky="w")

        self.dir_status_label = ctk.CTkLabel(self, text="You chose: None", font=FONT_LABEL, text_color="gray")
        self.dir_status_label.grid(row=4, column=0, columnspan=2, padx=(20, 20), pady=(0, 20), sticky="w")

        # --- File Entry ---
        self.filename_label = ctk.CTkLabel(self, text="Enter filenames (comma-separated):", font=FONT_LABEL)
        self.filename_label.grid(row=5, column=0, padx=(20, 10), pady=10, sticky="w")
        
        self.filename_entry = ctk.CTkEntry(self, placeholder_text="test.txt, photo.png", font=FONT_ENTRY)
        self.filename_entry.grid(row=5, column=1, padx=(0, 20), pady=10, sticky="we")

        # --- Submit Button ---
        self.submit_button = ctk.CTkButton(
            self, text="Download Files", command=self.download_files,
            fg_color="#007bff", hover_color="#0056b3", font=FONT_LABEL
        )
        self.submit_button.grid(row=6, column=0, columnspan=2, pady=(20, 40))

        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self, text="Status: Waiting...", font=FONT_STATUS)
        self.status_label.grid(row=7, column=0, columnspan=2, pady=(10, 20))

        # --- ІДЕАЛЬНЕ ВИРІВНЮВАННЯ ВЛІВО ---
        self.grid_columnconfigure(0, weight=0) # Колонка рівно по ширині тексту
        self.grid_columnconfigure(1, weight=1) # Entry розтягуються на весь вільний простір

    # --- Methods ---
    def test_connection(self):
        ip = self.server_ip.get().strip()
        port = self.server_port.get().strip()

        conn = client_logic.connect_server(ip, port)
        if conn:
            self.saved_ip = ip
            self.saved_port = int(port)
            messagebox.showinfo("Success", f"Connected to server {ip}:{port}")
            conn.close()
            self.status_label.configure(text="Status: Connection OK")
        elif client_logic.ip_validate(ip):
            messagebox.showinfo("Error",f"U entered wrong PORT")
            self.status_label.configure(text="Status: Error, wrong PORT")
        elif client_logic.port_validate(port):
            messagebox.showinfo("Error",f"U entered wrong IP address")
            self.status_label.configure(text="Status: Error, wrong IP address")
        else:
            messagebox.showinfo("Error",f"Entered wrong connection parameters")
            self.status_label.configure(text="Status: wrong connection parameters")

    def choose_folder(self):
        self.save_path = filedialog.askdirectory()
        if self.save_path:
            self.dir_status_label.configure(text=f"You chose: {self.save_path}")

    def download_files(self):
        if not self.saved_ip or not self.saved_port:
            messagebox.showerror("Error", "Press 'Connect' first!")
            return
        if not self.save_path:
            messagebox.showerror("Error", "Choose a folder first!")
            return

        raw_filenames = self.filename_entry.get()
        if not raw_filenames.strip():
            messagebox.showerror("Error", "Enter at least one file name!")
            return

        filenames = [f.strip() for f in raw_filenames.split(",") if f.strip()]
        errors = []
        downloaded = []

        for filename in filenames:
            self.status_label.configure(text=f"Downloading: {filename}...")
            self.update()

            conn = client_logic.connect_server(self.saved_ip, self.saved_port)
            if not conn:
                errors.append(f"[{filename}]: Cannot connect")
                continue

            try:
                client_logic.request_file(conn, filename, self.save_path)
                downloaded.append(filename)
            except Exception as e:
                errors.append(f"[{filename}]: {e}")
            finally:
                conn.close()

        if downloaded:
            self.status_label.configure(text=f"Completed. {len(downloaded)} file(s) downloaded.")
            messagebox.showinfo("Success", f"Downloaded files:\n{', '.join(downloaded)}")
        if errors:
            self.status_label.configure(text="Completed with errors")
            messagebox.showerror("Errors", "\n".join(errors))
