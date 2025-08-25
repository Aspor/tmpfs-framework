# tmpfs-framework
Python implementation of "A tmpfs Based Middleware For Robotics Applications"

Requiremets:

* cbor2>=5.4.6
* numpy>=1.21.5
* watchdog>=2.1.6


## Build and install using pythons build module and pip:

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
See
https://www.kernel.org/doc/html/latest/filesystems/tmpfs.html for details how to create a tmpfs
