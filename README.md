# Ansible VPN
My own version of a simple interactive script that sets up a Wireguard VPN server with Adguard, Unbound and DNSCrypt-Proxy on your VPS of choice, and lets you manage the config files using a simple WebUI protected by two-factor-authentication.

## Requirements
* A KVM-based VPS (or an AWS EC2 instance) with a dedicated IPv4 address
* Ubuntu Server 22.04/20.04 or Debian 11/12 or Fedora (to be tested)

## Usage
```shell
# clone the project
$ git clone https://github.com/pluresque/ansible-vpn.git

# run the bootstrap script
$ bash bootstrap.sh
```

## Feature
* Rewritten bootstrap.sh script
* Wireguard WebUI (via wg-easy)
* Two-factor authentication for the WebUI (Authelia)
* Encrypted DNS resolution with optional ad-blocking functionality (Adguard Home, DNSCrypt and Unbound)
* IPTables firewall with sane defaults and Fail2Ban
* Automated and unattended upgrades
* SSH hardening and public key pair generation (optional, you can also use your own keys)

## Credits
Code and ideas in this project are inspired by the following projects:
* [ansible-role-wireguard](https://github.com/githubixx/ansible-role-wireguard/tree/master)