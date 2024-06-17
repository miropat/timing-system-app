import customtkinter as ctk
import serial
import threading
import sqlite3
from datetime import datetime
from database import setup_database
import winsound

class ArduinoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Arduino Data Viewer")

        self.setup_gui()
        setup_database()
        self.root.bind("<space>", self.ready_to_start)

        try:
            self.ser = serial.Serial('COM5', 9600, timeout=1)
            self.connection_status.set("Connected to Arduino")
        except serial.SerialException as e:
            print(f"Error: {e}")
            self.label.configure(text=f"Error: {e}")
            self.ser = None
            self.ready_button.configure(state=ctk.DISABLED)
            return

        self.data = []
        self.thread = threading.Thread(target=self.read_from_serial)
        self.thread.daemon = True
        self.thread.start()

    def setup_gui(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.frame = ctk.CTkFrame(self.root)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.label = ctk.CTkLabel(self.frame, text="Waiting for data...")
        self.label.pack(pady=20)

        self.connection_status = ctk.StringVar()
        self.connection_status.set("Disconnected")
        self.connection_status_label = ctk.CTkLabel(self.frame, textvariable=self.connection_status)
        self.connection_status_label.pack(pady=10)

        self.ready_button = ctk.CTkButton(self.frame, text="Ready to Start", command=self.send_ready_signal)
        self.ready_button.pack(pady=10)

        self.reset_button = ctk.CTkButton(self.frame, text="Reset", command=self.send_reset_signal)
        self.reset_button.pack(pady=10)

        self.save_button = ctk.CTkButton(self.frame, text="Save to Database", command=self.save_to_db)
        self.save_button.pack(pady=10)

        self.show_button = ctk.CTkButton(self.frame, text="Show Saved Timings", command=self.show_data)
        self.show_button.pack(pady=10)

        self.data_viewer = ctk.CTkTextbox(self.frame, height=10, width=50)
        self.data_viewer.pack(pady=10)

        self.scrollbar = ctk.CTkScrollbar(self.frame, command=self.data_viewer.yview)
        self.scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)
        self.data_viewer.configure(yscrollcommand=self.scrollbar.set)

    def ready_to_start(self, event=None):
        self.send_ready_signal()

    def send_ready_signal(self):
        if self.ser:
            self.ser.write(b'R')
            print("Sent ready signal to Arduino")
        else:
            print("Error: Serial connection not established")
            self.label.configure(text="Error: Serial connection not established")

    def send_reset_signal(self):
        if self.ser:
            self.ser.write(b'X')
            print("Sent reset signal to Arduino")
        else:
            print("Error: Serial connection not established")
            self.label.configure(text="Error: Serial connection not established")

    def read_from_serial(self):
        while True:
            if self.ser and self.ser.is_open:
                try:
                    line = self.ser.readline().decode('utf-8').rstrip()
                    if line:
                        print(f"Received line: {line}")
                        timestamp = datetime.now().strftime('%Y-%m-%d ')
                        self.root.after(0, self.update_gui, line, timestamp)
                        if "sec" in line:
                            try:
                                duration_str = line.split(" ")[0]
                                duration = float(duration_str)
                                self.data.append((duration, timestamp))
                                print(f"Appended to data: Duration={duration}, Timestamp={timestamp}")
                                self.play_beep()
                            except ValueError:
                                print(f"Invalid duration value: {duration_str}")
                        elif "Gate passed" in line:
                            self.play_beep()
                except Exception as e:
                    print(f"Error reading from serial: {e}")
            else:
                print("Serial port is not open or no data available")
                break

    def update_gui(self, display_line, timestamp):
        self.label.configure(text=display_line)
        log_entry = f"{timestamp} - {display_line}"
        self.data_viewer.insert(ctk.END, log_entry + "\n")
        self.data_viewer.see(ctk.END)

    def save_to_db(self):
        if self.data:
            conn = sqlite3.connect('timing_data.db')
            c = conn.cursor()
            c.execute('CREATE TABLE IF NOT EXISTS timings (id INTEGER PRIMARY KEY, duration REAL, timestamp TEXT)')
            for duration, timestamp in self.data:
                c.execute('INSERT INTO timings (duration, timestamp) VALUES (?, ?)', (duration, timestamp))
                print(f"Inserted to DB: Duration={duration}, Timestamp={timestamp}")
            conn.commit()
            conn.close()
            self.data = []
            self.label.configure(text="Data saved to database")

    def fetch_data(self):
        conn = sqlite3.connect('timing_data.db')
        c = conn.cursor()
        c.execute('SELECT * FROM timings')
        rows = c.fetchall()
        conn.close()
        print(f"Fetched data: {rows}")
        return rows

    def show_data(self):
        rows = self.fetch_data()
        if rows:
            display_text = "\n".join([f"ID: {row[0]}, Duration: {row[1]} seconds, Timestamp: {row[2]}" for row in rows])
        else:
            display_text = "No data found"
        self.label.configure(text=display_text)
        self.data_viewer.delete('1.0', ctk.END)
        self.data_viewer.insert(ctk.END, display_text + "\n")

    def play_beep(self):
        winsound.Beep(1000, 200)  # Beep at 1000 Hz for 200 ms

if __name__ == "__main__":
    root = ctk.CTk()
    app = ArduinoApp(root)
    root.mainloop()
