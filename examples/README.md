# Examples


## Guided example

Walks through creating a dummy sensor writer and demostrates some basic consepts and features

## Webcam example

1. Example with seansor that is easy to aquire and give a starting point for adding new types of sensors.
2. Give idea of latency in tmpfs-framework
   - Images are written to tmpfs and later read from there for shape detection this causes delay that can be seen by moving detected objects or webcam
3. Demotrates idea of having data processing module that generates new data from existing.
    - This allows implementing a whiteboard system where some processes provide raw data and other processes process the data to generate aditional information




## Network monitoring

Demostrates how to implement a thread based writer and reader object with device available to most users
