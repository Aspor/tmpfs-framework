[![Unit tests](https://github.com/Aspor/tmpfs-framework/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/Aspor/tmpfs-framework/actions/workflows/python-app.yml)

Allows one way communication between two separate python process via Linux's tmpfs. Future implantation will add two way communication.

Robots need to handle tasks like sensing the environment, planning actions, and controlling movement. Doing all this in one big program makes things complicated and hard to change. A better way is to split the system into smaller parts that talk to each other using interprocess communication (IPC).

The tmpfs framework is a simple IPC solution for Linux. It uses temporary files in memory (tmpfs) to share data between programs. Data is stored in files with clear names, and  Concise Binary Object Representation (CBOR) is used for efficient binary serialization, including support for arrays and images. The framework is lightweight, works on most Linux systems, and makes it easy to add new sensors or actuators without rigid message formats.


Why it’s useful:

- Easy to set up
- Portable across Linux
- Self-describing data
- Supports “publish and forget” communication

While not necessary suitable for hard real-time applications, tmpfs-based IPC can perform well in scenarios requiring modularity, transparency, and ease of integration.


## Requirements:

* cbor2>=5.4.6
* numpy>=1.21.5
* watchdog>=2.1.6
* Linux

## Build and install using pythons build module and pip:
Requirements:
* hatchling

        python3 -m build
        python3 -m pip install dist/tmpfs_framework-0.0.1-py3-none-any.whl

## Usage
In example directory there are some example code showcasing usage.


Default tmpfs path is set to /home/robot/tmp/ this can be changed by setting TMPFS_PATH variable in tmpfs_framework module
```
import tmpfs_framework
TMPFS_PATH = "/path/to/tmpfs"
```
or by setting TMPFS_PATH environment variable in shell:
```
$export  TMPFS_PATH=/path/to/tmpfs
```

### tmpfs

Create a tmpfs to use:

        mount -t tmpfs tmpfs   /path/to/tmpfs/

See
https://www.kernel.org/doc/html/latest/filesystems/tmpfs.html for more details how to create a tmpfs



## Contributing

If you found a bug or want a new feature feel free to open a issue in this GitHub repository.

Or if you improve the framework and want to share you can create a pull request


## Citing
If you use this work in your research please cite the following paper:

`Mäenpää, T., Tikanmäki, A., Röning, J. (2025). A tmpfs-Based Middleware for Robotics Applications. In: Arai, K. (eds) Intelligent Systems and Applications. IntelliSys 2025. Lecture Notes in Networks and Systems, vol 1567. Springer, Cham. https://doi.org/10.1007/978-3-032-00071-2_35`
