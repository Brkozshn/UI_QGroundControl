import sys
from PyQt5.QtWidgets import (
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

from leo.core.leoQt import has_WebEngineWidgets
if has_WebEngineWidgets:
    from leo.core.leoQt import QtWebEngineWidgets
    QWebEngineView = QtWebEngineWidgets.QWebEngineView
    # If you have existing code that uses QWebView:
    QWebView = QWebEngineView
import time
import math
import folium

from dronekit import connect, LocationGlobal, VehicleMode
from Move_commands import goto, get_distance_metres, goto_position_target_global_int, arm_and_takeoff, get_location_metres
from generating_path import determine_circle


# Functions simulating data retrieval from QGround Control

# Global variables

global vehicle


def connect_vehicle():
    starting_location = []
    vehicle = connect('127.0.0.1:14550', wait_ready=True)
    return vehicle


def get_current_location():
    drone = connect_vehicle()
    if drone:
        current_location = drone.location.global_relative_frame
        return current_location.lat, current_location.lon, current_location.alt
    else:
        QMessageBox.critical(None, "Connection Error", "Cannot connect to Drone.")


def move_forward(x, y, z):
    arm_and_takeoff(z)
    global vehicle
    if vehicle:
        goto(x, y)


def patrol_path(path):
    for waypoint in path:
        goto_position_target_global_int(waypoint)
        while True:
            current_location = vehicle.location.global_relative_frame
            distance_to_waypoint = get_distance_metres(current_location, waypoint)
            if distance_to_waypoint < 1:
                break
            time.sleep(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QGround Control User Interface")
        self.setGeometry(100, 100, 800, 600)
        self.starting_end_points = []
        self.lat = None
        self.lon = None
        self.alt = None
        self.all_paths = None
        self.drone_connected = False
        self.moved_forward = False

        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left side widgets
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 12pt;")
        self.connect_button.clicked.connect(self.connect_drone)
        left_layout.addWidget(self.connect_button)

        self.current_location_label = QLabel("Current Location:")
        left_layout.addWidget(self.current_location_label)
        self.current_location_value = QLabel()
        left_layout.addWidget(self.current_location_value)

        self.start_point_button = QPushButton("Save as Start Point")
        self.start_point_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 12pt;")
        self.start_point_button.clicked.connect(self.set_starting_point)
        self.start_point_button.setVisible(False)
        left_layout.addWidget(self.start_point_button)

        self.end_point_button = QPushButton("Save as End Point")
        self.end_point_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 12pt;")
        self.end_point_button.clicked.connect(self.set_end_point)
        self.end_point_button.setVisible(False)
        self.end_point_button.setEnabled(False)
        left_layout.addWidget(self.end_point_button)

        self.starting_point_label = QLabel("Starting Point:")
        left_layout.addWidget(self.starting_point_label)
        self.starting_point_value = QLabel()
        left_layout.addWidget(self.starting_point_value)

        self.end_point_label = QLabel("End Point:")
        left_layout.addWidget(self.end_point_label)
        self.end_point_value = QLabel()
        left_layout.addWidget(self.end_point_value)

        main_layout.addWidget(left_widget)

        # Right side widgets
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.x_axis_label = QLabel("X axis:")
        right_layout.addWidget(self.x_axis_label)
        self.x_axis_entry = QLineEdit()
        right_layout.addWidget(self.x_axis_entry)

        self.y_axis_label = QLabel("Y axis:")
        right_layout.addWidget(self.y_axis_label)
        self.y_axis_entry = QLineEdit()
        right_layout.addWidget(self.y_axis_entry)

        self.z_axis_label = QLabel("Z axis:")
        right_layout.addWidget(self.z_axis_label)
        self.z_axis_entry = QLineEdit()
        right_layout.addWidget(self.z_axis_entry)

        self.move_button = QPushButton("Move in meters")
        self.move_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 12pt;")
        self.move_button.clicked.connect(self.move_drone)
        self.move_button.setEnabled(False)
        right_layout.addWidget(self.move_button)

        main_layout.addWidget(right_widget)

        # Bottom Buttons
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        self.circle_button = QPushButton("Draw a Circle")
        self.circle_button.setStyleSheet("background-color: #FF5733; color: white; font-size: 14pt;")
        self.circle_button.clicked.connect(self.draw_circle)
        self.circle_button.setEnabled(False)
        bottom_layout.addWidget(self.circle_button)

        self.scan_button = QPushButton("Scan Area")
        self.scan_button.setStyleSheet("background-color: #FF5733; color: white; font-size: 14pt;")
        self.scan_button.clicked.connect(self.scan_area)
        self.scan_button.setEnabled(False)
        bottom_layout.addWidget(self.scan_button)

        main_layout.addWidget(bottom_widget)

        # Google Maps WebView
        self.web_view = QWebEngineView()
        main_layout.addWidget(self.web_view)

        self.load_google_map()

    def load_google_map(self):
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Google Maps</title>
            <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyBvF4aNNii8rcNbiRlOq8iciS2J-FkZLKA&callback=initMap"
                    async defer></script>
            <style>
                #map {
                    height: 100%;
                }
                html, body {
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map;
                function initMap() {
                    var myLatLng = {lat: -34.397, lng: 150.644};
                    map = new google.maps.Map(document.getElementById('map'), {
                        center: myLatLng,
                        zoom: 8
                    });
                }
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html_content)

    def connect_drone(self):
        connect_vehicle()
        self.drone_connected = True
        self.move_button.setEnabled(True)
        self.start_point_button.setVisible(True)

    def set_starting_point(self):
        self.lat, self.lon, self.alt = get_current_location()
        if int(self.alt) >= 10:
            self.starting_end_points.append((self.lat, self.lon, self.alt))
            self.current_location_value.setText(
                f"{self.starting_end_points[0][0]}, {self.starting_end_points[0][1]}, {self.starting_end_points[0][2]}")
            self.starting_point_value.setText(
                f"{self.starting_end_points[0][0]}, {self.starting_end_points[0][1]}, {self.starting_end_points[0][2]}")
            self.end_point_button.setVisible(True)
            self.end_point_button.setEnabled(True)
        else:
            QMessageBox.critical(self, "Error", "Please move the drone to required altitude (at least 10 meters).")

    def move_drone(self):
        x_val = float(self.x_axis_entry.text())
        y_val = float(self.y_axis_entry.text())
        z_val = float(self.z_axis_entry.text())

        if x_val and y_val and z_val:
            move_forward(x_val, y_val, z_val)
            self.moved_forward = True
            QMessageBox.information(self, "Move Drone", "Drone moved")
        else:
            QMessageBox.critical(self, "Error", "Please enter values for all axis")

    def set_end_point(self):
        current_location = get_current_location()
        self.alt = current_location[2]
        if current_location != self.starting_end_points[0]:
            for point in self.starting_end_points:
                z = point[2]
                if z == self.alt:
                    self.starting_end_points.append((current_location[0], current_location[1], self.alt))
                    self.end_point_value.setText(
                        f"{self.starting_end_points[1][0]}, {self.starting_end_points[1][1]}, {self.starting_end_points[1][2]}")
                    self.circle_button.setEnabled(True)
                    self.end_point_button.setEnabled(False)
                else:
                    QMessageBox.critical(self, "Error", "Altitude of Starting and End Points must be same")
        else:
            QMessageBox.critical(self, "Error", "Start and End points cannot be same.")

    def draw_circle(self):
        if self.starting_end_points[0] != self.starting_end_points[1]:
            if self.starting_end_points[0][2] == self.starting_end_points[1][2]:
                self.all_paths = determine_circle(self.starting_end_points[0], self.starting_end_points[1])
        return self.all_paths

    def scan_area(self):
        self.all_paths = self.draw_circle()
        if self.all_paths:
            for path in self.all_paths:
                patrol_path(path)
            QMessageBox.information(self, "Area Scanning", "Scanning started in the specified area.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
