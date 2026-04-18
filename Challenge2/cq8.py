import subprocess
import matplotlib.pyplot as plt
import csv


A_FILE = "A.pcapng"
B_FILE = "B.pcapng"


def run_tshark(pcap_file):
    """
    Extract MQTT PUBLISH topics directed to the local broker
    from the given pcap file.
    """
    cmd = [
        "tshark",
        "-r", pcap_file,
        "-Y", 'mqtt.msgtype == 3 && (ip.dst == 127.0.0.1 || ipv6.dst == ::1)',
        "-T", "fields",
        "-e", "mqtt.topic",
        "-E", "occurrence=f"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Store all extracted topics here
    topics = []

    # Split tshark output line by line
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        for p in parts:
            if p != "":
                topics.append(p)

    return topics


def count_layers(topic):
    """
    Count the number of layers in a topic.
    Example:
    home/temp -> 2
    home/room1/temp -> 3
    """
    return topic.count("/") + 1


def count_layer_distribution(topics):
    """
    Count how many messages belong to each topic depth.
    Returns a dictionary such as:
    {1: 10, 2: 25, 3: 8}
    """
    layer_counts = {}

    for topic in topics:
        layers = count_layers(topic)

        if layers not in layer_counts:
            layer_counts[layers] = 0

        layer_counts[layers] += 1

    return layer_counts


def group_topics_by_layer(topics):
    """
    Group topics by their number of layers.
    Returns a dictionary such as:
    {
        2: [topic1, topic2, ...],
        3: [topic3, topic4, ...]
    }
    """
    grouped = {}

    for topic in topics:
        layers = count_layers(topic)

        if layers not in grouped:
            grouped[layers] = []

        grouped[layers].append(topic)

    return grouped


def write_layer_csv(filename, grouped_a, grouped_b):
    """
    Write a CSV file containing:
    File, Layer, Count, Topics
    """
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["File", "Layer", "Count", "Topics"])

        for layer in sorted(grouped_a.keys()):
            topics_text = "; ".join(grouped_a[layer])
            writer.writerow(["A.pcapng", layer, len(grouped_a[layer]), topics_text])

        for layer in sorted(grouped_b.keys()):
            topics_text = "; ".join(grouped_b[layer])
            writer.writerow(["B.pcapng", layer, len(grouped_b[layer]), topics_text])


def fill_missing_layers(dict_a, dict_b):
    """
    Build a common list of layers for A and B.
    If one file does not contain a given layer,
    its count is set to 0.
    """
    all_layers = sorted(set(dict_a.keys()) | set(dict_b.keys()))

    a_values = []
    b_values = []

    for layer in all_layers:
        a_values.append(dict_a.get(layer, 0))
        b_values.append(dict_b.get(layer, 0))

    return all_layers, a_values, b_values


def plot_histogram(layers, a_values, b_values):
    """
    Plot a side-by-side histogram comparing A.pcapng and B.pcapng.
    """
    x_positions = range(len(layers))
    width = 0.35

    x_a = []
    x_b = []

    for x in x_positions:
        x_a.append(x - width / 2)
        x_b.append(x + width / 2)

    plt.figure(figsize=(10, 6))
    plt.bar(x_a, a_values, width=width, label="A.pcapng")
    plt.bar(x_b, b_values, width=width, label="B.pcapng")

    plt.xticks(list(x_positions), layers)
    plt.xlabel("Number of topic layers")
    plt.ylabel("Number of PUBLISH messages")
    plt.title("Distribution of MQTT topic depth for local broker")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig("cq8_histogram.png", dpi=300)
    plt.show()


def main():
    # Extract topics from A and B
    topics_a = run_tshark(A_FILE)
    topics_b = run_tshark(B_FILE)

    # Count total number of considered publish messages
    total_a = len(topics_a)
    total_b = len(topics_b)

    # Count the distribution of topic depths
    layer_counts_a = count_layer_distribution(topics_a)
    layer_counts_b = count_layer_distribution(topics_b)

    # Group topics by layer for CSV output
    grouped_a = group_topics_by_layer(topics_a)
    grouped_b = group_topics_by_layer(topics_b)

    # Print a few example topics
    print("10 examples of A.pcapng topics:")
    for t in topics_a[:10]:
        print(" ", t)

    print("\n10 examples of B.pcapng topics:")
    for t in topics_b[:10]:
        print(" ", t)

    # Print layer distributions
    print("\nLayer distribution for A.pcapng:")
    for layer in sorted(layer_counts_a.keys()):
        print(f"  {layer} layers -> {layer_counts_a[layer]} messages")

    print("\nLayer distribution for B.pcapng:")
    for layer in sorted(layer_counts_b.keys()):
        print(f"  {layer} layers -> {layer_counts_b[layer]} messages")

    # Print CQ8 answers
    print(f"\nCQ8a = {total_a}")
    print(f"CQ8b = {total_b}")

    # Write CSV file
    write_layer_csv("cq8_layer_topics.csv", grouped_a, grouped_b)
    print("\nCSV file saved as: cq8_layer_topics.csv")

    # Prepare data for plotting
    layers, a_values, b_values = fill_missing_layers(layer_counts_a, layer_counts_b)

    # Plot the histogram
    plot_histogram(layers, a_values, b_values)

    print("\nFigure saved as: cq8_histogram.png")


if __name__ == "__main__":
    main()