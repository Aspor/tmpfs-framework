import os
from time import sleep

import tmpfs_framework
from tmpfs_framework import SensorReader

class NetworkStatsReader(SensorReader):
  def __init__ (self, directory='network_stats', name=None, *args,**kwargs):
    if(name is None or type(name) is int ):
      if(name is None):
        name=-1
      files =os.listdir(f'{tmpfs_framework.TMPFS_PATH}/{directory}')
      name = files[name]

    super().__init__(directory=directory,filename=name,*args,**kwargs)
    self.to_watch = "wireless_status"

if __name__=="__main__":
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from collections import deque
    import sys

    inteface = sys.argv[1] if len(sys.argv)>1 else None

    plotter = NetworkStatsReader(sensorName="network_stats", name=inteface)

    #Read and print current values
    for v in plotter.attributes:
        print(f"{v}: ")
        print( plotter.get_value(v))
        #It's also possible to use __getattribute__:
        print(plotter.__getattribute__(v))

    plot_lenght=25
    y = deque(maxlen=plot_lenght)
    x = deque(maxlen=plot_lenght)

    def updateGraph(frame ):
        #Variables raed from tmpfs can be read normally:
        y.append(plotter.transmit_bytes)
        x.append(frame)
        plt.clf()
        return plt.plot(x,y)

    ani = animation.FuncAnimation(plt.figure("transmit_bytes"), updateGraph, interval=250)
    plt.show()
