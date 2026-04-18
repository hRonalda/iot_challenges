import subprocess
import csv
import io
from collections import defaultdict

PCAP = "B.pcapng"
BROKER_PORT = "1883"


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
    rows = []
    for line in result.stdout.splitlines():
        rows.append(line.split("\t"))
    return rows


def has_wildcard(topic: str) -> bool:
    return "+" in topic or "#" in topic


def main():
    # 1) Find all CONNECT packets with Will Flag set
    will_rows = run_tshark(
        ["frame.number", "mqtt.clientid", "mqtt.willtopic"],
        'mqtt.msgtype == 1 && mqtt.conflag.willflag == 1'
    )

    will_topics = set()
    print("Will packets:")
    for row in will_rows:
        if len(row) < 3:
            continue
        frame_no, client_id, will_topic = row
        print(f"  frame={frame_no}, client_id={client_id}, will_topic={will_topic}")
        if will_topic:
            will_topics.add(will_topic)

    print("\nUnique Will Topics:")
    for t in sorted(will_topics):
        print(" ", t)

    # 2) For each Will Topic, find broker->client PUBLISH
    topic_to_ports = defaultdict(set)

    for topic in sorted(will_topics):
        pub_rows = run_tshark(
            ["frame.number", "tcp.srcport", "tcp.dstport", "mqtt.topic"],
            f'mqtt.msgtype == 3 && mqtt.topic == "{topic}" && tcp.srcport == {BROKER_PORT}'
        )
        for row in pub_rows:
            if len(row) < 4:
                continue
            frame_no, src_port, dst_port, pkt_topic = row
            if dst_port:
                topic_to_ports[topic].add(dst_port)

    print("\nLWT receivers by topic:")
    candidate_ports = set()
    for topic, ports in topic_to_ports.items():
        print(f"  {topic}: {sorted(ports, key=int)}")
        candidate_ports.update(ports)

    # 3) For each receiver port, find all SUBSCRIBE topics
    port_to_topics = defaultdict(set)
    for port in sorted(candidate_ports, key=int):
        sub_rows = run_tshark(
            ["frame.number", "tcp.srcport", "tcp.dstport", "mqtt.topic"],
            f'mqtt.msgtype == 8 && tcp.port == {port}'
        )
        for row in sub_rows:
            if len(row) < 4:
                continue
            frame_no, src_port, dst_port, topic = row
            if topic:
                port_to_topics[port].add(topic)

    print("\nSubscriptions of candidate receivers:")
    for port in sorted(port_to_topics, key=int):
        print(f"  Port {port}:")
        for topic in sorted(port_to_topics[port]):
            print("   ", topic)

    # 4) Keep only receivers with wildcard subscriptions
    wildcard_receivers = set()
    for port, topics in port_to_topics.items():
        if any(has_wildcard(t) for t in topics):
            wildcard_receivers.add(port)

    print("\nWildcard receivers:")
    for port in sorted(wildcard_receivers, key=int):
        print(" ", port)

    print(f"\nCQ5 answer = {len(wildcard_receivers)}")


    import csv

    # write on CSV
    with open("cq5_results.csv", "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["Will Topic", "Subscriber Port", "Has Wildcard"])

        for topic, ports in topic_to_ports.items():
            for port in ports:
                has_wc = "No"

                if port in port_to_topics:
                    if any(has_wildcard(t) for t in port_to_topics[port]):
                        has_wc = "Yes"

                writer.writerow([topic, port, has_wc])

    print("\nCSV file 'cq5_results.csv' generated.")


if __name__ == "__main__":
    main()