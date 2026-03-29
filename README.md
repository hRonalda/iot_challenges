# IoT Challenge 1 – ESP32 Motion and Light Sensor Node

This repository contains the implementation, measurements, analysis scripts, and report material for **IoT Challenge 1**.

## Author

**Rong Huang**  
Personal Code: **10948935**

## Project Overview

The goal of this project is to design a commercial-style IoT sensor node using an **ESP32** in the **Wokwi simulator**.  
The node:

- detects human motion using a **PIR sensor**
- measures ambient light using an **LDR sensor**
- sends the sensed information to a sink node using **ESP-NOW**
- enters **deep sleep** after transmission to reduce energy consumption

The transmitted message has the form:

- `MOTION_DETECTED-LUMINOSITY:ZZZ`
- `MOTION_NOT_DETECTED-LUMINOSITY:ZZZ`


## Key Calculated Results

### Assigned power values
- BOOT: **237.05 mW**
- SENSOR READ: **351.09 mW**
- MESSAGE BUILD: **237.05 mW**
- WIFI ON: **632.04 mW**
- TRANSMISSION: **667.41 mW**
- WIFI OFF: **252.22 mW**
- DEEP SLEEP: **45.78 mW**

### Final timing values
- SENSOR READ: **0.929 ms**
- MESSAGE BUILD: **0.263 ms**
- TRANSMISSION: **0.482 ms**
- WIFI ON: **191.388 ms**
- WIFI OFF: **9.440 ms**
- ACTIVE without BOOT: **202.502 ms**
- Estimated BOOT: **150.343 ms**
- TOTAL ACTIVE: **352.845 ms**
- DEEP SLEEP: **4000.000 ms**
- CYCLE PERIOD: **4352.845 ms**

### Final energy results
- Energy per cycle: **342.81 mJ**
- Average power: **78.75 mW**
- Battery lifetime: **66.79 hours ≈ 2.78 days**
- Supported cycles: **55234**
## Repository Structure



```text
Challenge1/
├── README.md
├── report/
│   ├── main.tex
│   └── hardware_setup.png
├── data/
│   ├── deep_sleep.csv
│   ├── sensor-read.csv
│   └── sender.csv
├── scripts/
│   ├── group.py
│   └── plot_power.py
├── results/
│   └── csv_analysis_results.txt
└── refs/
    └── Challenge1.pdf
