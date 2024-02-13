# Ansible VPN
Simple & interactive script that sets up a secure VPN server with Wireguard, WebUI, DNS encryption and ad blocking.

## Requirements
* A KVM host (or an AWS EC2 instance) with a dedicated IPv4 address

## Tested on
* Ubuntu Server 22.04/20.04
* Debian 11/12 
* Fedora 39 

## Usage
```shell
# clone the project
$ git clone https://github.com/pluresque/ansible-vpn.git

# run the bootstrap script
$ bash bootstrap.sh
```

## Feature
* Wireguard WebUI with two-factor authentication (2FA)
* Encrypted DNS resolution with optional ad-blocking functionality
* IPTables firewall with sane defaults and Fail2Ban
* SSH hardening and public key pair generation 

## Credits
Code and ideas in this project are inspired by the following projects:
* [ansible-role-wireguard](https://github.com/githubixx/ansible-role-wireguard/tree/master)