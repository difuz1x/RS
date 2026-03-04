import tkinter as tk
from tkinter import ttk, messagebox
import grpc
import random


from grpc_client import GRPCClient

class CurrencyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NBU gRPC Converter (Thick Client)")
        self.root.geometry("400x400")
        
        
        self.api = GRPCClient() 
        self.rates_dict = {}   

        self.setup_ui()
        self.register_client()

    def setup_ui(self):
        
        self.status_label = tk.Label(self.root, text="Status: Connecting...", fg="orange", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=10)

       
        tk.Label(self.root, text="Enter amount:").pack()
        self.amount_entry = tk.Entry(self.root, width=15, font=("Arial", 12))
        self.amount_entry.pack(pady=5)
        self.amount_entry.insert(0, "100")


        tk.Label(self.root, text="From currency:").pack()
        self.combo_from = ttk.Combobox(self.root, width=20, state="readonly")
        self.combo_from.pack(pady=5)

   
        tk.Label(self.root, text="To currency:").pack()
        self.combo_to = ttk.Combobox(self.root, width=20, state="readonly")
        self.combo_to.pack(pady=5)

      
        self.calc_btn = tk.Button(self.root, text="Convert", command=self.calculate_total, bg="lightgreen")
        self.calc_btn.pack(pady=15)

        
        self.result_label = tk.Label(self.root, text="Result: 0.00", font=("Arial", 14, "bold"), fg="blue")
        self.result_label.pack(pady=10)

      
        self.refresh_btn = tk.Button(self.root, text="Update NBU Rates", command=self.load_rates)
        self.refresh_btn.pack(pady=5)

    def register_client(self):
        try:
            while True:
                self.client_id = random.randint(0,1000)
                response = self.api.connect(self.client_id)
                if response.isRegistered:
                    self.status_label.config(text=f"Connected (ID: {response.clientID})", fg="green")
                    self.load_rates()
                break
        except grpc.RpcError:
            self.status_label.config(text="Server unavailable!", fg="red")

    def load_rates(self):
        try:
            rates_list = self.api.get_rates()
            
            self.rates_dict = {"UAH": 1.0}
            
            for item in rates_list:
                self.rates_dict[item.fromCurrency] = item.trade_rate
            
            currencies = list(self.rates_dict.keys())
            self.combo_from['values'] = currencies
            self.combo_to['values'] = currencies
            
            if currencies:
                if "USD" in currencies:
                    self.combo_from.current(currencies.index("USD"))
                else:
                    self.combo_from.current(0)
                self.combo_to.current(currencies.index("UAH"))
                
        except grpc.RpcError:
            messagebox.showerror("Error", "Failed to get exchange rates from the server.")

    def calculate_total(self):
        try:
            amount = float(self.amount_entry.get())
            curr_from = self.combo_from.get()
            curr_to = self.combo_to.get()
            
            if not curr_from or not curr_to:
                messagebox.showwarning("Warning", "Please select currencies to convert!")
                return

            rate_from = self.rates_dict[curr_from]
            rate_to = self.rates_dict[curr_to]
            
            total = amount * (rate_from / rate_to)
            
            self.result_label.config(text=f"Result: {total:.2f} {curr_to}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number!")

    def on_closing(self):
        try:
            self.api.disconnect(self.client_id)
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()