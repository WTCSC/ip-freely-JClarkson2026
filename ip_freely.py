"""
network_scanner.py
------------------
A lightweight network scanning utility that:
  - Expands a CIDR range into individual IP addresses
  - Pings each host to check reachability
  - Performs reverse DNS lookups on each IP
  - Exports results to a timestamped CSV file via pandas
"""

import os
import socket
import pandas as pd
from datetime import datetime


# ---------------------------------------------------------------------------
# DNS / Network helpers
# ---------------------------------------------------------------------------

def reverseDNS(ip):
    """
    Perform a reverse DNS lookup for the given IP address.

    Args:
        ip (str): IPv4 address to look up.

    Returns:
        dict: Contains 'ip', 'hostname', 'aliases', and 'addresses'.
              On failure, also includes an 'error' key describing the problem.
    """
    try:
        hostname, aliases, addresses = socket.gethostbyaddr(ip)
        return {
            "ip": ip,
            "hostname": hostname,
            "aliases": aliases,
            "addresses": addresses
        }
    except socket.herror:
        # herror is raised when no PTR record exists for the IP
        return {
            "ip": ip,
            "hostname": None,
            "aliases": [],
            "addresses": [],
            "error": "No PTR record found"
        }
    except socket.gaierror:
        # gaierror is raised for address-related errors (e.g. malformed IP)
        return {
            "ip": ip,
            "hostname": None,
            "aliases": [],
            "addresses": [],
            "error": "Invalid IP address"
        }


def IPToInt(ip):
    """
    Convert a dotted-decimal IPv4 address to a 32-bit integer.

    Args:
        ip (str): IPv4 address (e.g. '192.168.1.1').

    Returns:
        int: The IP address as a 32-bit unsigned integer.
    """
    a, b, c, d = ip.split(".")
    # Shift each octet into its correct byte position and OR them together
    return (int(a) << 24) | (int(b) << 16) | (int(c) << 8) | int(d)


def intToIP(n):
    """
    Convert a 32-bit integer back to a dotted-decimal IPv4 address.

    Args:
        n (int): 32-bit unsigned integer representing an IP address.

    Returns:
        str: Dotted-decimal IPv4 string (e.g. '192.168.1.1').
    """
    # Extract each octet by shifting and masking, then join with dots
    return ".".join(str((n >> s) & 0xFF) for s in (24, 16, 8, 0))


def cidrToIPS(cidr):
    """
    Expand a CIDR block into a list of all individual IP addresses it contains,
    including the network address and broadcast address.

    Args:
        cidr (str): CIDR notation string (e.g. '192.168.1.0/24').

    Returns:
        list[str]: All IP addresses within the CIDR range.
    """
    ip, prefix = cidr.split("/")
    prefix = int(prefix)
    ip_int = IPToInt(ip)

    # Build the subnet mask from the prefix length
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF

    # Network address = IP ANDed with mask; broadcast = network ORed with inverted mask
    network = ip_int & mask
    broadcast = network | (~mask & 0xFFFFFFFF)

    return [intToIP(i) for i in range(network, broadcast + 1)]


# ---------------------------------------------------------------------------
# Ping
# ---------------------------------------------------------------------------

def pingHost(hostname):
    """
    Send a single ICMP ping to the given host.

    Args:
        hostname (str): IP address or hostname to ping.

    Returns:
        int: Return code from the ping command (0 = reachable, non-zero = unreachable).
    """
    # -c 1 sends a single packet; output is suppressed for a cleaner console
    response = os.system(f"ping -c 1 {hostname} > /dev/null 2>&1")
    return response


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def exportToCSV(results, output_file=None):
    """
    Export the scan results list to a CSV file using pandas.

    Each row represents one scanned host and includes its reachability status
    and reverse DNS information.

    Args:
        results (list[dict]): Scan results as returned by runList().
        output_file (str | None): Destination file path. If None, a timestamped
                                  filename is generated automatically.

    Returns:
        str: Path to the written CSV file.
    """
    # Auto-generate a filename if none was provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"scan_results_{timestamp}.csv"

    # Flatten each result dict into a row suitable for a DataFrame
    rows = []
    for r in results:
        dns = r["dns"]
        rows.append({
            "IP Address": r["ip"],
            "Status":     r["status"],
            "Hostname":   dns.get("hostname") or "",
            # Aliases and extra addresses are joined into comma-separated strings
            "Aliases":    ", ".join(dns.get("aliases", [])),
            "Addresses":  ", ".join(dns.get("addresses", [])),
            "DNS Error":  dns.get("error", ""),
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
    print(f"\nResults exported to: {output_file}")
    return output_file


# ---------------------------------------------------------------------------
# Main scan runner
# ---------------------------------------------------------------------------

def runList(hosts, export_csv=True, csv_file=None):
    """
    Ping every host in the provided list, perform a reverse DNS lookup on each,
    print a live status update, and optionally export the results to CSV.

    Args:
        hosts (list[str]):   List of IP addresses or hostnames to scan.
        export_csv (bool):   If True (default), write results to a CSV file.
        csv_file (str|None): Custom CSV output path. Auto-generated if None.

    Returns:
        list[dict]: Full scan results, one dict per host.
    """
    active = 0
    inactive = 0
    results = []  # Accumulates per-host result dicts for CSV export

    for host in hosts:
        print(f"Pinging {host}...")
        reachable = pingHost(host) == 0   # 0 exit code means the host responded
        dns_info = reverseDNS(host)

        if reachable:
            print(f"{host} is reachable.")
            print(f"  Hostname: {dns_info['hostname']}")
            active += 1
            status = "active"
        else:
            print(f"{host} is not reachable.")
            inactive += 1
            status = "inactive"

        # Store result for later export
        results.append({"ip": host, "status": status, "dns": dns_info})

    print(f"\nSummary: {active} active, {inactive} inactive.")

    # Export to CSV if requested
    if export_csv:
        exportToCSV(results, csv_file)

    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Scan the entire 192.168.1.0/24 subnet and export results to CSV
    runList(cidrToIPS(input("Enter CIDR notation (e.g., 192.168.1.0/24): ")), export_csv=True)