import tkinter as tk
from tkinter import messagebox


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QGround Control Arayüzü")
        self.geometry("800x600")
        self.starting_end_points = []  # Stores the Starting and End Point (Which user wants to use)
        self.lat = None  # Latitude of location
        self.lon = None  # Longitude of location
        self.alt = None  # Altitude of location
        self.all_paths = None  # All paths generated with genetic algorithms.

        # Global variable to track drone connection status
        self.drone_connected = False

        # Global variable to track drone move status
        self.moved_forward = False

        # Frame for left side widgets
        self.left_frame = tk.Frame(self)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Frame for right side widgets
        self.right_frame = tk.Frame(self)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Connect Button
        self.connect_button = tk.Button(self, text="Connect", command=self.connect_drone, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.connect_button.place(relx=0.5, rely=0.1, anchor=tk.CENTER)

        # Current Location Widgets
        self.current_location_label = tk.Label(self.left_frame, text="Current Location:", font=("Arial", 12))
        self.current_location_label.pack()
        self.current_location_value = tk.Label(self.left_frame, text=f"{self.get_current_location()}", font=("Arial", 12))
        self.current_location_value.pack()

        # Save as Start Point Button (Initially invisible)
        self.start_point_button = tk.Button(self.left_frame, text="Save as Start Point", command=self.set_starting_point, bg="#008CBA", fg="white", font=("Arial", 12))
        self.start_point_button.pack(pady=(10, 2))  # Added padx to create space
        self.start_point_button.pack_forget()

        # Empty space between Save as End Point and Save as Start Point
        self.space_label = tk.Label(self.left_frame, text="", font=("Arial", 12))
        self.space_label.pack()

        # Save as End Point Button (Initially invisible)
        self.end_point_button = tk.Button(self.left_frame, text="Save as End Point", command=self.set_end_point, bg="#008CBA", fg="white", font=("Arial", 12))
        self.end_point_button.pack(pady=(2, 10))  # Added padx to create space
        self.end_point_button.pack_forget()
        self.end_point_button.config(state=tk.DISABLED)  # Initially disabled

        # Starting Point Label
        self.starting_point_label = tk.Label(self.left_frame, text="Starting Point:", font=("Arial", 12))
        self.starting_point_label.pack()
        self.starting_point_value = tk.Label(self.left_frame, text="", font=("Arial", 12))
        self.starting_point_value.pack()

        # End Point Label
        self.end_point_label = tk.Label(self.left_frame, text="End Point:", font=("Arial", 12))
        self.end_point_label.pack()
        self.end_point_value = tk.Label(self.left_frame, text="", font=("Arial", 12))
        self.end_point_value.pack()

        # Right Side Widgets
        self.x_axis_label = tk.Label(self.right_frame, text="X axis:", font=("Arial", 12))
        self.x_axis_label.pack()
        self.x_axis_entry = tk.Entry(self.right_frame)
        self.x_axis_entry.pack()

        self.y_axis_label = tk.Label(self.right_frame, text="Y axis:", font=("Arial", 12))
        self.y_axis_label.pack()
        self.y_axis_entry = tk.Entry(self.right_frame)
        self.y_axis_entry.pack()

        self.z_axis_label = tk.Label(self.right_frame, text="Z axis:", font=("Arial", 12))
        self.z_axis_label.pack()
        self.z_axis_entry = tk.Entry(self.right_frame)
        self.z_axis_entry.pack()

        self.move_button = tk.Button(self.right_frame, text="Move in meters", command=self.move_drone, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.move_button.pack(pady=20)
        self.move_button.config(state=tk.DISABLED)  # Initially disabled

        # Bottom Buttons
        self.circle_button = tk.Button(self, text="Draw a Circle", command=self.draw_circle, bg="#FF5733", fg="white", font=("Arial", 14))
        self.circle_button.pack(side=tk.BOTTOM, padx=20, pady=20)
        self.circle_button.config(state=tk.DISABLED)  # Initially disabled

        self.scan_button = tk.Button(self, text="Scan Area", command=self.scan_area, bg="#FF5733", fg="white", font=("Arial", 14))
        self.scan_button.pack(side=tk.BOTTOM, padx=20, pady=10)
        self.scan_button.config(state=tk.DISABLED)  # Initially disabled

    def connect_drone(self):
        # Set drone connection status
        self.drone_connected = True
        # Enable move button if drone is connected
        self.move_button.config(state=tk.NORMAL)
        # Show start point button
        self.start_point_button.pack()

    def get_current_location(self):
        # Drone'un global konumunu al
        current_location_lat = 30
        current_location_lon = 40
        current_location_alt = 50
        # Enlem, boylam ve irtifayı döndür
        return current_location_lat, current_location_lon, current_location_alt

    def set_starting_point(self):
        # Set current location as start point
        self.lat, self.lon, self.alt = self.get_current_location()
        self.starting_end_points.append((int(self.x_axis_entry.get()) + self.lat, int(self.y_axis_entry.get()) + self.lon, int(self.z_axis_entry.get()) + self.alt))
        self.current_location_value.config(text=f"{self.starting_end_points[0][0]}, {self.starting_end_points[0][1]}, {self.starting_end_points[0][2]}")
        self.starting_point_value.config(text=f"{self.starting_end_points[0][0]}, {self.starting_end_points[0][1]}, {self.starting_end_points[0][2]}")

        # Enable end point button
        self.end_point_button.pack()
        self.end_point_button.config(state=tk.NORMAL)

    def set_end_point(self):
        # Set current location as end point
        self.lat, self.lon, self.alt = self.get_current_location()
        current_location = (int(self.x_axis_entry.get()) + self.lat, int(self.y_axis_entry.get()) + self.lon, int(self.z_axis_entry.get()) + self.alt)
        if current_location != self.starting_end_points[0]:
            self.starting_end_points.append(current_location)
            self.end_point_value.config(text=f"{self.starting_end_points[1][0]}, {self.starting_end_points[1][1]}, {self.starting_end_points[1][2]}")
            # Enable circle button
            self.circle_button.config(state=tk.NORMAL)
            # Disable end point button after setting end point
            self.end_point_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Error", "Start and End points cannot be same.")

    def move_drone(self):
        # Move drone according to provided axis values
        x_val = self.x_axis_entry.get()
        y_val = self.y_axis_entry.get()
        z_val = self.z_axis_entry.get()

        if x_val and y_val and z_val:
            messagebox.showinfo("Move Drone", "Drone moved")
        else:
            messagebox.showerror("Error", "Please enter values for all axis")

    def draw_circle(self):
        # Draw a circle
        messagebox.showinfo("Draw Circle", "Circle drawn")
        # Enable scan button
        self.scan_button.config(state=tk.NORMAL)

    def scan_area(self):
        # Scan the area
        messagebox.showinfo("Scan Area", "Area scanned")


if __name__ == "__main__":
    app = Application()
    app.mainloop()
