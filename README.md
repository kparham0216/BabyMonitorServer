# BabyMonitorServer

A FastAPI-based REST server that runs on a Raspberry Pi and continuously collects heart rate (BPM), blood oxygen saturation (SpO2), and body temperature readings from an I2C-connected sensor. Processed data is served over HTTP in rolling time-window aggregations for real-time monitoring and historical trending.

---

## Table of Contents

- [Overview](#overview)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
  - [Data Collection](#data-collection)
  - [Rolling Windows](#rolling-windows)
  - [API Endpoints](#api-endpoints)
- [Running the Server](#running-the-server)
- [Utilities](#utilities)
  - [Sensor Test Script](#sensor-test-script)
  - [Temperature Accuracy Plotter](#temperature-accuracy-plotter)
- [API Reference](#api-reference)

---

## Overview

This server is the backend component of a baby monitor system. It interfaces with a sensor module (connected via I2C) to read vital signs at regular intervals and exposes the data through a lightweight REST API. A companion mobile or web application can poll these endpoints to display live readings and historical trends.

---

## Hardware Requirements

| Component | Details |
|---|---|
| Single-board computer | Raspberry Pi (any model with I2C support) |
| Sensor module | I2C device at address `0x42` (custom microcontroller or compatible pulse oximeter/thermometer board) |
| Connection | I2C bus 1 (SDA/SCL on GPIO pins 2/3) |

**Sensor data layout (11-byte I2C read from register 0):**

| Bytes | Field |
|---|---|
| `[0:2]` | BPM (24-bit big-endian) |
| `[3:5]` | IR raw value (24-bit big-endian) |
| `[8:9]` | Temperature (16-bit big-endian, raw) |
| `[10]` | SpO2 (%) |

---

## Software Requirements

- Python 3.8+
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/) (ASGI server)
- [smbus2](https://pypi.org/project/smbus2/) (I2C communication)
- [matplotlib](https://matplotlib.org/) (plotter utility only)

Install dependencies:

```bash
pip install fastapi uvicorn smbus2 matplotlib
```

---

## Project Structure

```
BabyMonitorServer/
├── server.py       # Main FastAPI server — data collection & REST API
├── test2.py        # Standalone I2C sensor read test
├── plotter.py      # Temperature accuracy visualization utility
└── output.csv      # Sample data file used by plotter.py
```

---

## How It Works

### Data Collection

A background thread (`collect_data`) starts at server launch and polls the I2C sensor every **11 seconds**. Each reading is parsed into:

- **BPM** — heart rate in beats per minute
- **SpO2** — blood oxygen saturation percentage
- **Temp** — temperature converted to °F using the formula:
  $$T_F = \left(\text{raw} \times 9 \times 0.00078125\right) + 32$$

The most recent reading is always stored in `latest_data` and accessible via `/latest_data`.

### Rolling Windows

Data is maintained in four rolling window buffers. Each window holds a fixed maximum of **360 samples** and older entries are discarded as new ones arrive:

| Endpoint | Window | Sample Interval | Max Samples | Coverage |
|---|---|---|---|---|
| `/one_hr_data` | 1-hour | Every reading (~11s) | 360 | ~1.1 hours |
| `/six_hr_data` | 6-hour | Average of every 6 readings | 360 | ~6.6 hours |
| `/twelve_hr_data` | 12-hour | Average of every 12 readings | 360 | ~13.2 hours |
| `/twenty_four_hr_data` | 24-hour | Average of every 24 readings | 360 | ~26.4 hours |

The 6-, 12-, and 24-hour buffers store **averaged** values, smoothing out short-term noise. The internal sample counter wraps at **8,640** (360 × 24) to prevent overflow.

### API Endpoints

All responses are JSON. Data arrays are ordered chronologically (oldest → newest).

---

## Running the Server

Enable I2C on the Raspberry Pi if not already done:

```bash
sudo raspi-config
# Interface Options → I2C → Enable
```

Start the server:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

The server will begin collecting sensor data immediately on startup. Access the interactive API docs at:

```
http://<raspberry-pi-ip>:8000/docs
```

---

## Utilities

### Sensor Test Script

`test2.py` is a minimal standalone script for verifying that the I2C sensor is wired correctly and returning valid data. It reads and prints BPM, SpO2, and temperature every 11 seconds in a loop.

```bash
python test2.py
```

Use this to confirm sensor connectivity before running the full server.

### Temperature Accuracy Plotter

`plotter.py` reads two rows of temperature data from `output.csv` and renders a comparison chart of observed vs. control (reference) temperatures over time.

```bash
python plotter.py
```

`output.csv` format (two rows, comma-separated floats):

```
<observed_temp_1>,<observed_temp_2>,...
<control_temp_1>,<control_temp_2>,...
```

---

## API Reference

### `GET /latest_data`

Returns the single most recent sensor reading.

**Response:**
```json
{
  "bpm": 72,
  "spo2": 98,
  "temp": 98.4,
  "timestamp": null
}
```

---

### `GET /one_hr_data`

Returns up to 360 raw readings covering approximately the last hour.

**Response:**
```json
{
  "bpm":  [71, 72, 73, ...],
  "spo2": [97, 98, 98, ...],
  "temp": [98.3, 98.4, 98.5, ...]
}
```

---

### `GET /six_hr_data`

Returns up to 360 averaged readings (averaged over each 6-reading block) covering approximately the last 6 hours.

---

### `GET /twelve_hr_data`

Returns up to 360 averaged readings (averaged over each 12-reading block) covering approximately the last 12 hours.

---

### `GET /twenty_four_hr_data`

Returns up to 360 averaged readings (averaged over each 24-reading block) covering approximately the last 24 hours.
