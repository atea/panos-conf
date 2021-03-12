# panos-conf

PAN-OS configuration utility. Fetch and/or push configuration from one or more
PANOS devices. Configuration is stored per host in individual YAML files.

## Features
* Fetch configuration of the following types, and store as YAML:
  - Objects (address, address groups, tags, etc)
  - Policies (NAT rules, PBF, and security rules)
  - Device (Admin users, system settings, etc)
  - Network (Interfaces, tunnels, zones, virtual routers, etc)
* Encrypts per-device API keys (similar to `ansible-vault encrypt_string`)
* Password for encryption stored in keyring or entered manually on each run
* Re-encrypt API-keys upon password change
* Verify stored API-keys; create new ones if invalid

## Roadmap:
* Push configuration to PANOS devices based on YAML
* Push files to PANOS devices (certificates, etc)

## Potential future roadmap:
* Configure Panorama
* Configure HA

