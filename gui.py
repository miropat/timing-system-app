import tkinter as tk
from tkinter import ttk
import serial
import threading
import sqlite3
from datetime import datetime
from database import setup_database

class ArduinoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino Data Viewer")

        self.setup_gui()
        setup_database()
        self.root.bind("<space>", self.ready_to_start)

        try:
            self.ser = serial.Serial('COM5', 9600, timeout=1)
        except serial.SerialException as e:
            print(f"Error: {e}")
            self.label.config(text=f"Error: {e}")
            return

        self.data = []
        self.durations = []
        self.thread = threading.Thread(target=self.read_from_serial)
        self.thread.daemon = True
        self.thread.start()

    def setup_gui(self):
        self.label = ttk.Label(self.root, text="Waiting for data...")
        self.label.pack(pady=20)
        
        
        self.ready_button = ttk.Button(self.root, text="Ready to Start", command=self.send_ready_signal)
        self.ready_button.pack(pady=10)
        
        self.save_button = ttk.Button(self.root, text="Save to Database", command=self.save_to_db)
        self.save_button.pack(pady=10)
        
        self.show_button = ttk.Button(self.root, text="Show Saved Timings", command=self.show_data)
        self.show_button.pack(pady=10)

        self.data_viewer = tk.Text(self.root, height=10, width=50)
        self.data_viewer.pack(pady=10)
        
        self.scrollbar = tk.Scrollbar(self.root, command=self.data_viewer.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_viewer.config(yscrollcommand=self.scrollbar.set)

    
    def ready_to_start(self, event):
        # Simulate button press event
        self.send_ready_signal()

    def send_ready_signal(self):
        self.ser.write(b'R')  # Send 'R' to indicate ready
        print("Sent ready signal to Arduino")

    def read_from_serial(self):
        while True:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').rstrip()
                if line.startswith("Duration"):
                    duration_str = line.split(":")[1].strip().split(" ")[0]
                    duration = float(duration_str)
                    self.durations.append(duration)
                    display_line = f"{duration} seconds"
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_entry = f"{timestamp} - {line}"
                    self.label.config(text=line)
                    self.data.append(line)
                    self.data_viewer.insert(tk.END, log_entry + "\n")
                    self.data_viewer.see(tk.END)  # Auto-scroll to the end

    def save_to_db(self):
        if self.durations:
            conn = sqlite3.connect('timing_data.db')
            c = conn.cursor()
            c.execute('CREATE TABLE IF NOT EXISTS timings (id INTEGER PRIMARY KEY, duration TEXT, timestamp TEXT)')
            for duration in self.durations:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute('INSERT INTO timings (duration, timestamp) VALUES (?, ?)', (duration, timestamp))
            conn.commit()
            conn.close()
            self.durations = []
            self.label.config(text="Data saved to database")

    def fetch_data(self):
        conn = sqlite3.connect('timing_data.db')
        c = conn.cursor()
        c.execute('SELECT * FROM timings')
        rows = c.fetchall()
        conn.close()
        return rows

    def show_data(self):
        rows = self.fetch_data()
        display_text = "\n".join([f"ID: {row[0]}, Duration: {row[1]}, Timestamp: {row[2]}" for row in rows])
        self.label.config(text=display_text)
        self.data_viewer.delete('1.0', tk.END)
        self.data_viewer.insert(tk.END, display_text + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = ArduinoApp(root)
    root.mainloop()