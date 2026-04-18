import subprocess
import csv

PCAP = "B.pcapng"
LOCAL_IPS = {"127.0.0.1", "::1"}


def run_tshark(fields, display_filter):
    cmd = [
        "tshark",
        "-r", PCAP,
        "-Y", display_filter,
        "-T", "fields",
        "-E", "header=n",
        "-E", "separator=\t",
        "-E", "quote=n",
        "-E", "occurrence=f",
    ]
    for f in fields:
        cmd += ["-e", f]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [line.split("\t") for line in result.stdout.splitlines()]


def is_retained_erase(qos_str, msg_len_str, topic_len_str):
    try:
        qos = int(qos_str)
        msg_len = int(msg_len_str)
        topic_len = int(topic_len_str)
    except Exception:
        return False

    diff = msg_len - topic_len

    if qos == 0 and diff == 2:
        return True
    if qos in (1, 2) and diff == 4:
        return True
    return False


def main():
    rows = run_tshark(
        [
            "frame.number",
            "ip.src",
            "ip.dst",
            "ipv6.src",
            "ipv6.dst",
            "tcp.stream",
            "tcp.srcport",
            "tcp.dstport",
            "mqtt.topic",
            "mqtt.topic_len",
            "mqtt.len",
            "mqtt.qos",
        ],
        'mqtt.msgtype == 3 && mqtt.retain == 1'
    )

    candidate_packets = []
    candidate_streams = set()

    for row in rows:
        row += [""] * (12 - len(row))
        (
            frame_no, ip_src, ip_dst, ipv6_src, ipv6_dst,
            tcp_stream, tcp_srcport, tcp_dstport,
            topic, topic_len, msg_len, qos
        ) = row

        dst = ip_dst if ip_dst else ipv6_dst
        src = ip_src if ip_src else ipv6_src

        if dst in LOCAL_IPS:
            continue

        if not is_retained_erase(qos, msg_len, topic_len):
            continue

        candidate_packets.append({
            "frame": frame_no,
            "src": src,
            "dst": dst,
            "stream": tcp_stream,
            "srcport": tcp_srcport,
            "dstport": tcp_dstport,
            "topic": topic,
            "topic_len": topic_len,
            "msg_len": msg_len,
            "qos": qos,
            "diff": int(msg_len) - int(topic_len)
        })
        if tcp_stream:
            candidate_streams.add(tcp_stream)

    print("Candidate retained-erase packets:")
    for pkt in candidate_packets:
        print(pkt)

    print("\nCandidate streams:")
    print(sorted(candidate_streams, key=lambda x: int(x) if x.isdigit() else x))

    with open("cq6_qos_candidates.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Frame", "Src", "Dst", "TCP Stream", "Src Port", "Dst Port",
            "Topic", "Topic Length", "Msg Len", "QoS", "Diff"
        ])
        for pkt in candidate_packets:
            writer.writerow([
                pkt["frame"], pkt["src"], pkt["dst"], pkt["stream"],
                pkt["srcport"], pkt["dstport"], pkt["topic"],
                pkt["topic_len"], pkt["msg_len"], pkt["qos"], pkt["diff"]
            ])

    # map stream -> client
    stream_to_client = {}

    if candidate_streams:
        stream_filter = " || ".join([f"tcp.stream == {s}" for s in candidate_streams])
        connect_rows = run_tshark(
            [
                "frame.number",
                "tcp.stream",
                "mqtt.clientid",
                "mqtt.clientid_len",
            ],
            f'mqtt.msgtype == 1 && ({stream_filter})'
        )

        for row in connect_rows:
            row += [""] * (4 - len(row))
            frame_no, tcp_stream, client_id, client_len = row
            if tcp_stream and tcp_stream not in stream_to_client:
                stream_to_client[tcp_stream] = {
                    "frame": frame_no,
                    "client_id": client_id,
                    "client_len": client_len,
                }

    print("\nStream to client mapping:")
    for s, info in stream_to_client.items():
        print(s, info)

    unique_clients = {}
    for s in candidate_streams:
        if s in stream_to_client:
            cid = stream_to_client[s]["client_id"]
            if cid == "":
                cid = f"<empty-id-stream-{s}>"
            unique_clients[cid] = stream_to_client[s]

    print("\nUnique clients that erased retained values:")
    for cid, info in unique_clients.items():
        print(cid, info)

    cq6a = len(unique_clients)

    long_clients = []
    for cid, info in unique_clients.items():
        try:
            cid_len = int(info["client_len"])
        except Exception:
            cid_len = 0
        if cid_len > 7:
            long_clients.append((cid, cid_len))

    print("\nClients with client ID length > 7:")
    for cid, cid_len in long_clients:
        print(cid, cid_len)

    print(f"\nCQ6a answer = {cq6a}")
    print(f"CQ6b answer = {len(long_clients)}")
    print("\nCSV file 'cq6_qos_candidates.csv' generated.")


if __name__ == "__main__":
    main()