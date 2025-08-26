# Examples

## Network monitoring

Demostrates how to implement a thread based writer and reader object with device available to most users

Requirements: matplotlib

**networkLogger.py** reads statistics from files /proc/net/, parses them and writes corresponding data to tmpfs path set by the user.
**networkPlotter.py** reads the same data from tmpfs path, prints current values and start drawing a plot of total transmitted bytes using matplotlib. Shows three different ways to acces the data on tmpfs:
1. By calling get_value()
2. By calling \_\_get_attribute\_\_()
3. By directly accessing with object.variable
