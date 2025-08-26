# tmpfs-framework
Python implementation of "A tmpfs Based Middleware For Robotics Applications"

Allows one way communication between two separate python process via Linux's tmpfs. Future implemantion will add two way communication.

Requiremets:

* cbor2>=5.4.6
* numpy>=1.21.5
* watchdog>=2.1.6
* L

## Build and install using pythons build module and pip:
Requiremets:
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


### tmpfs

Create a tmpfs to use:

        mount -t tmpfs tmpfs   /path/to/tmpfs/

See
https://www.kernel.org/doc/html/latest/filesystems/tmpfs.html for more details how to create a tmpfs


## CITING
If you use this work in your research please cite the following paper:

`Mäenpää, T., Tikanmäki, A., Röning, J. (2025). A tmpfs-Based Middleware for Robotics Applications. In: Arai, K. (eds) Intelligent Systems and Applications. IntelliSys 2025. Lecture Notes in Networks and Systems, vol 1567. Springer, Cham. https://doi.org/10.1007/978-3-032-00071-2_35`
