# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in SystemDNA, please open a issue at https://github.com/Fontailll/SystemDNA/issues. Do not disclose it publicly until it has been addressed.

You should receive an acknowledgement within 48 hours. Once the vulnerability is confirmed, a fix will be prepared and released as soon as possible depending on severity.

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## No Telemetry

SystemDNA is fully offline. It does not make network requests, collect usage data, phone home, or transmit any system information. All data stays on the machine where the snapshot is created until you explicitly export it.

## Offline-First Design

- No network calls are made during snapshot creation, diffing, or analysis
- Plugin discovery and loading is filesystem-local
- All configuration is stored in local files
- Exported reports are written to local paths or stdout
