import tkinter as tk
from tkinter import messagebox
from dronekit import connect, LocationGlobal, VehicleMode
from Move_commands import goto, get_distance_metres, goto_position_target_global_int, arm_and_takeoff, get_location_metres
from generating_path import determine_circle
import time
import math

# Global variables
vehicle = connect('127.0.0.1:14550', wait_ready=True)
starting_location = []


# Functions simulating data retrieval from QGround Control

def connect_vehicle():
    # Establish a connection

    global vehicle
    if not vehicle:
        vehicle = connect('127.0.0.1:14550', wait_ready=True)
    return vehicle


def get_current_location():
    drone = connect_vehicle()
    if drone:
        # Get the global location of the drone
        current_location = drone.location.global_relative_frame

        # Return latitude, longitude and altitude
        return current_location.lat, current_location.lon, current_location.alt
    else:
        messagebox.showerror("Cannot connected to Drone.")


def move_forward(x, y, z):
    # Move forward according to X and Y coordinates
    # Ascend according to altitude Z

    # Arm and take of to altitude of z meters
    arm_and_takeoff(z)
    global vehicle
    if vehicle:
        goto(x, y)

# Area scanning function
# These 100 points will form the perimeter of the circle and the drone will start passing through these points.
# Then, by getting closer to the center towards the inner part of the circle (Radius, i.e. r will be reduced by 1%), these points will be determined and the drone will start to pass through these points.
# Approaching the center will continue until we reach the center. When the center is reached, the drone will land at the center.


def patrol_path(path):
    for waypoint in path:
        # Assuming waypoint is a LocationGlobal object
        goto_position_target_global_int(waypoint)
        while True:
            # Wait for drone to reach the waypoint
            current_location = vehicle.location.global_relative_frame
            distance_to_waypoint = get_distance_metres(current_location, waypoint)
            if distance_to_waypoint < 1:  # Assuming 1 meter threshold
                break
            time.sleep(1)  # Wait for 1 second before checking again


def land_vehicle():
    # Change mode to LAND
    vehicle.mode = VehicleMode("LAND")


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QGround Control User Interface")
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
        self.current_location_value = tk.Label(self.left_frame, text=f"{get_current_location()}", font=("Arial", 12))
        self.current_location_value.pack()

        # Save as Start Point Button (Initially invisible)
        self.start_point_button = tk.Button(self.left_frame, text="Save as Start Point", command=self.set_starting_point, bg="#008CBA", fg="white", font=("Arial", 12))
        self.start_point_button.pack(pady=10)  # Added padx to create space
        self.start_point_button.pack_forget()

        # Save as End Point Button (Initially invisible)
        self.end_point_button = tk.Button(self.left_frame, text="Save as End Point", command=self.set_end_point, bg="#008CBA", fg="white", font=("Arial", 12))
        self.end_point_button.pack(pady=16)  # Added padx to create space
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
        connect_vehicle()
        # Set drone connection status
        self.drone_connected = True
        # Enable move button if drone is connected
        self.move_button.config(state=tk.NORMAL)
        # Show start point button
        self.start_point_button.pack()

    def set_starting_point(self):
        # Set current location as start point
        self.lat, self.lon, self.alt = get_current_location()
        if int(self.alt) >= 10:       # At least 10 meters
            self.starting_end_points.append((self.lat, self.lon, self.alt))
            self.current_location_value.config(text=f"{get_current_location()}")
            self.starting_point_value.config(text=f"{self.starting_end_points[0][0]}, {self.starting_end_points[0][1]}, {self.starting_end_points[0][2]}")

            # Enable end point button
            self.end_point_button.pack()
            self.end_point_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Error", "Please move the drone to required altitude(10 meters at least)")

    def move_drone(self):
        # Move drone according to provided axis values
        x_val = float(self.x_axis_entry.get())
        y_val = float(self.y_axis_entry.get())
        z_val = float(self.z_axis_entry.get())

        move_forward(x_val, y_val, z_val)
        self.moved_forward = True
        if x_val and y_val and z_val:
            messagebox.showinfo("Move Drone", "Drone moved")
        else:
            messagebox.showerror("Error", "Please enter values for all axis")

    def set_end_point(self):
        # Set current location as end point
        current_location = get_current_location()
        self.alt = current_location[2]
        if current_location != self.starting_end_points[0]:
            # Assuming circle_points is the array containing (x, y, z) tuples
            for point in self.starting_end_points:
                z = point[2]  # Accessing the first element of the tuple (x, y, z)
                if z == self.alt:
                    self.starting_end_points.append((current_location[0], current_location[1], self.alt))
                    self.end_point_value.config(text=f"{self.starting_end_points[1][0]}, {self.starting_end_points[1][1]}, {self.starting_end_points[1][2]}")
                    # Enable circle button
                    self.circle_button.config(state=tk.NORMAL)
                    # Disable end point button after setting end point
                    self.end_point_button.config(state=tk.DISABLED)
                else:
                    messagebox.showerror("Altitude of Starting and End Points must be same !!!")
        else:
            messagebox.showerror("Error", "Start and End points cannot be same.")

    def draw_circle(self):
        if self.starting_end_points[0] != self.starting_end_points[1]:
            # Assuming circle_points is the array containing (x, y, z) tuples
            if self.starting_end_points[0][2] == self.starting_end_points[1][2]:   # Checking the 3 rd element of the tuples(z)
                self.all_paths = determine_circle(self.starting_end_points[0], self.starting_end_points[1])

        return self.all_paths

    def scan_area(self):
        self.all_paths = self.draw_circle()  # Getting all paths to patrol
        if self.all_paths:
            for path in self.all_paths:
                patrol_path(path)
            messagebox.showinfo("Area Scanning", "Scanning started in the specified area.")


if __name__ == "__main__":
    app = Application()
    app.mainloop()
