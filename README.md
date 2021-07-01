# Napalm AWS Tunnel Builder
This script simplifies the building of tunnels from AWS to your on-prem Juniper SRX firewall. It will parse through the configuration provided by AWS for the relevant variables you need (pre-shared-keys, tunnel endpoints, tunnel interface configuration, BGP neighbors, etc), it will then use those variables to render a Jinja2 template, and then it will push the rendered template to a firewall using the Napalm network automation library.

The template can be customized to fit your own needs.

## Usage
```
$ ./build-tunnel.py --help
usage: build-tunnel.py [-h] -f F

This script will parse and deploy AWS VPN Tunnels

optional arguments:
  -h, --help  show this help message and exit
  -f F        Downloaded AWS Config File
```
You will also be prompted to answer a few questions about the VPC and other tunnel parameters. Example:
```
Descriptive VPC name: my-vpc-name
VPC name is: my-vpc-name
Is this correct? Y/N? y
First st0 unit number: 1
First st0 interface is st0.1
Is this correct Y/N? y
```
After you've answered those questions, you will be required to enter the IP of the firewall you wish to push this configuration to, as well as a username and password:
```
Please enter firewall IP address: 192.168.0.1
Please enter username: user.name
Password:
```
Napalm will then connect to the firewall, push the configuration, and render a diff based on the current configuration:
```
Connecting to device...
Loading replacement candidate ...

Diff:
[edit security ike policy ike-pol-my-vpc-name-1]
+     pre-shared-key ascii-text ... ## Truncated
```
You will then have the option to discard or commit the configuration:
```
Would you like to commit these changes? (yes/no): no
Discarding...
```

## Requirements
This script was written and tested using Python 3. The Napalm and argparse modules are also required. To install required modules simply run ```pip install -r requirements.txt``` in this directory.