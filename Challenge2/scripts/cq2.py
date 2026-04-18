import pyshark
import csv

PCAP_FILE = "A.pcapng"
OUTPUT_CSV = "cq2_results.csv"
COAP_ME_IP = "134.102.218.18"

packets = []

cap = pyshark.FileCapture(PCAP_FILE, display_filter="coap")

for pkt in cap:
    try:
        if not hasattr(pkt, "coap") or not hasattr(pkt, "ip"):
            continue

        token = getattr(pkt.coap, "token", None)
        code = getattr(pkt.coap, "code", None)
        coap_type = getattr(pkt.coap, "type", None)
        mid = getattr(pkt.coap, "mid", None)

        if token is None or code is None:
            continue

        uri = ""
        try:
            uri = str(pkt.coap.opt_uri_path)
        except Exception:
            pass

        packets.append({
            "frame": int(pkt.number),
            "src": str(pkt.ip.src),
            "dst": str(pkt.ip.dst),
            "token": str(token),
            "code": str(code),
            "type": str(coap_type) if coap_type is not None else "",
            "mid": str(mid) if mid is not None else "",
            "uri": uri,
        })

    except Exception:
        pass

cap.close()

# 保存候选 request
requests = []

for p in packets:
    # local server only: exclude coap.me traffic
    if p["src"] == COAP_ME_IP or p["dst"] == COAP_ME_IP:
        continue

    # CON POST / CON PUT
    if p["type"] == "0" and p["code"] in ["2", "3"]:
        method = "POST" if p["code"] == "2" else "PUT"
        requests.append({
            "frame": p["frame"],
            "token": p["token"],
            "uri": p["uri"],
            "method": method,
            "mid": p["mid"],
        })

# 对每个 resource 统计 unique failed POST/PUT
resource_stats = {}

for req in requests:
    uri = req["uri"]
    if uri not in resource_stats:
        resource_stats[uri] = {"POST": set(), "PUT": set()}

    # 找这个 request 后面的第一个同 token response
    matched_response = None
    for p in packets:
        if p["frame"] <= req["frame"]:
            continue
        if p["token"] != req["token"]:
            continue

        try:
            code_num = int(p["code"])
        except Exception:
            continue

        # 只看 response code
        if code_num >= 64:
            matched_response = p
            break

    if matched_response is None:
        continue

    # unsuccessful = 4.xx or 5.xx
    try:
        resp_code = int(matched_response["code"])
    except Exception:
        continue

    if 128 <= resp_code < 192:
        resource_stats[uri][req["method"]].add(req["frame"])

rows = []
cq2_count = 0

for uri, stats in sorted(resource_stats.items()):
    post_count = len(stats["POST"])
    put_count = len(stats["PUT"])
    ok = (post_count == put_count and post_count > 0)

    if ok:
        cq2_count += 1

    rows.append({
        "resource": uri,
        "unsuccessful_post_count": post_count,
        "unsuccessful_put_count": put_count,
        "x_equals_y_and_x_gt_0": ok
    })

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "resource",
            "unsuccessful_post_count",
            "unsuccessful_put_count",
            "x_equals_y_and_x_gt_0"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print("CQ2 result =", cq2_count)
print("Saved detailed results to", OUTPUT_CSV)

print("\nDetailed rows:")
for row in rows:
    print(row)