# Maelstrom P&ID Control System

A PyQt5-based application for controlling and monitoring a fluid system with LabJack interface for valve control, pressure readings, data logging, and automated sequencing.

The project Maelstrom is a 500-lbf kerosene-LOX heatsink engine designed as a testbed for PURPL to experiment with various experimental rocket propulsion technologies. One of these technologies is a coaxial swirl injector—an injector type that utilizes concentric passages and tangential inlets to spin fuel and oxidizer into hollow conical sprays, promoting fine atomization and rapid mixing for efficient combustion. Maelstrom is equipped with a 6-element fuel-centered bi-swirl coaxial injector 3D printed by Protolabs out of 17-4 stainless steel

## Overview

This application provides a graphical interface for controlling a fluid control system with the following features:

- Real-time pressure monitoring from multiple transducers
- Solenoid valve control with visual state indicators
- Data logging with adjustable sampling rates
- Automated sequencing capability for valve operations
- Emergency shutdown functionality

The P&ID of Maelstrom looks below
![P&ID](P&ID.png)

Program Running with the P&ID
![Program](Example_Image.png)

## System Requirements

- Python 3.14.0
- PyQt5
- LabJack T7 device and LJM library [Download Link](https://support.labjack.com/docs/ljm-software-installer-windows)
- Additional Python libraries: csv, threading, queue, datetime

## Installation

1. Ensure you have Python 3.14.0 or greater installed
2. Clone or download this repository to your local machine
3. Install required packages by navigating to the Maelstrom_PID directory and running:

   ```
   pip install --user -r requirements.txt
   ```

   This will install the necessary dependencies including PyQt5 and LabJack-LJM

   If there is an issue with dependencies use the following commands below:
   pip install pyqtgraph
   pip install labjack-ljm
   pip install PyQt5-tools
   pip install PyQt5

## Running the Application

The application is started by running the main.py file from within the Maelstrom_PID directory:

```
python main.py
```

This will open the fluid panel interface, which is the main entry point for the program. The fluid panel will open all other necessary panels automatically.

## Application Structure

- **main.py**: Application entry point
- **MainPanel.py**: Main control window showing system P&ID
- **data_logger.py**: Handles data logging functionality
- **pressure_transducer.py**: Interface for pressure sensors
- **valve_control.py**: Controls for solenoid valves
- **sequencer.py**: Handles automated valve sequencing

## Usage Instructions

### Main Interface

The application opens with one main windows:

1. **Maelstrom P&ID** - Main interface showing system diagram with pressure readings

MainPanel.py is where most objects are initialized and the main script operates.

- The main GUI panel will be loaded
  - There are two main parts of the GUI panel
  - The background "pixmap" and the controls sidebar
    - Features are scaled off of a static coordinate plane designed for a 1728 by 973 (numbers may not be exact) pixel window
    - Controls panel uses hardcoded pixel dimensions and does not scale. Thus, the pixmap must scale off of an offset frame
  - A border reflects the logging speed for the data logger. Green is high and red is low
  - A connection status label reflects the connection status to the Labjack. Red indicates disconnection
- Autosequence file will be read in
- Various devices (PTs, Thermocouples, Solenoids, Loadcells, etc.) are initialized and stored in lists.
  - Spark plug is initialized as a "solenoid" as it exhibits nearly identical on/off behavior
- Data logger is initialized
  - Controls sampling rate
  - Writes data to buffer then dumps to CSV
- Sequencer is initialized
  - The device map allows the Sequencer to interact with the device objects
  - Auto-sequence is started from a button

### Data Logging

- The **LOGGING SPEED** button toggles between high-speed (10ms) and low-speed (500ms) data collection
- Enter a base filename in the text field before starting logging
- Log files are saved in the "Torch_Hot_Fire/data" directory with timestamps
- The border color of both panels indicates the current logging speed (red = low, green = high)

### Valve Control

- Valves are shown in the Valve Control Panel
- Click a valve to change its state (open/closed)
- "O" (green) indicates an open valve, "C" (red) indicates a closed valve

### Sequencer

- The **Start Sequencer** button initiates an automated valve sequence
- Sequences are loaded from a CSV file via the sequence_reader module
- The sequencer automatically switches to high-speed logging when started

### Emergency Shutdown

- The **Emergency Shutdown** button will reset all valves to their default state and stop any active sequence
- Use this instead of the sequencer's stop button due to known issues

### Data Log Files

Log files are CSV format with the following columns:

- Timestamp
- Pressure readings for each transducer
- State of each valve (True/False)

## Known Issues

    - Some of the Pressure readings are misaligned but this will be fixed in the next update since it's just fixing the numbers

## Permissions and Hardware Access

This application requires appropriate permissions to access the LabJack hardware. Ensure the user running the application has the required system permissions.
