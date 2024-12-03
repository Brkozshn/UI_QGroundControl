import os
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QMessageBox
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QFont
from leo.core.leoQt import has_WebEngineWidgets
if has_WebEngineWidgets:
    from leo.core.leoQt import QtWebEngineWidgets
    QWebEngineView = QtWebEngineWidgets.QWebEngineView
    # If you have existing code that uses QWebView:
    QWebView = QWebEngineView
import math
import folium


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.map = None
        self.setWindowTitle("QGround Control Interface")
        self.setGeometry(100, 100, 1200, 800)  # Increased window size for the map
        self.starting_end_points = []  # Stores the Starting and End Point (Which user wants to use)
        self.lat = None
        self.lon = None
        self.alt = None
        self.all_paths = [[40,50], [60,70]]

        # Global variable to track drone connection status
        self.drone_connected = False

        # Central widget for the layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left side widgets
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Connect Button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 12pt;")
        self.connect_button.clicked.connect(self.connect_drone)
        left_layout.addWidget(self.connect_button)

        # Current Location Widgets
        self.current_location_label = QLabel("Current Location:")
        self.current_location_label.setFont(QFont("Arial", 16))  # Larger font size for labels
        left_layout.addWidget(self.current_location_label)
        self.current_location_value = QLabel()
        self.current_location_value.setFont(QFont("Arial", 16))  # Larger font size for labels
        left_layout.addWidget(self.current_location_value)

        # Save as Start Point Button (Initially invisible)
        self.start_point_button = QPushButton("Save as Start Point")
        self.start_point_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 12pt;")
        self.start_point_button.clicked.connect(self.set_starting_point)
        left_layout.addWidget(self.start_point_button)
        self.start_point_button.setVisible(False)

        # Save as End Point Button (Initially invisible)
        self.end_point_button = QPushButton("Save as End Point")
        self.end_point_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 12pt;")
        self.end_point_button.clicked.connect(self.set_end_point)
        left_layout.addWidget(self.end_point_button)
        self.end_point_button.setVisible(False)
        self.end_point_button.setEnabled(False)  # Initially disabled

        # Starting Point Label
        self.starting_point_label = QLabel("Starting Point:")
        self.starting_point_label.setFont(QFont("Arial", 16))  # Larger font size for labels
        left_layout.addWidget(self.starting_point_label)
        self.starting_point_value = QLabel()
        self.starting_point_value.setFont(QFont("Arial", 16))  # Larger font size for labels
        left_layout.addWidget(self.starting_point_value)

        # End Point Label
        self.end_point_label = QLabel("End Point:")
        self.end_point_label.setFont(QFont("Arial", 16))  # Larger font size for labels
        left_layout.addWidget(self.end_point_label)
        self.end_point_value = QLabel()
        self.end_point_value.setFont(QFont("Arial", 16))  # Larger font size for labels
        left_layout.addWidget(self.end_point_value)

        # Add left widget to main layout
        main_layout.addWidget(left_widget)

        # Right side widgets
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # X, Y, Z Entries
        xyz_layout = QHBoxLayout()  # Layout for X, Y, Z entries
        self.x_axis_label = QLabel("X axis:")
        self.x_axis_label.setFont(QFont("Arial", 16))  # Larger font size for labels
        xyz_layout.addWidget(self.x_axis_label)
        self.x_axis_entry = QLineEdit()
        xyz_layout.addWidget(self.x_axis_entry)

        self.y_axis_label = QLabel("Y axis:")
        self.y_axis_label.setFont(QFont("Arial", 16))  # Larger font size for labels
        xyz_layout.addWidget(self.y_axis_label)
        self.y_axis_entry = QLineEdit()
        xyz_layout.addWidget(self.y_axis_entry)

        self.z_axis_label = QLabel("Z axis:")
        self.z_axis_label.setFont(QFont("Arial", 16))  # Larger font size for labels
        xyz_layout.addWidget(self.z_axis_label)
        self.z_axis_entry = QLineEdit()
        xyz_layout.addWidget(self.z_axis_entry)

        right_layout.addLayout(xyz_layout)

        self.move_button = QPushButton("Move in meters")
        self.move_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 12pt;")
        self.move_button.clicked.connect(self.move_drone)
        right_layout.addWidget(self.move_button)
        self.move_button.setEnabled(False)  # Initially disabled
        self.move_button.setVisible(False)

        # Add right widget to main layout
        main_layout.addWidget(right_widget)

        # Bottom Buttons
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        self.circle_button = QPushButton("Draw a Circle")
        self.circle_button.setStyleSheet("background-color: #FF5733; color: white; font-size: 14pt;")
        self.circle_button.clicked.connect(self.draw_circle)
        bottom_layout.addWidget(self.circle_button)
        self.circle_button.setVisible(False)
        self.circle_button.setEnabled(False)  # Initially disabled

        self.scan_button = QPushButton("Scan Area")
        self.scan_button.setStyleSheet("background-color: #FF5733; color: white; font-size: 14pt;")
        self.scan_button.clicked.connect(self.scan_area)
        bottom_layout.addWidget(self.scan_button)
        self.scan_button.setVisible(False)
        self.scan_button.setEnabled(False)  # Initially disabled

        # Add bottom widget to main layout
        main_layout.addWidget(bottom_widget)

        # Graphics View for drawing circles and points
        self.graphics_view = QWidget()
        self.graphics_view.setStyleSheet("background-color: white;")
        main_layout.addWidget(self.graphics_view)

        self.circle_points = []  # List to store circle points

    def connect_drone(self):
        # Set drone connection status
        self.drone_connected = True
        # Show start point button
        self.start_point_button.setVisible(True)
        self.move_button.setVisible(True)
        self.move_button.setEnabled(True)

    def set_starting_point(self):
        # Set current location as start point
        self.lat, self.lon, self.alt = 30, 40, 50  # Mock current location
        self.starting_end_points.append((
            int(self.x_axis_entry.text()) + int(self.lat),
            int(self.y_axis_entry.text()) + int(self.lon),
            int(self.z_axis_entry.text()) + int(self.alt)
        ))
        self.current_location_value.setText(f"{self.starting_end_points[0][0]}, "
                                            f"{self.starting_end_points[0][1]}, "
                                            f"{self.starting_end_points[0][2]}")
        self.starting_point_value.setText(f"{self.starting_end_points[0][0]}, "
                                          f"{self.starting_end_points[0][1]}, "
                                          f"{self.starting_end_points[0][2]}")

        # Enable end point button
        self.end_point_button.setVisible(True)
        self.end_point_button.setEnabled(True)

        QMessageBox.information(self, "Starting Point", "Starting Point is Saved")

    def set_end_point(self):
        # Set current location as end point
        self.lat, self.lon, self.alt = 30, 40, 50  # Mock current location
        current_location = (
            int(self.x_axis_entry.text()) + int(self.lat),
            int(self.y_axis_entry.text()) + int(self.lon),
            int(self.z_axis_entry.text()) + int(self.alt)
        )
        if current_location != self.starting_end_points[0]:
            self.starting_end_points.append(current_location)
            self.end_point_value.setText(f"{self.starting_end_points[1][0]}, "
                                         f"{self.starting_end_points[1][1]}, "
                                         f"{self.starting_end_points[1][2]}")
            # Enable circle button
            self.circle_button.setVisible(True)
            self.circle_button.setEnabled(True)
            # Disable end point button after setting end point
            self.end_point_button.setEnabled(False)
            QMessageBox.information(self, "End Point", "End Point is Saved")
        else:
            QMessageBox.critical(self, "Error", "Start and End points cannot be same.")

    def move_drone(self):
        # Move drone according to provided axis values
        x_val = self.x_axis_entry.text()
        y_val = self.y_axis_entry.text()
        z_val = self.z_axis_entry.text()

        if x_val and y_val and z_val:
            QMessageBox.information(self, "Move Drone", "Drone moved")
        else:
            QMessageBox.critical(self, "Error", "Please enter values for all axis")

    def draw_circle(self):
        # Draw a circle
        QMessageBox.information(self, "Draw Circle", "Circle drawn")
        # Enable scan button
        self.scan_button.setVisible(True)
        self.scan_button.setEnabled(True)

        # Calculate circle points
        circle_center = (self.starting_end_points[0][0], self.starting_end_points[0][1])
        radius = 100  # Example radius
        num_points = 100
        angle_increment = 360 / num_points
        self.circle_points = [(circle_center[0] + radius * math.cos(math.radians(angle)),
                               circle_center[1] + radius * math.sin(math.radians(angle)))
                              for angle in range(0, 360, int(angle_increment))]

        # Refresh the graphics view
        self.graphics_view.update()

    def scan_area(self):
        QMessageBox.information(self,"Area Scanning", "Scanning started in the specified area.")

        self.generate_map()  # Generate the map
        self.display_map()  # Display the map

    def generate_map(self):
        # Create a map centered on the starting point
        self.map = folium.Map(location=[self.starting_end_points[0][0], self.starting_end_points[0][1]], zoom_start=15)

        # Add a marker for the starting point
        folium.Marker(location=[self.starting_end_points[0][0], self.starting_end_points[0][1]]).add_to(self.map)

        # Add a marker for the end point
        folium.Marker(location=[self.starting_end_points[1][0], self.starting_end_points[1][1]]).add_to(self.map)

        # Add circles to the map
        for path in self.all_paths:
            folium.Circle(location=[path[0].lat, path[0].lon], radius=100, color='red').add_to(self.map)

        # Save the map to an HTML file
        self.map.save('map.html')

    def display_map(self):
        # Create a new window for the map
        map_window = QMainWindow(self)
        map_window.setWindowTitle("Map")

        # Create a web browser widget and display the map
        browser = QWebEngineView(map_window)
        browser.setUrl(QUrl.fromLocalFile(os.path.abspath('map.html')))
        map_window.setCentralWidget(browser)

        # Add an event filter to detect when the map window is closed
        map_window.installEventFilter(self)

        # Show the map window
        map_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
