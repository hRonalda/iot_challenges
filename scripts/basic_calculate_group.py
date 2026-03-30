import pandas as pd

# 1. Read CSV files
deep_df = pd.read_csv("../data/deep_sleep.csv")
sensor_df = pd.read_csv("../data/sensor-read.csv")
sender_df = pd.read_csv("../data/sender.csv")


# 2. Convert Data column to numeric
deep_df["Data"] = pd.to_numeric(deep_df["Data"], errors="coerce")
sensor_df["Data"] = pd.to_numeric(sensor_df["Data"], errors="coerce")
sender_df["Data"] = pd.to_numeric(sender_df["Data"], errors="coerce")
# Remove invalid values
deep_df = deep_df.dropna(subset=["Data"])
sensor_df = sensor_df.dropna(subset=["Data"])
sender_df = sender_df.dropna(subset=["Data"])


# 3. Extract states by thresholds
# deep_sleep.csv 
deep_sleep_state = deep_df[deep_df["Data"] < 100]
wifi_off_state   = deep_df[(deep_df["Data"] > 200) & (deep_df["Data"] < 300)]
wifi_on_state    = deep_df[deep_df["Data"] > 500]

# sensor-read.csv
local_state      = sensor_df[sensor_df["Data"] < 260]
sensor_read_state = sensor_df[sensor_df["Data"] > 330]

# sender.csv
sender_base_state = sender_df[sender_df["Data"] < 620]
tx_state          = sender_df[sender_df["Data"] > 640]


# 4. Compute mean power of each state
P_DEEP_SLEEP  = deep_sleep_state["Data"].mean()
P_WIFI_OFF    = wifi_off_state["Data"].mean()
P_WIFI_ON     = wifi_on_state["Data"].mean()

P_LOCAL       = local_state["Data"].mean()
P_SENSOR_READ = sensor_read_state["Data"].mean()

P_TX_BASE     = sender_base_state["Data"].mean()
P_TX          = tx_state["Data"].mean()


# 5. Recommended mapping for the challenge
P_BOOT = P_LOCAL
P_MESSAGE_BUILD = P_LOCAL
P_TRANSMISSION = P_TX


# 6. Save output in the text file
results_text = f"""===== Average Power of Extracted States =====
P_DEEP_SLEEP   = {P_DEEP_SLEEP:.2f} mW
P_WIFI_OFF     = {P_WIFI_OFF:.2f} mW
P_WIFI_ON      = {P_WIFI_ON:.2f} mW
P_LOCAL        = {P_LOCAL:.2f} mW
P_SENSOR_READ  = {P_SENSOR_READ:.2f} mW
P_TX_BASE      = {P_TX_BASE:.2f} mW
P_TX           = {P_TX:.2f} mW

===== Recommended Mapping =====
P_BOOT          = {P_BOOT:.2f} mW
P_SENSOR_READ   = {P_SENSOR_READ:.2f} mW
P_MESSAGE_BUILD = {P_MESSAGE_BUILD:.2f} mW
P_WIFI_ON       = {P_WIFI_ON:.2f} mW
P_TRANSMISSION  = {P_TRANSMISSION:.2f} mW
P_WIFI_OFF      = {P_WIFI_OFF:.2f} mW
P_DEEP_SLEEP    = {P_DEEP_SLEEP:.2f} mW

===== Number of Samples in Each State =====
deep_sleep_state:   {len(deep_sleep_state)}
wifi_off_state:     {len(wifi_off_state)}
wifi_on_state:      {len(wifi_on_state)}
local_state:        {len(local_state)}
sensor_read_state:  {len(sensor_read_state)}
sender_base_state:  {len(sender_base_state)}
tx_state:           {len(tx_state)}
"""

with open("../results/csv_analysis_results.txt", "w", encoding="utf-8") as f:
    f.write(results_text)

print("\nResults saved to csv_analysis_results.txt")