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

## System States

The energy model is based on the following operating states:

1. BOOT  
2. SENSOR READ  
3. MESSAGE BUILD  
4. WIFI ON  
5. TRANSMISSION  
6. WIFI OFF  
7. DEEP SLEEP  

The code directly measures:

- SENSOR READ
- MESSAGE BUILD
- WIFI ON
- TRANSMISSION
- WIFI OFF

The **BOOT** duration is not directly taken from the simulator timing, but is estimated from the transient observed in `deep_sleep.csv`.

## Measurement and Analysis Workflow

### 1. Wokwi node implementation
The ESP32 node was implemented in Wokwi with:

- PIR sensor connected to **GPIO 13**
- LDR analog output connected to **GPIO 34**

### 2. Timing measurement
The code measures the directly observable execution times using `micros()`.

### 3. Power extraction from CSV traces
The provided CSV traces are used as reference power profiles.  
The script `group.py` extracts stable regions from the traces and maps them to the final node states.

### 4. Energy estimation
The per-state energy is computed as:

\[
E_i = P_i \cdot T_i
\]

and the cycle energy is obtained by summing all state contributions.

## Final Reference Values

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

## Notes

- The simulator does not realistically reproduce the actual hardware wake-up latency of a real ESP32 board.  
  For this reason, the BOOT duration is estimated from the timestamped transient in `deep_sleep.csv`.

- Timing outliers were removed before averaging.  
  Warm-up runs were also excluded from the final timing statistics.

