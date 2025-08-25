#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import threading

from time import sleep

from tmpfs_framework import SensorWriter



class wifiLogger(SensorWriter):

    def __init__(self, dirPath='wifilogger', filename='.', **kwargs):
        super().__init__(dirPath,filename)

        #Hard coded fields because parsing /proc/net/ file header is split to two lines
        #making parsing it challenging
        self.wireless_fields=("name", "wireless_status", "wireless_link", "wireless_level",
                              "wireless_noise", "wireless_nwid", "wireless_crypt", "wireless_frag",
                              "wireless_retry", "wireless_misc", "wireless_missedbeacon",
                              "wireless_WE")
        self.dev_fields=("name", "receive_bytes","receive_packets", "receive_errs",
                         "receive_drop", "receive_fifo", "receive_frame",
                         "receive_compressed", "receive_multicast",
                         "transmit_bytes", "transmit_packets", "transmit_errs",
                         "transmit_drop", "transmit_fifo", "transmit_colls",
                         "transmit_carrier", "transmit_compressed")

        self.workerThread = threading.Thread(target=self.writeWorker, daemon=False)

    def writeWorker(self):
        """Read network interfaces information from /proc/ file and write them in /tmpfs/
        """
        running =True
        while running:
            try:
                wireless = parse_file("/proc/net/wireless",self.wireless_fields)
                netdev = parse_file("/proc/net/dev",self.dev_fields)
            except Exception as e:
                    print(e)
                    running=False
            else:
                for key in netdev:
                    if key in wireless:
                        netdev[key].update(wireless[key])
                self.write(".",netdev)
                sleep(0.05)

def parse_file(filename,fieldnames, wireless=False):
  """Parses /proc/net/ file in given path. Assumes that fieldnames correspond to actual
  fields

  Arguments:
      filename -- Path to /proc/net/file where info about net devices can be read
      fieldnames -- Fieldnames found in file header

  Returns:
      Dictionary of values. Keys are fieldnames and values are read from file
  """
  lines=[]
  data_dict={}
  with open (filename, 'r') as net_file:
      line = net_file.readline()

      while(line):
          lines.append(line)
          line = net_file.readline()
      #First two lines are for the header
      interfaces = lines[2:]
      for interface in interfaces:
          info = interface.split()
          info[0] = info[0].strip(": ") #interface name
          #cast numbers to float
          for i,item in enumerate(info):
              try:
                  info[i] = float(item)
              except:
                  pass

          info_dict = dict(zip(fieldnames,info))
          if wireless:
            ssid=os.popen(f"iwgetid -r {info[0]}").read()
            info_dict['ssid'] = ssid.strip()
          data_dict[info[0]] = info_dict
  return data_dict

if __name__=="__main__":
    logger = wifiLogger()
    logger.workerThread.start()
    logger.workerThread.join()
