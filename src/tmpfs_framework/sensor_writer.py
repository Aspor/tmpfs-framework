#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 11:30:43 2021

@author: aspor
"""
import os
import zipfile
import shutil

from typing import Any
from threading import Event
from pathlib import Path

from .cbor_utils import write_cbor, get_temp_file
import tmpfs_framework

import logging

class SensorWriter():
    """
    A class to handle writing sensor data to files and compressing them.

    Attributes:
    tmpfs_path (str): Temporary file system path.
    data_path (str): Path to the directory where data is stored.
    filename (str): Name of the file or directory.
    stop_event (Event): Event to control stopping of write loop.
    """
    def __init__(self, dir_path: str, filename: str, tmpfs_path=None) -> None:
        """
        Initializes SensorWriter with directory path and filename.

        Args:
        dir_path (str): Directory path for storing data.
        filename (str): Name of the file or directory.
        """
        self.tmpfs_path = tmpfs_path if tmpfs_path is not None else tmpfs_framework.TMPFS_PATH
        d = os.path.join(self.tmpfs_path,dir_path)
        os.makedirs(d,exist_ok=True)
        self.data_path =os.path.join(d,filename)
        Path(self.data_path).mkdir(parents=True,exist_ok=True)

        self.filename=filename
        self.stop_event=Event()


    def start(self) -> None:
        """
        Placeholder method for necessary setup for the sensors.
        """
        pass

    def stop(self) -> None:
        """
        Sets the stop event to signal stopping of the write loop.
        """
        self.stop_event.set()

    def _write_loop(self, wait: float = None) -> None:
        """
        Placeholder method for the write loop.

        Args:
        wait (float, optional): Time to wait between writes.
        """
        self.stop_event.clear()
        pass

    def write(self,name: str, data: Any, attributes: dict = None) ->None:
        """
        Writes data to a file. Supports nested dictionaries.

        Args:
        name (str): Name of the file or directory.
        data (any): Data to be written.
        attributes (dict, optional): Attributes to be written.
        """

        if type (data) is dict:
            for d in data:
                self.write(name = os.path.join(name,str(d)), data = data[d])
        else:
            write_cbor(filename = os.path.join(self.data_path, name), data = data)

        if attributes is not None:
            self.write(name+"_attr", attributes)

    def write_zip(self, name:str, data: Any, compress: bool = False, keep: bool = False) -> None:
        """
        Writes data and compresses it into a zip file.

        Args:
        name (str): Name of the directory.
        data (any): Data to be written.
        compress (bool): Whether to compress the zip file.
        keep (bool): Whether to keep the original files.
        """
        self.write(name, data)
        final_path=os.path.join(self.data_path, name)

        compression=zipfile.ZIP_DEFLATED
        if(not compress):
            compression=zipfile.ZIP_STORED
        tmpF=get_temp_file()
        with zipfile.ZipFile(f'{tmpF}.zip' ,'w' ,compression=compression ,compresslevel=3) as zf:
                    for root, _, files in os.walk(final_path):
                        for file in files:
                            fn=Path(root, file)
                            afn=fn.relative_to(self.data_path)
                            zf.write(filename=fn, arcname=afn)
                        # shutil.copy2(f'{self.data_path}/{f}',f'{p}/{f}')
        if not keep:
            shutil.rmtree(final_path, ignore_errors=True)
        os.rename(f'{tmpF}.zip',f'{final_path}.zip')



def pack_to_zip(files: list[str], base_dir:str = ".", zipname:str = "measurement",
                compress:bool = False) -> None:
        """
        Packs a list of files into a zip archive.

        Args:
        files (list): List of file paths to include in the zip.
        base_dir (str): Base directory for relative paths.
        zipname (str): Name of the output zip file.
        compress (bool): Whether to compress the zip file.
        """
        root = base_dir#os.path.dirname(zipname)
        path = zipname

        compression=zipfile.ZIP_DEFLATED
        if(not compress):
            compression=zipfile.ZIP_STORED

        tmpF=get_temp_file()
        with zipfile.ZipFile(f'{tmpF}.zip','w',compression=compression,compresslevel=3) as z:
            for file in files:
                            fn=Path(root, file)
                            afn=file
                            z.write(filename=fn,arcname=afn)
        path = os.path.join(root,path)

        os.rename(f'{tmpF}.zip',f'{path}.zip')
