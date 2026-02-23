# Network Scanner

A lightweight command-line network scanning utility written in Python. It expands a CIDR range into individual IPs, pings each host to check reachability, performs reverse DNS lookups, and exports the results to a CSV file.

---

## Features

- **CIDR expansion** — converts any CIDR block (e.g. `192.168.1.0/24`) into a full list of IPs
- **ICMP ping** — checks whether each host is reachable using a single ping packet
- **Reverse DNS lookup** — resolves hostnames, aliases, and associated addresses for each IP
- **CSV export** — saves all results to a timestamped CSV file via pandas

---

## Requirements

- Python 3.7+
- [pandas](https://pandas.pydata.org/)

Install dependencies:

```bash
pip install pandas
```

> **Note:** The ping functionality uses the system `ping` command with the `-c 1` flag (Linux/macOS). On Windows, replace `-c 1` with `-n 1` inside `pingHost()`.

---

## Usage

### Run a default scan

```bash
python ip_freely.py
```

This scans the entire `192.168.1.0/24` subnet and writes results to a file named `scan_results_YYYYMMDD_HHMMSS.csv`.

### Use as a module

```python
from ip_freely import cidrToIPS, runList

# Scan a /28 subnet, save to a custom file
hosts = cidrToIPS("10.0.0.0/28")
runList(hosts, export_csv=True, csv_file="my_scan.csv")

# Scan without exporting
results = runList(hosts, export_csv=False)
```

---

## API Reference

### `cidrToIPS(cidr) -> list[str]`
Expands a CIDR block into a list of all IP addresses (including network and broadcast addresses).

| Param | Type | Description |
|-------|------|-------------|
| `cidr` | `str` | CIDR notation, e.g. `"192.168.1.0/24"` |

---

### `pingHost(hostname) -> int`
Pings a host once and returns the exit code (`0` = reachable).

| Param | Type | Description |
|-------|------|-------------|
| `hostname` | `str` | IP address or hostname to ping |

---

### `reverseDNS(ip) -> dict`
Performs a reverse DNS lookup and returns a dict with the following keys:

| Key | Type | Description |
|-----|------|-------------|
| `ip` | `str` | The queried IP address |
| `hostname` | `str \| None` | Resolved hostname |
| `aliases` | `list[str]` | Any DNS aliases |
| `addresses` | `list[str]` | Associated addresses |
| `error` | `str` | Present only on lookup failure |

---

### `runList(hosts, export_csv=True, csv_file=None) -> list[dict]`
Scans a list of hosts and optionally exports results to CSV.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `hosts` | `list[str]` | — | IPs or hostnames to scan |
| `export_csv` | `bool` | `True` | Whether to write a CSV file |
| `csv_file` | `str \| None` | `None` | Custom output path; auto-generated if `None` |

---

### `exportToCSV(results, output_file=None) -> str`
Writes scan results to a CSV file and returns the file path.

---

## CSV Output Format

| Column | Description |
|--------|-------------|
| IP Address | The scanned IP |
| Status | `active` or `inactive` |
| Hostname | Reverse DNS hostname (empty if unresolved) |
| Aliases | Comma-separated DNS aliases |
| Addresses | Comma-separated associated addresses |
| DNS Error | Error message if DNS lookup failed |

Example:

```
IP Address,Status,Hostname,Aliases,Addresses,DNS Error
192.168.1.1,active,router.local,,192.168.1.1,
192.168.1.2,inactive,,,,"No PTR record found"
```

---

## Project Structure

```
network_scanner.py   # Main script
README.md            # This file
scan_results_*.csv   # Auto-generated output files (after running)
```

---

## License

MIT — use freely, modify as needed.