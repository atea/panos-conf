# panos-conf

PAN-OS configuration utility.

Currently let's you fetch configuration from one or more PANOS devices. The
configuration is stored as separate YAML files.

## Features
* Fetch configuration of the following types, and store as YAML:
  - Objects (address, address groups, tags, etc)
  - Policies (NAT rules, PBF, and security rules)
* Store API key in system keyring (where supported)

## Roadmap:
* Fetch other configuration aspects of PANOS devices, such as:
  - "Device" configuration
  - "Network" configuration
* Encrypt per-device API keys (similar to `ansible-vault encrypt_string`)
* Push configuration to PANOS devices based on YAML
* Push files to PANOS devices (certificates, etc)

## Potential future roadmap:
* Configure Panorama
* Configure HA

