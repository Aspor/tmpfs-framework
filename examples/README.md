# Examples


## Guided example

Walks through creating a dummy sensor writer and demonstrates some basic concepts and features

## Webcam example

1. Example with sensor that is easy to acquire and give a starting point for adding new types of sensors.
2. Give idea of latency in tmpfs-framework
   - Images are written to tmpfs and later read from there for shape detection this causes delay that can be seen by moving detected objects or webcam
3. Demonstrates idea of having data processing module that generates new data from existing.
    - This allows implementing a whiteboard system where some processes provide raw data and other processes process the data to generate additional information




## Network monitoring

Demonstrates how to implement a thread based writer and reader object with device available to most users
