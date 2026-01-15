
# tmpfs-framework

[![Unit tests](https://github.com/Aspor/tmpfs-framework/actions/workflows/python-app.yml/badge.svg?branch=master)](https://github.com/Aspor/tmpfs-framework/actions/workflows/python-app.yml)



A lightweight IPC (Interprocess Communication) framework for Linux using **tmpfs** and **CBOR**. Designed for modular robotics and distributed Python systems, it enables simple, fast, one‑way communication between processes. Two‑way communication is planned for future releases.

---

## Overview

Robotic systems often consist of multiple subsystems—sensors, planners, controllers—running independently. Packing everything into a single monolithic program quickly becomes difficult to maintain and scale. A better architecture is to split functionality into separate processes connected by a simple communication layer.

The **tmpfs-framework** provides such a layer using:

- **tmpfs** — in‑memory temporary file storage on Linux
- **CBOR serialization** — compact, self‑describing binary messages
- **File‑based IPC** — easy to inspect, debug, and extend

This approach offers a transparent and flexible communication mechanism without complex middleware or strict message schemas.

---

## Features

- **Simple setup** — no background services or daemons
- **Portable** — runs on most Linux distributions
- **Supports arrays and images** through CBOR
- **Lightweight** — minimal dependencies
- **Publish‑and‑forget** semantics
- **Human‑readable file structure** inside tmpfs

>  While not ideal for hard real‑time systems, tmpfs‑based IPC performs well where modularity, clarity, and extensibility are priorities.

---

## Requirements

- `cbor2 >= 5.4.6`
- `numpy >= 1.21.5`
- `watchdog >= 2.1.6`
- Linux
- (For building) `hatchling`

---

## Installation

Build using Python’s build system and install with pip:

```bash
python3 -m build
python3 -m pip install dist/tmpfs_framework-0.0.1-py3-none-any.whl
```

---

## Configuration

Default tmpfs path:

```
/home/robot/tmp/
```

Override it in Python:

```python
import tmpfs_framework
tmpfs_framework.TMPFS_PATH = "/path/to/tmpfs"
```

Or via environment variable:

```bash
export TMPFS_PATH=/path/to/tmpfs
```

---

##  Setting Up a tmpfs

Create a tmpfs directory:

```bash
sudo mount -t tmpfs tmpfs /path/to/tmpfs/
```

More details:
https://www.kernel.org/doc/html/latest/filesystems/tmpfs.html

---

##  Examples

The `examples/` directory includes:

#### 1. **Guided Example**
A step‑by‑step walkthrough demonstrating dummy sensors and framework features.

#### 2. **Webcam Example**
Uses real hardware to show image acquisition and processing.

#### 3. **Network Monitoring**
Works on most machines without additional hardware

---

##  Contributing

Contributions are welcome!

- Found a bug? Open an **issue**.
- Added an improvement? Create a **pull request**.

---

## Citation

If you use this framework in research, please cite:

```
Mäenpää, T., Tikanmäki, A., Röning, J. (2025).
A tmpfs-Based Middleware for Robotics Applications.
In: Arai, K. (eds) Intelligent Systems and Applications. IntelliSys 2025.
Lecture Notes in Networks and Systems, vol 1567. Springer, Cham.
https://doi.org/10.1007/978-3-032-00071-2_35
```

---
