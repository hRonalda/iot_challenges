import subprocess
import csv

PCAP = "B.pcapng"

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

def wildcard_count(topic: str) -> int:
    return topic.count('+') + topic.count('#')

def main():
    rows = run_tshark(
        [
            "frame.number",
            "ip.src",
            "ip.dst",
            "ipv6.src",
            "ipv6.dst",
            "tcp.stream",
            "mqtt.topic",
        ],
        'mqtt.msgtype == 8 && (ip.dst == 127.0.0.1 || ipv6.dst == ::1)'
    )

    matches = []

    for row in rows:
        row += [""] * (7 - len(row))
        frame_no, ip_src, ip_dst, ipv6_src, ipv6_dst, tcp_stream, topic = row

        if not topic:
            continue

        wc = wildcard_count(topic)
        if wc >= 2:
            matches.append({
                "frame": frame_no,
                "stream": tcp_stream,
                "topic": topic,
                "wildcards": wc,
            })

    print("Subscribe requests with at least two wildcards:")
    for m in matches:
        print(m)

    print(f"\nCQ7 answer = {len(matches)}")

    with open("cq7_results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Frame", "TCP Stream", "Topic", "Wildcard Count"])
        for m in matches:
            writer.writerow([m["frame"], m["stream"], m["topic"], m["wildcards"]])

    print("\nCSV file 'cq7_results.csv' generated.")

if __name__ == "__main__":
    main()