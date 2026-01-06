import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Add the Python directory to sys.path to import AmazingHand_Demo
# This allows us to use the AmazingHand class we just refactored
current_dir = os.path.dirname(os.path.abspath(__file__))
python_dir = os.path.join(current_dir, '..', 'Python')
sys.path.append(python_dir)

try:
    from AmazingHand_Demo_Optimized import AmazingHand
except ImportError as e:
    print(f"Error importing AmazingHand: {e}")
    AmazingHand = None

class HandControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AmazingHand Control Panel")
        self.hand = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # Port
        ttk.Label(config_frame, text="Port:").grid(row=0, column=0, padx=5)
        self.port_var = tk.StringVar(value="COM3")
        ttk.Entry(config_frame, textvariable=self.port_var, width=10).grid(row=0, column=1, padx=5)
        
        # Baudrate
        ttk.Label(config_frame, text="Baudrate:").grid(row=0, column=2, padx=5)
        self.baud_var = tk.IntVar(value=1000000)
        ttk.Entry(config_frame, textvariable=self.baud_var, width=10).grid(row=0, column=3, padx=5)
        
        # Side
        ttk.Label(config_frame, text="Side:").grid(row=0, column=4, padx=5)
        self.side_var = tk.IntVar(value=1) # 1=Right, 2=Left
        ttk.Radiobutton(config_frame, text="Right", variable=self.side_var, value=1).grid(row=0, column=5)
        ttk.Radiobutton(config_frame, text="Left", variable=self.side_var, value=2).grid(row=0, column=6)
        
        # Connect Button
        self.connect_btn = ttk.Button(config_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=7, padx=10)
        
        # Gestures Frame
        self.gesture_frame = ttk.LabelFrame(self.root, text="Gestures", padding=10)
        self.gesture_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        gestures = [
            ("Open Hand", "OpenHand"),
            ("Close Hand", "CloseHand"),
            ("Open Progressive", "OpenHand_Progressive"),
            ("Spread Hand", "SpreadHand"),
            ("Clench Hand", "ClenchHand"),
            ("Index Pointing", "Index_Pointing"),
            ("No No No", "Nonono"),
            ("Perfect", "Perfect"),
            ("Victory", "Victory"),
            ("Scissors", "Scissors"),
            ("Pinched", "Pinched"),
            ("Fuck", "Fuck"),
        ]
        
        row = 0
        col = 0
        for text, method_name in gestures:
            btn = ttk.Button(self.gesture_frame, text=text, 
                             command=lambda m=method_name: self.perform_gesture(m))
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            # Grid layout logic (3 columns)
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        # Status Bar
        self.status_var = tk.StringVar(value="Disconnected")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", side="bottom")

    def toggle_connection(self):
        if self.hand:
            # Disconnect
            self.hand = None
            self.connect_btn.config(text="Connect")
            self.status_var.set("Disconnected")
            # Note: Scs0009PyController doesn't have an explicit close/disconnect method, 
            # so we just drop the reference.
        else:
            # Connect
            try:
                port = self.port_var.get()
                baud = self.baud_var.get()
                side = self.side_var.get()
                
                if AmazingHand is None:
                    messagebox.showerror("Error", "AmazingHand library not found! Check Python path.")
                    return

                self.status_var.set(f"Connecting to {port}...")
                self.root.update()
                
                # Instantiate the controller
                self.hand = AmazingHand(port=port, baudrate=baud, side=side)
                
                self.connect_btn.config(text="Disconnect")
                self.status_var.set(f"Connected to {port} (Side: {'Right' if side==1 else 'Left'})")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Could not connect:\n{str(e)}")
                self.status_var.set("Connection Failed")
                self.hand = None

    def perform_gesture(self, method_name):
        if not self.hand:
            messagebox.showwarning("Not Connected", "Please connect to the hand first.")
            return
            
        try:
            method = getattr(self.hand, method_name)
            self.status_var.set(f"Performing: {method_name}...")
            self.root.update()
            
            # Execute the gesture
            method()
            
            self.status_var.set(f"Done: {method_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to perform gesture: {e}")
            self.status_var.set("Error performing gesture")

if __name__ == "__main__":
    root = tk.Tk()
    # Set window size and position
    root.geometry("500x400")
    app = HandControlApp(root)
    root.mainloop()
