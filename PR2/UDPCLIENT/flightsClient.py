# flightsClient.py — точка входу програми клієнта

import tkinter as tk
from flightsClientGUI import FlightBoardApp

if __name__ == '__main__':
    root = tk.Tk()
    app  = FlightBoardApp(root)
    root.mainloop()

"""
**Схема залежностей:**
```
flightsClient.py
    └── flightsClientGUI.py
            └── flightsClientLogic.py
"""