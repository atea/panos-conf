# panos-conf

PAN-OS configuration utility.

Currently let's you fetch configuration from one or more PANOS devices. The
configuration is stored as separate YAML files.

## Features
* Fetch configuration of the following types, and store as YAML:
  - Objects (address, address groups, tags, etc)
  - Policies (NAT rules, PBF, and security rules)

## Roadmap:
* Fetch other configuration aspects of PANOS devices, such as:
  - "Device" configuration
  - "Network" configuration
* Push configuration to PANOS devices based on YAML
* Push files to PANOS devices (certificates, etc)

## Potential future roadmap:
* Configure Panorama
* Configure HA

