from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from Devices.valve_control import ValveControl
from Devices.pressure_transducer import PressureTransducer
from Devices.thermocouple import Thermocouple
from Devices.load_cell import LoadCell
from backend.labjack_connection import LabJackConnection
from backend.data_logger import DataLogger
from Sequencer.sequencer import Sequencer
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import statistics

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        #______ INITIALIZE MAIN WINDOW SCREEN ______
        super().__init__()
        desktop = QtWidgets.QApplication.desktop()
        screen_rect = desktop.availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()
        # screen_width  = 1200
        # screen_height = 700
        margin = 30
        self.windim_x, self.windim_y = screen_width, screen_height - margin
        # Original dimensions used to build UI - used to scale pixel maps for GUI features appropriately (this is what i changed 10_30_2025)
        self.static_x, self.static_y = 1600, 1007

        # Autosequence input file 
        # TODO: Reset to no input at default - have user upload a file from application
        input_file = 'GG_Test/Sequencer/Sequencer_Info/mug_hotfire_sequence_1.csv'

        # Background setup (P&ID Background)
        import os
        bg_label = QtWidgets.QLabel(self)
        # Build an absolute path to the P&ID relative to this file so the image loads
        # regardless of the current working directory when the app is started.
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(module_dir)
        pid_path = os.path.join(project_root, 'P&ID.png')

        if os.path.exists(pid_path):
            bg_pixmap = QtGui.QPixmap(pid_path)
            if not bg_pixmap.isNull():
                scaled_pixmap = bg_pixmap.scaled(bg_pixmap.width(), self.windim_y, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                bg_label.setPixmap(scaled_pixmap)
                # Place the pixmap anchored to the right side of the window
                bg_label.setGeometry(self.windim_x - scaled_pixmap.width(), 0, scaled_pixmap.width(), self.windim_y)
            else:
                print(f"Warning: Could not load image at {pid_path} (pixmap is null). Using empty background.")
                bg_label.setStyleSheet("background-color: #EEEEEE;")
                bg_label.setGeometry(0, 0, self.windim_x, self.windim_y)
        else:
            print(f"Warning: P&ID image not found at {pid_path}. Using empty background.")
            bg_label.setStyleSheet("background-color: #EEEEEE;")
            bg_label.setGeometry(0, 0, self.windim_x, self.windim_y)

        # Get dimensions of the scaled pixmap
        self.scaled_width = scaled_pixmap.width()
        self.side_panel_width = self.windim_x - self.scaled_width
        # More static_dimensions used for scaling
        self.static_width = 1600 # ichanged this 10_30_2025
        self.static_panel_width = 316
        print(self.side_panel_width)
        # print(screen_height, screen_width)
        self.setWindowTitle("Maelstrom P&ID")
        # 1003, 1728
        window_x = 0
        window_y = 0
        
        self.setGeometry(window_x, window_y, self.windim_x, self.windim_y)
        
        # TODO: Figure out and document exactly how the application shutdown process works
        self.is_closing = False

        # Set border
        self.border_frame = QtWidgets.QFrame(self)
        self.border_frame.setFrameStyle(QtWidgets.QFrame.Box)
        self.border_frame.setLineWidth(5)
        self.border_frame.setGeometry(0, 0, self.windim_x, self.windim_y)

        # Connection Status Label
        self.connection_status = QtWidgets.QLabel("LabJack T7: Connection Missing", self)
        self.connection_status.setGeometry(self.windim_x - 260, 20, 240, 25)
        self.connection_status.setAlignment(Qt.AlignCenter)
        self.connection_status.setStyleSheet("background-color: red; color: white; font-weight: bold;")

        # LabJack Connection
        self.labjack = LabJackConnection(self.connection_status)
        self.labjack.connect_to_labjack()  # Initial connection attempt

        self.shutdown_button = QtWidgets.QPushButton("Emergency Shutdown", self)
        self.shutdown_button.setGeometry(10, self.windim_y-110, self.windim_x - self.scaled_width - 15, 100)  # Position below connection status
        self.shutdown_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.shutdown_button.clicked.connect(self.perform_shutdown)


        #____ INITIALIZE DEVICES _____
        self._transducers = []
        self._thermocouples = []
        self._solenoids = []
        self._loadcells = []

        # Hydrogen Valves
        self._solenoids.append(ValveControl("SN-H2-01", "CIO1", 1000-5, 682 - 5, parent=self))
        # Oxygen valves
        self._solenoids.append(ValveControl("SN-O2-01", "EIO0", 862-15, 678-10-10, parent=self))
        self._solenoids.append(ValveControl("SN-O2-02", "EIO1", 809-15, 677-10-10, parent=self))
        #Nitrogen Valves
    
        self._solenoids.append(ValveControl("SN-N2-02", "", 725 -15, 635-20-15+32, horizontal=True, parent=self))
        self._solenoids.append(ValveControl("SN-N2-01", "", 938-20, 625, horizontal=True, parent=self))
        #407 339
        self._solenoids.append(ValveControl("SN-N2-07", "EIO7", 376-11, 322-10-30, norm_open=True, horizontal=True, parent=self))
        # Carbon Valves
        self._solenoids.append(ValveControl("SN-CO2-01", "EIO3", 588-10, 705- 50 , parent=self))
        # Spark plug
        #self._solenoids.append(ValveControl("Pilot Circuit", "CIO0", int(self.side_panel_width + (540-self.static_panel_width) * self.scaled_width/self.static_width), int(594 * self.windim_y/973), parent=self))

        #Pneumatoic Valves (I'll combine them for now)
        self._solenoids.append(ValveControl("PV-N2-01", "CIO2", 376-11+348, 322-10-30, parent=self))
        self._solenoids.append(ValveControl("PV-FU-01", "CIO2", 588-10+59, 705- 50, parent=self))

        # # # Label Spark Plug (Spark Plug is not included in Maelstorm, but we are keeping this in case for flexibility of other projects)
        # self.label = QtWidgets.QLabel("Spark Plug", self)
        # self.label.setGeometry(445, 210, 100, 25)
        # self.label.setStyleSheet("background-color: #FFFFFF; color: black; font-size: 12pt")
        # self.label.setAlignment(Qt.AlignCenter)


        # TRANSDUCERS for mounted tanks (change the voltage input and output bc i dont know it right now)
        self._transducers.append(PressureTransducer("PT-FU-01", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 591 , 561 -30 + 2, self))
        self._transducers.append(PressureTransducer("PT-N2-07", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, int(537 -10-9-7-5), int(239 +20 +7), self))
        self._transducers.append(PressureTransducer("PT-TI-01", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 752 -15 , 907 , self))
        self._thermocouples.append(Thermocouple("TC-FU-01", 0, 5, 10000, 1, 0, 591 , 561 - 6 , self))

        # TRANSDUCERS FOR N2/Green Lines
        self._transducers.append(PressureTransducer("PT-N2-01", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1539 -10 -15, 269-10 - 10 , self))
        self._transducers.append(PressureTransducer("PT-N2-02", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1334, 171 -15, self))
        self._transducers.append(PressureTransducer("PT-N2-04", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1033, 232 -15, self))
        self._transducers.append(PressureTransducer("PT-N2-05", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1033, 263 -15, self))
        self._transducers.append(PressureTransducer("PT-N2-06", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1033, 294 -15, self))

        # TRANSDUCERS FOR GOX/ Blue Lines
        self._transducers.append(PressureTransducer("PT-O2-02", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1405 +15 +7, 390 +25, self))
        self._transducers.append(PressureTransducer("PT-O2-03", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1130 -10, 418 -8 -4, self))
        self._transducers.append(PressureTransducer("PT-N2-03", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1543-9, 462 - 10, self))
        self._transducers.append(PressureTransducer("PT-O2-05", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 889 -20, 760, self))
        self._transducers.append(PressureTransducer("PT-O2-04", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 715-15, 789 - 10, self))
        self._thermocouples.append(Thermocouple("TC-O2-05", 0, 5, 10000, 1, 0, 889-20, 821 - 10, self))
        self._thermocouples.append(Thermocouple("TC-O2-04", 0, 5, 10000, 1, 0, 715-15, 807 - 7, self))

        # TRANSDUCERS FOR GH2 Yellow Line
        self._transducers.append(PressureTransducer("PT-H2-01", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1450 -7, 508 -10, self))
        self._transducers.append(PressureTransducer("PT-H2-02", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1129-10 -7, 545-10 -4, self))
        self._transducers.append(PressureTransducer("PT-H2-03", "AIN90", "", 0.5, 2.4, 1500, 1, 5.5, 1038-10, 790-10, self))
        self._thermocouples.append(Thermocouple("TC-H2-03", 0, 5, 10000, 1, 0, 1038-10, 813 -7, self))


        # ___ INITIALIZE DATA LOGGER ___
        # Data Logger
        self.data_logger = DataLogger(self._transducers, self._thermocouples, self._loadcells, self._solenoids, width = self.side_panel_width - 15, height = 100, parent=self)
        self.data_logger.move(10, 10) 

        # Connect the state_changed signal to update the main window border for sampling speed
        self.data_logger.state_changed.connect(self.update_border_color)

        # Set initial border style
        self.update_border_color(self.data_logger.high_speed_mode) # TODO: Figure out why it initializes in high speed

        # Timer for updating data value - this controls the sampling rate
        self.reading_timer = QTimer(self)
        self.reading_timer.setTimerType(Qt.PreciseTimer)
        self.reading_timer.timeout.connect(self.update_data)
        self.reading_timer.start(500)  # Initial timing at 500ms

        # Give the data logger a reference to the timer 
        self.data_logger.set_timer(self.reading_timer)

        # Initialize graphs of important data for sidebar
        self._graphs = []
        # Graphs for pressure readings
        self._graph_number = 3
        self._graph_height = int((self.windim_y - 425 - (self._graph_number + 1) * 5)/3)
        # Torch graph
        self._graphs.append(pg.PlotWidget(self))
        self._graphs[0].setGeometry(10, 320, self.windim_x - self.scaled_width - 15, self._graph_height)
        self._graphs[0].setYRange(0, 200)
        self._graphs[0].setBackground('w')
        self._graphs[0].setTitle("PT-N2-07 Pressure")
        self._graphs[0].showGrid(y=True) 
        # GG graph
        self._graphs.append(pg.PlotWidget(self))
        self._graphs[1].setGeometry(10, 325 + self._graph_height, self.windim_x - self.scaled_width - 15, self._graph_height)
        self._graphs[1].setYRange(0, 200)
        self._graphs[1].setBackground('w')
        self._graphs[1].setTitle("PT-FU-01 Pressure")
        self._graphs[1].showGrid(y=True) 
        # OF graph
        self._graphs.append(pg.PlotWidget(self))
        self._graphs[2].setGeometry(10, 330 + 2 * self._graph_height, self.windim_x - self.scaled_width - 15, self._graph_height)
        self._graphs[2].setYRange(0, 200)
        self._graphs[2].setBackground('w')
        self._graphs[2].setTitle("PT-OX-01 Pressure")
        self._graphs[2].showGrid(y=True) 

        # ____ INITIALIZE SEQUENCER ____
        # Device Map so sequencer can interact with devices
        self.device_map = {}

        for i in range(len(self._solenoids)):
            self.device_map[self._solenoids[i].name] = self._solenoids[i]
        for i in range(len(self._transducers)):
            self.device_map[self._transducers[i].name] = self._transducers[i]
        for i in range(len(self._thermocouples)):
            self.device_map[self._thermocouples[i].name] = self._thermocouples[i]
        for i in range(len(self._loadcells)):
            self.device_map[self._loadcells[i].name] = self._loadcells[i]

        # Create the sequencer with the events and devices 
        # Reference to data_logger is just so sequencer can toggle sampling rate
        self.sequencer = Sequencer(self.device_map, self.data_logger, width = self.side_panel_width-15, height = 200, parent=self)
        # Move the sequencer button to the appropriate position (i think)
        self.sequencer.move(10, 115)


    # Function for each data read. Reads data from each device and puts it in a rolling window. If the median
    # of the window exceeds the redline value, it will run the shutdown sequence. The graphs for relevant 
    # transducers will also be updated. Then, write all the data into the data logger
    def update_data(self):
        """Update data readings from all measurement devices if LabJack is connected"""
        if not self.labjack.connection_status:
            print("Warning: Cannot update data reading - LabJack not connected")
            return
            
        # Update Transducers
        for i in range(len(self._transducers)):
            try:
                # Update data reading
                self._transducers[i].update_pressure(self.labjack.handle)
                if self._transducers[i].redline is not None:
                    if statistics.median(self._transducers[i].data) > self._transducers[i].redline:
                        print(f"CRITICAL: {self._transducers[i].name} exceeded redline value! Initiating shutdown.")
                        print(self._transducers[i].data)
                        self.perform_shutdown()

                if self._transducers[i].name == "PT-N2-07":
                    if self.sequencer.running:
                        # Update Graphs
                        self.sequencer.PT_N2_07_data.append(self._transducers[i].pressure)
                        self._graphs[0].plot(self.sequencer.PT_N2_07_data, pen=pg.mkPen(color='b', width=3), clear=True)
                elif self._transducers[i].name == "PT-FU-01":
                    if self.sequencer.running:
                        # Update Graphs
                        self.sequencer.PT_FU_01_data.append(self._transducers[i].pressure)
                        self._graphs[1].plot(self.sequencer.PT_FU_01_data, pen=pg.mkPen(color='r', width=3), clear=True)
                elif self._transducers[i].name == "PT-OX-01":
                    if self.sequencer.running:
                        # Update Graphs
                        self.sequencer.PT_OX_01_data.append(self._transducers[i].pressure)
                        self._graphs[2].plot(self.sequencer.PT_OX_01_data, pen=pg.mkPen(color='r', width=3), clear=True)
            except Exception as e:
                print(f"CRITICAL ERROR: Failed reading pressure from {self._transducers[i].name} ({self._transducers[i].input_channel_1}): {e}")
                # Log the error more prominently for rocket test infrastructure
        for i in range(len(self._thermocouples)):
            try:
                # Update data reading
                self._thermocouples[i].update_temperature(self.labjack.handle)
                if self._thermocouples[i].redline is not None:
                    if statistics.median(self._thermocouples[i].data) > self._thermocouples[i].redline:
                        print(f"CRITICAL: {self._thermocouples[i].name} exceeded redline value! Initiating shutdown.")
                        print(self._thermocouples[i].data)
                        self.perform_shutdown()
            except Exception as e:
                print(f"CRITICAL ERROR: Failed reading pressure from {self._thermocouples[i].name} ({self._thermocouples[i].input_channel_1}): {e}")
                # Log the error more prominently for rocket test infrastructure
        for i in range(len(self._loadcells)):
            try:
                # Update data reading
                self._loadcells[i].update_load(self.labjack.handle)
                if self._loadcells[i].redline is not None:
                    if statistics.median(self._loadcells[i].data) > self._loadcells[i].redline:
                        print(f"CRITICAL: {self._loadcells[i].name} exceeded redline value! Initiating shutdown.")
                        print(self._loadcells[i].data)
                        self.perform_shutdown()
            except Exception as e:
                print(f"CRITICAL ERROR: Failed reading pressure from {self._loadcells[i].name} ({self._loadcells[i].input_channel_1}): {e}")
                # Log the error more prominently for rocket test infrastructure
        self.data_logger.log_data()

    # Function just to update border color to appropriate logging speed color
    def update_border_color(self, high_speed_mode):
        """Update the border color based on the button state"""
        if high_speed_mode:
            # Green border for high speed mode
            border_style = "border: 5px solid #4CAF50;"
        else:
            # Red border for normal speed mode
            border_style = "border: 5px solid #f44336;"
        
        # Update main window border
        self.border_frame.setStyleSheet(border_style)

    # Shutdown sequence to properly depower devices (solenoids)
    def perform_shutdown(self):
        print("Shutting down")
        # Stop sequencer
        if self.sequencer.running:
            self.sequencer.stop_sequencer()
        # Turn off all devices
        for device in self._solenoids:
            try:
                # Force the valve to off (careful of normally opened) regardless of UI state
                if self.labjack.connection_status and self.labjack.handle:
                    # Update the UI state to match
                    # device.update_button_style()
                    if device.norm_open:
                        device.toggle_valve_on()
                    else:
                        device.toggle_valve_off()
                    print(f"{device.name} open state set to {device.valve_open}")
                else:
                    print(f"WARNING: Could not shut down {device.name} - No connection")
            except Exception as e:
                print(f"ERROR closing {device.name}: {e}")
    def closeEvent(self, event):
        # Graceful exit
        if not self.is_closing:
            self.is_closing = True

            # Perform shutdown tasks - only do this from the main window
            self.perform_shutdown()
            self.data_logger.stop()
            self.labjack.close_connection()
        event.accept()