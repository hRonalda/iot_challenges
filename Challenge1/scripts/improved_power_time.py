import os
os.makedirs("../result/improvedPlots", exist_ok=True)

import numpy as np
import matplotlib.pyplot as plt

# Power vs Time / Energy vs Time plots for IoT Challenge 1
# - Baseline: fixed 5-cycle model (always transmits)
# - After: SEND/SKIP cycles (send-on-change)
# - Includes fair cumulative-energy comparison over SAME total time


# User parameters
DT_MS = 1.0           # time resolution for step construction (ms)
N_SHOW = 5            # how many cycles to show in the Power-vs-Time plots
SHOW_START = 3        # start index for AFTER power plot window (0-based). Use 0 if you want from the beginning.
SAVE_FIGS = True     # set True to save figures as PNG
OUT_PREFIX = "fig" # output filename prefix if SAVE_FIGS=True


# 1. Power mapping (mW) from Table: state_power_mapping

P = {
    "BOOT": 237.05,
    "SENSOR": 351.09,
    "MSG": 237.05,
    "WIFI_ON": 632.04,
    "TX": 667.41,
    "WIFI_OFF": 252.22,
    "SLEEP": 45.78,
}

# 2) Baseline timing (ms) (always transmits)
baseline_cycle = [
    ("BOOT", 150.343),
    ("SENSOR", 0.929),
    ("MSG", 0.263),
    ("WIFI_ON", 191.388),
    ("TX", 0.482),
    ("WIFI_OFF", 9.440),
    ("SLEEP", 4000.000),
]
 
# 3) After timing (ms)
# Representative SEND (Run 8) and SKIP (Run 6)
send_cycle = [
    ("BOOT", 150.343),
    ("SENSOR", 0.930),
    ("MSG", 0.498),
    ("WIFI_ON", 29.790),
    ("TX", 0.567),
    ("WIFI_OFF", 8.618),
    ("SLEEP", 8000.000),
]

skip_cycle = [
    ("BOOT", 150.343),
    ("SENSOR", 0.911),
    ("SLEEP", 8000.000),
]

# 16-cycle pattern from the serial log
after_pattern = [
    "SEND", "SEND", "SEND", "SEND",
    "SKIP", "SKIP", "SKIP",
    "SEND",
    "SKIP", "SKIP", "SKIP", "SKIP",
    "SEND",
    "SKIP", "SKIP",
    "SEND",
]

# Helpers: build piecewise-constant power timeline
def build_timeline(cycles, dt_ms=1.0):
    """Build piecewise-constant power signal and cumulative energy.

    cycles: list of cycles, each cycle is list[(state, duration_ms)]
    dt_ms: discretization step for constructing the step signal

    Returns:
      t: array of time points in ms (length N+1)
      p: array of power values in mW (length N)
      e_cum: array of cumulative energy in mJ (length N+1)
    """
    t_list = [0.0]
    p_list = []
    e_list = [0.0]

    current_t = 0.0
    current_e = 0.0

    for cycle in cycles:
        for state, dur_ms in cycle:
            if dur_ms <= 0:
                continue

            n = max(1, int(np.ceil(dur_ms / dt_ms)))
            step = dur_ms / n  # end exactly at dur_ms

            power_mw = P[state]
            for _ in range(n):
                p_list.append(power_mw)
                current_t += step
                current_e += power_mw * step / 1000.0  # mW*ms/1000 = mJ
                t_list.append(current_t)
                e_list.append(current_e)

    return np.array(t_list), np.array(p_list), np.array(e_list)


def plot_power(t, p, title):
    fig = plt.figure()
    plt.step(t[:-1], p, where="post")
    plt.xlabel("Time (ms)")
    plt.ylabel("Power (mW)")
    plt.title(title)
    plt.tight_layout()
    return fig


def plot_energy(t, e_cum, title):
    fig = plt.figure()
    plt.plot(t, e_cum)
    plt.xlabel("Time (ms)")
    plt.ylabel("Cumulative Energy (mJ)")
    plt.title(title)
    plt.tight_layout()
    return fig


def save_fig(fig, name):
    if not SAVE_FIGS:
        return
    # fig.savefig(f"{OUT_PREFIX}_{name}.png", dpi=200)
    fig.savefig(f"../result/improvedPlots/{OUT_PREFIX}_{name}.png", dpi=300, bbox_inches="tight")

# Build cycles for plotting
# Baseline: show N_SHOW cycles in power plot
baseline_show = [baseline_cycle] * N_SHOW

# After: show N_SHOW cycles but start from SHOW_START to include more SKIP cycles (more visible improvement)
after_slice = after_pattern[SHOW_START:SHOW_START + N_SHOW]
after_show = [send_cycle if x == "SEND" else skip_cycle for x in after_slice]

# After full experiment: 16 cycles
after_16 = [send_cycle if x == "SEND" else skip_cycle for x in after_pattern]

# Build timelines
t_b_show, p_b_show, e_b_show = build_timeline(baseline_show, dt_ms=DT_MS)
t_a_show, p_a_show, e_a_show = build_timeline(after_show, dt_ms=DT_MS)

t_a16, p_a16, e_a16 = build_timeline(after_16, dt_ms=DT_MS)

# Fair cumulative-energy comparison over SAME total time window
# After total time = 16 * 8000 ms = 128000 ms
TOTAL_AFTER_MS = 16 * 8000

baseline_period_ms = sum(d for _, d in baseline_cycle)
need_cycles = int(np.ceil(TOTAL_AFTER_MS / baseline_period_ms)) + 1

t_b_long, p_b_long, e_b_long = build_timeline([baseline_cycle] * need_cycles, dt_ms=DT_MS)

# Truncate baseline to the same 128s window
mask_b = t_b_long <= TOTAL_AFTER_MS
t_b_128 = t_b_long[mask_b]
e_b_128 = e_b_long[mask_b]

# Truncate after (just in case of tiny rounding)
mask_a = t_a16 <= TOTAL_AFTER_MS
t_a_128 = t_a16[mask_a]
e_a_128 = e_a16[mask_a]
 
# Plot figures
fig1 = plot_power(t_b_show, p_b_show, f"Baseline: Power vs Time ({N_SHOW} cycles)")
save_fig(fig1, "baseline_power")

fig2 = plot_power(
    t_a_show, p_a_show,
    f"After Improvements: Power vs Time ({N_SHOW} cycles, window start={SHOW_START+1})"
)
save_fig(fig2, "after_power")

fig3 = plot_energy(t_b_128, e_b_128, "Baseline: Cumulative Energy vs Time (same 128s window)")
save_fig(fig3, "baseline_cum_energy_128s")

fig4 = plot_energy(t_a_128, e_a_128, "After Improvements: Cumulative Energy vs Time (128s)")
save_fig(fig4, "after_cum_energy_128s")

fig5 = plt.figure()
plt.plot(t_b_128, e_b_128, label="Baseline (same 128s window)")
plt.plot(t_a_128, e_a_128, label="After (128s)")
plt.xlabel("Time (ms)")
plt.ylabel("Cumulative Energy (mJ)")
plt.title("Cumulative Energy Comparison (same total time)")
plt.legend()
plt.tight_layout()
save_fig(fig5, "cum_energy_comparison_128s")

plt.show()