# TMPFS Framework Example

This example demonstrates how to use the `tmpfs_framework` for writing and reading sensor data in a temporary filesystem. It includes:

- Creating a custom writer (`DummyWriter`) that writes numeric data and packs it into a ZIP file.
- Reading data using `SensorReader`.
- Using watchdogs to react to changes.
- Taking snapshots and recording datasets.

---

## Requirements

- Python 3.8+
- `tmpfs_framework` installed and configured
- A Linux system with `tmpfs` mounted (or equivalent)


### Basic usage

Import required classes and methods
```python
>>> from tmpfs_framework import SensorReader, SensorWriter
>>> from tmpfs_framework.sensor_writer import pack_to_zip
>>> from tmpfs_framework.sensor_reader import read

```

Implement a dummy writer. With actual sensor writer_worker should be called periodically or when new data is aquired. In this example it is called when needed
```python

>>> class DummyWriter(SensorWriter):
...     def __init__(self, filename):
...         super().__init__("dummy", filename)

...     def writer_worker(self, number):
...         self.write("number", number)
...         self.write("number_x2", number * 2)
...         pack_to_zip(["number", "number_x2"], self.data_path)

```
Create instance of writer and reader. Writer needs to write something before reader can be created

```python
>>> dummy_writer = DummyWriter("first")
>>> dummy_writer.writer_worker(1)
>>> dummy_reader = SensorReader("dummy")

```
Accessing values

```python
#Now it's possible to access the value
>>> dummy_reader.get_data("number")
1
>>> dummy_reader.number
1
>>> dummy_reader.get_data("number_x2")
2

```

Writing and reading

```python
# Verify updates
>>> for i in range(5):
...     dummy_writer.writer_worker(i)
...     print(f"{dummy_reader.number} {dummy_reader.number_x2}")
0 0
1 2
2 4
3 6
4 8

```

---

## Advanced Doctest: Watchdog and Snapshot
Extra imports
```python
>>> from time import sleep
>>> from tmpfs_framework import TMPFS_PATH
>>> import os, shutil

```
Create a new writer instance
```
>>> dummy_writer = DummyWriter("watchdog_test")
>>> dummy_writer.writer_worker(-1)

```
Need to specify which dummy reader to use. Othewise wrong writer is used
```python
>>> dummy_reader = SensorReader("dummy","watchdog_test")
>>> dummy_reader2 = SensorReader("dummy")

#With default contructor we get previous
>>> dummy_reader2.number
4

#When specifying which directory to read
>>> dummy_reader.number
-1

```
Attach a watchdog to react to changes in 'number'

Printing happens in different thread. Could be any function attcepting a number

```Python
>>> dummy_reader.attach_watchdog("number", print)
>>> for i in range(3):
...     dummy_writer.writer_worker(i)
...     sleep(0.01)
0
1
2

# Disable watchdog
>>> dummy_reader.disable_watchdog("number")

```
Take a snapshot of data
```Python

>>> dataset_path = os.path.join(TMPFS_PATH, "dummy_dataset")
>>> os.mkdir(dataset_path)
>>> dummy_reader.take_snapshot(dataset_path)
True
>>> zip_path = os.listdir(dataset_path)[0]
>>> read(os.path.join(dataset_path, zip_path))
{'number': 2, 'number_x2': 4}

```

Snapshot won't change value anymore
```python
>>> dummy_writer.writer_worker(123)
>>> dummy_reader.number
123
>>> read(os.path.join(dataset_path, zip_path))
{'number': 2, 'number_x2': 4}

```
Current Epoch Unix Timestamp in milliseconds is automatically added to saved snapshot:

```python
#Skip doctest because timestamp will change
>>> print(zip_path)# doctest:+SKIP
```

Clean up the snapshot
```python
>>> shutil.rmtree(dataset_path)

```

Automatically take snapshots when change is detected in measurement.zip

```python
>>> os.mkdir(dataset_path)
>>> dummy_reader.start_write(dataset_path)
>>> for i in range(20):
...    dummy_writer.writer_worker(i)
...    sleep(0.01)
>>> dummy_reader.stop_watchdog()

```

Check the number of snapshots taken

```python
>>> zip_list = os.listdir(dataset_path)
>>> len(zip_list)
20

```

Check the content of dataset. Files are sorted because os.listdir doesn't quarantee any order

```python
>>> zip_files = sorted(os.listdir(dataset_path))
>>> for file in zip_files:
...    print (read(os.path.join(dataset_path, file)))
{'number': 0, 'number_x2': 0}
{'number': 1, 'number_x2': 2}
{'number': 2, 'number_x2': 4}
{'number': 3, 'number_x2': 6}
{'number': 4, 'number_x2': 8}
{'number': 5, 'number_x2': 10}
{'number': 6, 'number_x2': 12}
{'number': 7, 'number_x2': 14}
{'number': 8, 'number_x2': 16}
{'number': 9, 'number_x2': 18}
{'number': 10, 'number_x2': 20}
{'number': 11, 'number_x2': 22}
{'number': 12, 'number_x2': 24}
{'number': 13, 'number_x2': 26}
{'number': 14, 'number_x2': 28}
{'number': 15, 'number_x2': 30}
{'number': 16, 'number_x2': 32}
{'number': 17, 'number_x2': 34}
{'number': 18, 'number_x2': 36}
{'number': 19, 'number_x2': 38}

```
Remove the created dataset

```
>>> shutil.rmtree(dataset_path)

```


---


## Features Demonstrated
- **Dynamic updates**: Reader reflects changes made by Writer.
- **Watchdog**: Reacts to attribute changes in near real-time.
- **Snapshots & datasets**: Save and read sensor states.
