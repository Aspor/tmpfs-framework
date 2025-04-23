# tmpfs-framework
Package to read senor data from tmpfs and to create a watchdog to take snapshots from the data.

Requiremets:
cbor2>=5.4.6
numpy>=1.21.5
watchdog>=2.1.6

## Build and install using pythons build module and pip:

        python3 -m build
        python3 -m pip install dist/tmpfs_framework-0.0.1-py3-none-any.whl


## Explanation of the purpose of each function in the SensorReader class and the read function:

**__init__:**

Initializes the SensorReader object with the specified parameters.
Sets up the directory paths, filenames, and sensor attributes.
Checks for the presence of measurement and metadata files.
Initializes multiprocessing events and attributes.

**init_attributes:**

Initializes the attributes for the SensorReader object.
Creates getter functions for each attribute and sets them as properties of the class.

**attribute_function:**

Creates a getter function for the specified attribute.
The function reads the value of the attribute from the temporary filesystem as a numpy array.

**get_data:**

Retrieves data from the sensor.
Reads the data and intrinsics from the specified path.

**takeSnapShot:**

Takes a snapshot of the sensor data.
Saves the snapshot to the specified path, with an option to compress the data.

**updateAttributes:**

Updates the attributes for the SensorReader object.
Reinitializes the attributes by reading the directory contents.

**getValue:**

Retrieves the value of the specified attribute.
Reads the data from the file corresponding to the attribute.

**getBinary:**

Retrieves the binary data of the specified attribute.
Reads the binary data from the file, handling different file extensions.

**getValueFilePath:**

Constructs the file path for the specified attribute.
Returns the full path to the attribute file.

**startWrite:**

Starts the process of writing sensor data.
Initializes the watchdog to monitor changes in the sensor data directory.

**writerWorker:**

Worker function that writes sensor data.
Takes a snapshot of the data at regular intervals.

**init_watchdog:**

Initializes the watchdog to monitor changes in the sensor data directory.
Sets up an event handler to trigger the writerWorker function when changes are detected.

**stop_watchdog:**

Stops the watchdog monitoring.
Clears the wait event and deletes the observer.

**get_packed_data_location:**

Returns the location of the packed data (measurement.zip) if it exists.

**get_metadata_location:**

Returns the location of the metadata (metadata.zip) if it exists.

**attach_watchdog:**

Attaches a watchdog to monitor changes in the specified value.
Executes a callback function when changes are detected.

**disable_watchdog:**

Disables the watchdog monitoring the specified value.
Stops and deletes the observer.

**read:**

Reads data from the specified file.
Handles reading from directories, zip files, and regular files.
Decodes the data using the CBOR decoder.
