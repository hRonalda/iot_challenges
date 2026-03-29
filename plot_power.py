import pandas as pd
import matplotlib.pyplot as plt

files = ["deep_sleep.csv", "sender.csv", "sensor-read.csv"]

for file in files:
    df = pd.read_csv(file)

    # 自动处理 Data 列
    df["Data"] = pd.to_numeric(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])

    plt.figure(figsize=(10,4))
    plt.plot(df["Data"])
    plt.title(file)
    plt.xlabel("Sample Index")
    plt.ylabel("Power (mW)")
    plt.grid()

plt.show()