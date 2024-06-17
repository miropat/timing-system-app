import customtkinter as ctk
import serial
import threading
import sqlite3
from datetime import datetime
from database import setup_database
import winsound
from tkinter import messagebox, simpledialog

class ArduinoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MPerformance timing")


        self.connection_status = ctk.StringVar()  # Initialize connection_status here
        self.setup_gui()

        self.setup_serial()
        setup_database()
        self.fetch_athletes()  # Fetch athletes after setting up the GUI

        self.root.bind("<space>", self.ready_to_start)

        self.data = []
        self.thread = threading.Thread(target=self.read_from_serial)
        self.thread.daemon = True
        self.thread.start()


    def setup_gui(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.frame = ctk.CTkFrame(self.root)
        self.frame.pack(pady=30, padx=30, fill="both", expand=True)

        self.label = ctk.CTkLabel(self.frame, text="Waiting for data...")
        self.label.pack(pady=30)

        self.connection_status_label = ctk.CTkLabel(self.frame, textvariable=self.connection_status)
        self.connection_status_label.pack(pady=10)

        # Add a label and dropdown menu for athlete selection
        self.athlete_label = ctk.CTkLabel(self.frame, text="Select Athlete:")
        self.athlete_label.pack(pady=10)

        # Replace athlete_list with your list of athletes retrieved from the database
        self.athlete_var = ctk.StringVar()
        self.athlete_list = self.fetch_athletes()  # Fetch athletes from database
        print(f"Athlete List: {self.athlete_list}")

        
        if self.athlete_list:
            self.athlete_var.set(self.athlete_list[0])  # Default to the first athlete

       
        self.athlete_dropdown = ctk.CTkOptionMenu(self.frame, variable=self.athlete_var, values=self.athlete_list)
        self.athlete_dropdown.pack(pady=10)
        


        # Add label and dropdown menu for gate length selection
        self.gate_length_label = ctk.CTkLabel(self.frame, text="Select Gate Length:")
        self.gate_length_label.pack(pady=10)

        self.gate_length_var = ctk.StringVar()
        self.gate_length_options = ["10m", "20m", "30m"]
        self.gate_length_var.set(self.gate_length_options[0])  # Default to 10m

        self.gate_length_dropdown = ctk.CTkOptionMenu(self.frame, variable=self.gate_length_var, values=self.gate_length_options)
        self.gate_length_dropdown.pack(pady=10)

        #Start command once the gates are aligned
        self.ready_button = ctk.CTkButton(self.frame, text="Start", command=self.send_ready_signal)
        self.ready_button.pack(pady=10)

        self.save_button = ctk.CTkButton(self.frame, text="Save to Database", command=self.save_to_db)
        self.save_button.pack(pady=10)

        self.show_button = ctk.CTkButton(self.frame, text="Show Saved Timings", command=self.show_data)
        self.show_button.pack(pady=10)

        # self.data_viewer = ctk.CTkTextbox(self.frame, height=20, width=150)
        # self.data_viewer.pack(pady=10)

        # self.scrollbar = ctk.CTkScrollbar(self.frame, command=self.data_viewer.yview)
        # self.scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)
        # self.data_viewer.configure(yscrollcommand=self.scrollbar.set)

        # Add input field and buttons for athlete management

        self.add_athlete_button = ctk.CTkButton(self.frame, text="Add Athlete", command=self.add_athlete)
        self.add_athlete_button.pack(pady=10)

        self.edit_athlete_button = ctk.CTkButton(self.frame, text="Edit Athlete", command=self.edit_athlete)
        self.edit_athlete_button.pack(pady=10)

        self.delete_athlete_button = ctk.CTkButton(self.frame, text="Delete Athlete", command=self.delete_athlete)
        self.delete_athlete_button.pack(pady=10)

    def setup_serial(self):
        try:
            self.ser = serial.Serial('COM5', 9600, timeout=1)
            self.connection_status.set("Connected to Arduino")
        except serial.SerialException as e:
            print(f"Error: {e}")
            self.label.configure(text=f"Error: {e}")
            self.ser = None
            self.ready_button.configure(state=ctk.DISABLED)


    def ready_to_start(self, event=None):
        self.send_ready_signal()

    def send_ready_signal(self): #Works as a reset signal aswell
        if self.ser:
            self.ser.write(b'R')
            print("Sent ready/reset signal to Arduino")
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
            # Check if there is any valid data to save
        valid_data = any(isinstance(item[0], float) for item in self.data)

        if valid_data:
            selected_athlete = self.athlete_var.get()  # Get the selected athlete from the dropdown
            selected_gate_length = self.gate_length_var.get()  # Get the selected gate length from the dropdown

            try:
                conn = sqlite3.connect('timing_data.db')
                c = conn.cursor()

            # Fetch athlete ID from the database (assuming the athlete names are unique)
                c.execute('SELECT id FROM athletes WHERE name = ?', (selected_athlete,))
                row = c.fetchone()
                if row:
                    athlete_id = row[0]
                else:
                # If the athlete doesn't exist in the database, insert them and get the ID
                    c.execute('INSERT INTO athletes (name) VALUES (?)', (selected_athlete,))
                    athlete_id = c.lastrowid

            # Insert timing data with athlete_id
                c.execute('CREATE TABLE IF NOT EXISTS timings (id INTEGER PRIMARY KEY, athlete_id INTEGER, duration REAL, timestamp TEXT, gate_length TEXT)')
                for duration, timestamp in self.data:
                    c.execute('INSERT INTO timings (athlete_id, duration, timestamp) VALUES (?, ?, ?)', (athlete_id, duration, timestamp, selected_gate_length))
                    print(f"Inserted to DB: Athlete ID={athlete_id}, Duration={duration}, Timestamp={timestamp}, Gate Length={selected_gate_length}")


                conn.commit()
                conn.close()
                self.data = []
                self.label.configure(text="Data saved to database")
            except sqlite3.Error as e:
                print(f"SQLite erro while saving data: {e}")
        else:
            print("No data to save")

            # Check if there is any valid data left to enable the save_button
        if any(isinstance(item[0], float) for item in self.data):
            self.save_button.configure(state=ctk.NORMAL)
        else:
            self.save_button.configure(state=ctk.DISABLED)


    def fetch_athletes(self):
        try:
            conn = sqlite3.connect('timing_data.db')
            c = conn.cursor()
            c.execute('SELECT name FROM athletes ORDER BY name')
            athletes = [row[0] for row in c.fetchall()]
            conn.close()
            return athletes
        except sqlite3.Error as e:
            print(f"SQLite error while fetching athletes: {e}")
            return []


    def add_athlete(self):
        new_athlete = simpledialog.askstring("Add Athlete", "Enter new athlete name:")
        if new_athlete:
            conn = sqlite3.connect('timing_data.db')
            c = conn.cursor()
            c.execute('INSERT INTO athletes (name) VALUES (?)', (new_athlete,))
            conn.commit()
            conn.close()
            self.refresh_athlete_list()

    def edit_athlete(self):
        selected_athlete = self.athlete_var.get()
        if selected_athlete:
            new_name = simpledialog.askstring("Edit Athlete", "Enter new name:", initialvalue=selected_athlete)
            if new_name:
                conn = sqlite3.connect('timing_data.db')
                c = conn.cursor()
                c.execute('UPDATE athletes SET name = ? WHERE name = ?', (new_name, selected_athlete))
                conn.commit()
                conn.close()
                self.refresh_athlete_list()

    def delete_athlete(self):
        selected_athlete = self.athlete_var.get()
        if selected_athlete:
            confirm = messagebox.askyesno("Delete Athlete", f"Are you sure you want to delete '{selected_athlete}'?")
            if confirm:
                conn = sqlite3.connect('timing_data.db')
                c = conn.cursor()
                c.execute('DELETE FROM athletes WHERE name = ?', (selected_athlete,))
                conn.commit()
                conn.close()
                self.refresh_athlete_list()

    def refresh_athlete_list(self):
        self.athlete_list = self.fetch_athletes()
        self.athlete_dropdown.configure(values=self.athlete_list)
        if self.athlete_list:
            self.athlete_var.set(self.athlete_list[0])

    def fetch_data(self):
        try:
            conn = sqlite3.connect('timing_data.db')
            c = conn.cursor()

            selected_athlete = self.athlete_var.get()
            if selected_athlete:
                c.execute('SELECT id FROM athletes WHERE name = ?', (selected_athlete,))
                athlete_id = c.fetchone()[0]

                # Fetch timings for the selected athlete only
                c.execute('SELECT * FROM timings WHERE athlete_id = ?', (athlete_id))
                rows = c.fetchall()
            else:
                rows = []

            conn.close()
            print(f"Fetched data: {rows}")
            return rows
        except sqlite3.Error as e:
            print(f"SQLIte error while fetching data: {e}")
            return []

    def show_data(self):
        rows = self.fetch_data()
        if rows:
            display_text = "\n".join([f"ID: {row[0]}, Duration: {row[1]} seconds, Timestamp: {row[2]}" for row in rows])
        else:
            display_text = "No data found for the selected athlete"
        self.label.configure(text=display_text)
        self.data_viewer.delete('1.0', ctk.END)
        self.data_viewer.insert(ctk.END, display_text + "\n")

    def play_beep(self):
        winsound.Beep(1000, 200)  # Beep at 1000 Hz for 200 ms

if __name__ == "__main__":
    root = ctk.CTk()
    app = ArduinoApp(root)
    root.mainloop()
