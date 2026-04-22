import subprocess
import csv

PCAP = "../captures/B.pcapng"

HIVEMQ_IPS = ["18.192.151.104", "35.158.34.213", "35.158.43.69"]
MQTT_VERSIONS = [3, 4, 5]


def run_tshark_fields(fields, display_filter):
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

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("TSHARK FAILED")
        print("Command:")
        print(" ".join(cmd))
        print("\nSTDERR:")
        print(result.stderr)
        raise RuntimeError("tshark failed")

    rows = []
    for line in result.stdout.splitlines():
        rows.append(line.split("\t"))
    return rows


def run_tshark_verbose(display_filter):
    cmd = [
        "tshark",
        "-r", PCAP,
        "-Y", display_filter,
        "-V",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("TSHARK FAILED")
        print("Command:")
        print(" ".join(cmd))
        print("\nSTDERR:")
        print(result.stderr)
        raise RuntimeError("tshark failed")

    return result.stdout


def broker_ip_filter():
    return "(" + " || ".join(f"ip.dst=={ip}" for ip in HIVEMQ_IPS) + ")"


def packet_has_missing_message(frame_no):
    verbose_text = run_tshark_verbose(f"frame.number=={frame_no}")
    return "Message: <MISSING>" in verbose_text


def main():
    ip_filter = broker_ip_filter()

    cq6a_clients = set()
    cq6a_details = []

    with open("../results/cq6a_results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "MQTT Version",
            "CONNECT Frame",
            "Stream",
            "Client ID",
            "Client ID Length",
            "Broker IP",
            "Publish Frame",
            "Topic",
            "Message Missing",
            "Counted for CQ6a",
            "Counted for CQ6b"
        ])

        for ver in MQTT_VERSIONS:
            connect_filter = (
                f"mqtt.msgtype==1 && mqtt.ver=={ver} && tcp.dstport==1883 && {ip_filter}"
            )

            connect_rows = run_tshark_fields(
                ["frame.number", "tcp.stream", "mqtt.clientid", "ip.dst"],
                connect_filter
            )

            print(f"\n=== MQTT version {ver} CONNECT packets ===")

            for row in connect_rows:
                if len(row) < 4:
                    continue

                connect_frame, stream_id, client_id, broker_ip = row

                if not stream_id or not client_id:
                    continue

                client_len = len(client_id)

                print(
                    f"CONNECT frame={connect_frame}, stream={stream_id}, "
                    f"client_id={client_id}, client_len={client_len}, broker_ip={broker_ip}"
                )

                publish_filter = (
                    f"mqtt.msgtype==3 && mqtt.retain==1 && tcp.dstport==1883 "
                    f"&& {ip_filter} && tcp.stream=={stream_id}"
                )

                pub_rows = run_tshark_fields(
                    ["frame.number", "mqtt.topic"],
                    publish_filter
                )

                if not pub_rows:
                    print(f"  -> No retained PUBLISH packets in stream {stream_id}")
                    continue

                print(f"  -> Retained PUBLISH packets found: {len(pub_rows)}")

                missing_frames = []

                for pub_row in pub_rows:
                    frame_pub = pub_row[0] if len(pub_row) > 0 else ""
                    topic = pub_row[1] if len(pub_row) > 1 else ""

                    is_missing = packet_has_missing_message(frame_pub)

                    if is_missing:
                        missing_frames.append((frame_pub, topic))

                if missing_frames:
                    cq6a_clients.add(client_id)

                    print(f"  -> CQ6a match in stream {stream_id}")
                    for frame_pub, topic in missing_frames:
                        print(f"     missing frame={frame_pub}, topic={topic}")

                    counted_6b = "Yes" if client_len > 7 else "No"

                    cq6a_details.append({
                        "version": ver,
                        "connect_frame": connect_frame,
                        "stream": stream_id,
                        "client_id": client_id,
                        "client_len": client_len,
                        "broker_ip": broker_ip,
                        "missing_frames": missing_frames,
                        "counted_6b": counted_6b,
                    })

                    for frame_pub, topic in missing_frames:
                        writer.writerow([
                            ver,
                            connect_frame,
                            stream_id,
                            client_id,
                            client_len,
                            broker_ip,
                            frame_pub,
                            topic,
                            "Yes",
                            "Yes",
                            counted_6b
                        ])
                else:
                    print(f"  -> No 'Message: <MISSING>' found in stream {stream_id}")

                    for pub_row in pub_rows:
                        frame_pub = pub_row[0] if len(pub_row) > 0 else ""
                        topic = pub_row[1] if len(pub_row) > 1 else ""
                        writer.writerow([
                            ver,
                            connect_frame,
                            stream_id,
                            client_id,
                            client_len,
                            broker_ip,
                            frame_pub,
                            topic,
                            "No",
                            "No",
                            "No"
                        ])

    cq6b_clients = {client_id for client_id in cq6a_clients if len(client_id) > 7}

    print("\n=== CQ6a RESULT ===")
    print("Clients counted for CQ6a:")
    for client_id in sorted(cq6a_clients):
        print(" ", client_id)
    print(f"\nCQ6a answer = {len(cq6a_clients)}")

    print("\n=== CQ6b RESULT ===")
    print("Clients from CQ6a with client ID length > 7:")
    for client_id in sorted(cq6b_clients):
        print(f"  {client_id} (length={len(client_id)})")
    print(f"\nCQ6b answer = {len(cq6b_clients)}")

    print("\nDetails of matched clients:")
    for item in cq6a_details:
        print(
            f"  version={item['version']}, connect_frame={item['connect_frame']}, "
            f"stream={item['stream']}, client_id={item['client_id']}, "
            f"length={item['client_len']}, broker_ip={item['broker_ip']}, "
            f"CQ6b={item['counted_6b']}"
        )
        for frame_pub, topic in item["missing_frames"]:
            print(f"     missing frame={frame_pub}, topic={topic}")


if __name__ == "__main__":
    main()