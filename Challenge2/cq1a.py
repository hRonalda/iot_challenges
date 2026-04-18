import pyshark
import csv

PCAP_FILE = "A.pcapng"
COAP_ME_IP = "134.102.218.18"
OUTPUT_CSV = "cq1_results.csv"

# token is the request info
requests = {}

# CQ1a matches all successful response (2.xx)
cq1a_results = []

# CQ1b matches the desired outcome 
cq1b_results = []

cap = pyshark.FileCapture(PCAP_FILE, display_filter="coap")

for pkt in cap:
    try:
        if not hasattr(pkt, "coap") or not hasattr(pkt, "ip"):
            continue

        token = getattr(pkt.coap, "token", None)
        code = getattr(pkt.coap, "code", None)
        coap_type = getattr(pkt.coap, "type", None)
        mid = getattr(pkt.coap, "mid", None)

        if token is None:
            continue

        token_str = str(token)
        src_ip = pkt.ip.src
        dst_ip = pkt.ip.dst

        # save NON DELETE requests sent to coap.me
        if src_ip != COAP_ME_IP and dst_ip == COAP_ME_IP:
            if coap_type == "1" and code == "4":
                uri = ""
                try:
                    uri = str(pkt.coap.opt_uri_path)
                except Exception:
                    pass

                requests[token_str] = {
                    "request_frame": str(pkt.number),
                    "request_mid": str(mid),
                    "token": token_str,
                    "uri": uri,
                    "request_src": src_ip,
                    "request_dst": dst_ip
                }

        # find responses from coap.me with same token
        elif src_ip == COAP_ME_IP and token_str in requests:
            try:
                code_num = int(code)
            except Exception:
                continue

            req = requests[token_str]

            row = {
                "request_frame": req["request_frame"],
                "request_mid": req["request_mid"],
                "token": req["token"],
                "uri": req["uri"],
                "response_frame": str(pkt.number),
                "response_mid": str(mid),
                "response_code": str(code_num)
            }

            # CQ1a: successful response = 2.xx
            if 64 <= code_num < 96:
                cq1a_results.append(row)

            # CQ1b: desired outcome for DELETE = 2.02 Deleted = 66
            if code_num == 66:
                cq1b_results.append(row)

    except Exception:
        pass

cap.close()

# CQ1a output
cq1a_mids = [row["request_mid"] for row in cq1a_results]
print("CQ1a MIDs:")
print(cq1a_mids)
print(f"CQ1a count = {len(cq1a_mids)}")

# CQ1b output
cq1b_mids = [row["request_mid"] for row in cq1b_results]
print("\nCQ1b MIDs:")
print(cq1b_mids)
print(f"CQ1b count = {len(cq1b_mids)}")

# Save all CQ1a rows
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "request_frame",
            "request_mid",
            "token",
            "uri",
            "response_frame",
            "response_mid",
            "response_code"
        ]
    )
    writer.writeheader()
    writer.writerows(cq1a_results)

print(f"\nSaved CQ1a details to {OUTPUT_CSV}")