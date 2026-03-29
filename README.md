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
