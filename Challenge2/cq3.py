import csv
import re
import subprocess

PCAP_FILE = "A.pcapng"
OUTPUT_CSV = "cq3_results.csv"

SERVER_IP = "127.0.0.1"
TARGET_RESOURCE = "/dining_room/temperature"

# Main filter for observe notifications
DISPLAY_FILTER = "coap.opt.observe && ip.src==127.0.0.1 && coap.code==69"


def run_tshark_fields():
    """Export basic fields from tshark."""
    cmd = [
        "tshark",
        "-r", PCAP_FILE,
        "-Y", DISPLAY_FILTER,
        "-T", "fields",
        "-E", "separator=\t",
        "-E", "quote=n",
        "-e", "frame.number",
        "-e", "frame.time_relative",
        "-e", "ip.src",
        "-e", "ip.dst",
        "-e", "coap.mid",
        "-e", "coap.token",
        "-e", "_ws.col.Info",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.splitlines()


def get_frame_hex(frame_number: str) -> str:
    """Export raw packet hex for one frame."""
    cmd = [
        "tshark",
        "-r", PCAP_FILE,
        "-Y", f"frame.number == {frame_number}",
        "-x",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def extract_ascii_from_hex_dump(hex_dump: str) -> str:
    """
    Convert tshark -x output into bytes, then decode printable text.
    This may still contain some binary garbage before the JSON part.
    """
    hex_bytes = []

    for line in hex_dump.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        # Skip first token (offset), keep only hex byte pairs
        for token in parts[1:]:
            if re.fullmatch(r"[0-9a-fA-F]{2}", token):
                hex_bytes.append(token)
            else:
                # Stop when ASCII preview starts
                break

    try:
        raw = bytes.fromhex("".join(hex_bytes))
        text = raw.decode("utf-8", errors="ignore")
        return text
    except Exception:
        return ""


def clean_payload_text(text: str) -> str:
    """
    Keep only the JSON part.
    This removes binary/control garbage before the real payload.
    """
    start = text.find('[{"name"')
    if start == -1:
        start = text.find('{"name"')
    if start == -1:
        return ""
    return text[start:]


def extract_value_from_text(text: str):
    """Extract JSON field: value"""
    match = re.search(r'"value"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    return None


# Step 1: collect candidate notification rows
raw_lines = run_tshark_fields()

rows = []

for line in raw_lines:
    parts = line.split("\t")
    while len(parts) < 7:
        parts.append("")

    frame_no, rel_time, src, dst, mid, token, info = parts[:7]

    if not frame_no.strip():
        continue

    info = info.strip()

    # Keep only target resource
    if TARGET_RESOURCE not in info:
        continue

    # Ignore retransmissions
    if "Retransmission" in info:
        continue

    # Ignore blockwise packets
    if "Block #0" in info or "End of Block #0" in info:
        continue

    rows.append({
        "frame_number": frame_no.strip(),
        "time": rel_time.strip(),
        "src_ip": src.strip(),
        "dst_ip": dst.strip(),
        "mid": mid.strip(),
        "token": token.strip(),
        "info": info,
    })

# Step 2: remove duplicate MIDs
seen_mids = set()
separate_rows = []

for row in rows:
    mid = row["mid"]
    if mid in seen_mids:
        continue
    seen_mids.add(mid)
    separate_rows.append(row)

# Step 3: extract payload text and value
for row in separate_rows:
    hex_dump = get_frame_hex(row["frame_number"])
    ascii_text = extract_ascii_from_hex_dump(hex_dump)
    clean_text = clean_payload_text(ascii_text)
    value = extract_value_from_text(clean_text)

    row["payload_text"] = clean_text
    row["value"] = value if value is not None else ""

# Step 4: count useless notifications
# Useless = same value as previous notification
previous_value = None
cq3b = 0

for row in separate_rows:
    current_value = row["value"]

    if previous_value is not None and current_value != "" and current_value == previous_value:
        row["is_useless"] = "Yes"
        cq3b += 1
    else:
        row["is_useless"] = "No"

    previous_value = current_value

# Step 5: save CSV
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "frame_number",
            "time",
            "src_ip",
            "dst_ip",
            "mid",
            "token",
            "info",
            "payload_text",
            "value",
            "is_useless",
        ]
    )
    writer.writeheader()
    writer.writerows(separate_rows)

cq3a = len(separate_rows)

print("CQ3a =", cq3a)
print("CQ3b =", cq3b)
print("Saved to", OUTPUT_CSV)