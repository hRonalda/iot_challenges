# IoT Challenge 1 – ESP32 Motion & Light Sensor Node (ESP-NOW)

This repository contains the implementation, measurements, analysis scripts, plots, and the final report for **IoT Challenge 1**.

## Author
**Rong Huang**  
Personal Code: **10948935**

## Project Overview
A commercial-style IoT sensor node was implemented in the **Wokwi** simulator using an **ESP32**. The node:

- detects motion with a **PIR** sensor (digital)
- measures ambient light with an **LDR** sensor (analog → lux approximation)
- transmits updates to a sink node using **ESP-NOW**
- follows a duty-cycled operation with low-power sleep/idle between cycles

Baseline transmission message format:
- `MOTION_DETECTED-LUMINOSITY:ZZZ`
- `MOTION_NOT_DETECTED-LUMINOSITY:ZZZ`

Improved version message format (send-on-change):
- `MOTION_...-LEVEL:X-LUX:ZZZ`

## Key Results (Baseline)
State power mapping (from CSV traces):
- BOOT: **237.05 mW**
- SENSOR READ: **351.09 mW**
- MESSAGE BUILD: **237.05 mW**
- WIFI ON: **632.04 mW**
- TRANSMISSION: **667.41 mW**
- WIFI OFF: **252.22 mW**
- DEEP SLEEP: **45.78 mW**

Final timing values:
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

Energy estimation:
- Energy per cycle: **342.81 mJ**
- Average power: **78.75 mW**
- Estimated lifetime: **66.79 hours ≈ 2.78 days**
- Supported cycles: **55234**

## Improvements (Send-on-change)
To reduce unnecessary radio activations, an improved design transmits **only when**:
- the PIR motion state changes, or
- the light **category** changes (lux quantized into 5 levels)

Evidence and artifacts:
- Plots for baseline vs improved energy/power are in `result/improvedPlots/`
- Full 16-cycle serial output for the improved run is in `result/serial_output_improved.txt`

How to Reproduce Plots:
- Run the plotting script (PNG output enabled in the script): `python scripts/improved_power_time.py`
- Figures will be written under `result/improvedPlots/`.

## Repository Structure
```text
Challenge1/
├── Challenge.pdf                      # Final report (PDF)
├── README.md
├── github_link.txt                    # Link to submission/repo (if needed)
├── data/                              # Provided traces
│   ├── deep_sleep.csv
│   ├── sender.csv
│   └── sensor-read.csv
├── refs/
│   └── Challenge1.pdf                 # Assignment reference (slides/pdf)
├── result/
│   ├── csv_analysis_results.txt       # Power mapping results from CSV analysis
│   ├── serial_output_improved.txt     # 16-cycle serial logs (improved)
│   └── improvedPlots/                 # Generated figures (PNG)
│       ├── fig_baseline_power.png
│       ├── fig_after_power.png
│       ├── fig_baseline_cum_energy_128s.png
│       ├── fig_after_cum_energy_128s.png
│       └── fig_cum_energy_comparison_128s.png
├── scripts/
│   ├── basic_calculate_group.py       # CSV state/power extraction utilities
│   ├── basic_calculate_plot_power.py  # Plotting utilities
│   └── improved_power_time.py         # Baseline vs improved plots (PNG export)
└── wokwi_code/
    ├── iot_improved.zip               # Wokwi export (improved)
    └── test_iot_basic_calculate.zip   # Wokwi export (baseline/other)
