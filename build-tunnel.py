#! /usr/bin/env python3

import re
import napalm
import argparse
from getpass import getpass
from jinja2 import Environment
from jinja2 import Template
from jinja2 import FileSystemLoader


def commit_discard(choice):
    # Commit or discard function
    # Will either commit or discard configuration based on input from commit_check function
    if choice == 'yes':
        print('Comitting...')
        device.commit_config()
    elif choice == 'no':
        print('Discarding...')
        device.discard_config()


def check_commit(question, choices):
    # Check commit function
    # Gathers input from user to determine whether or not to commit or discard config - question and choices vars passed when function is called, see line 164
    choice = input(question)
    if choice in choices:
        return commit_discard(choice)

    print('Invalid choice')
    return check_commit(question, choices)


def get_hostname(host_ip="Please enter firewall IP address: "):
    # Get hostname function
    # Gathers IP information of the firewall that we will push the config to - also validates whether it is a valid IP
    global host
    host = input(host_ip)
    split_host_ip = host.split('.')
    for octet in split_host_ip:
        if int(octet) >= 255:
            print("Invalid IP")
            return get_hostname()


# Arugments passed when executing the script
parser = argparse.ArgumentParser(description="This script will parse and deploy AWS VPN Tunnels")
parser.add_argument("-f", default=None, required=True, type=str, help="Downloaded AWS Config File")

args = parser.parse_args()

# Location of file passed to variable, file opened and passed to variable
file_name = args.f
fo = open(file_name)


def get_vpc_name(vpc_name_input="Descriptive VPC name (24 character max): "):
    # Function to enter a descriptive VPC name - logic to ensure entry is correct
    global vpc_name
    vpc_name = input(vpc_name_input)
    while len(vpc_name) >= 24:
        print("VPC name is too long, try again")
        vpc_name = input(vpc_name_input)
    print("VPC name is: " + vpc_name)
    counter = 1
    while counter == 1:
        choice = input("Is this correct? Y/N? ")
        if choice == "y" or choice == "Y":
            return
        if choice == "n" or choice == "N":
            return get_vpc_name()
        else:
            print("Invalid choice")
    return vpc_name


get_vpc_name()


def get_st(st="First st0 unit number: "):
    # Function to enter tunnel interface unit number - logic to ensure entry is correct
    global st_input
    st_input = input(st)
    print("First st0 interface is st0." + st_input)
    counter = 1
    while counter == 1:
        choice = input("Is this correct Y/N? ")
        if choice == "y" or choice == "Y":
            return
        if choice == "n" or choice == "N":
            return get_st()
        else:
            print("Invalid choice")


get_st()

int(st_input)  # Convert st0 input to integer for later logic

data = fo.read()  # Read opened file and pass to variable

psk = re.findall("-[1-2] pre-shared-key ascii-text ([a-zA-Z0-9!@#$%^&*(),._]+)", data)  # Scrape file for PSK information and pass to list

# Pass each PSK in list to its own var
psk1 = psk[0]
psk2 = psk[1]

gateway = re.findall("-[1-2] address (\d+\.\d+\.\d+\.\d+)", data)  # Scrape file for gateway information and pass to list

# Pass each gateway in list to its own var
gateway1 = gateway[0]
gateway2 = gateway[1]

st_ip = re.findall("family inet address (\d+\.\d+\.\d+\.\d+\/30)", data)  # Scrape file for tunnel interface IP information and pass to list

# Pass each IP in list to its own var
st_ip1 = st_ip[0]
st_ip2 = st_ip[1]

# Split IP var at dot to list
split_st_ip1 = st_ip1.split('.')
split_st_ip2 = st_ip2.split('.')

# Logic to determine which tunnel interface has the lower IP, lower IP goes to first st0 inputted earlier
if split_st_ip1[3] <= split_st_ip2[3]:
    st1 = int(st_input)
    st2 = int(st_input) + 1
    str(st1)
    str(st2)
else:
    st1 = int(st_input) + 1
    st2 = int(st_input)
    str(st1)
    str(st2)

neighbors = re.findall("neighbor (\d+\.\d+\.\d+\.\d+) peer-as", data)  # Scrape file for BGP neighbor information and pass to list

# Pass each BGP neighnor in list to its own var
neighbor1 = neighbors[0]
neighbor2 = neighbors[1]

# Set up for jinja2 template rendering
config = "template.j2"
with open(config) as t_fh:
    t_format = t_fh.read()

template_config = Template(t_format)

# Render template
with open('rendered_template.conf', "w") as rendtemplate:
    rendtemplate.write(template_config.render(**locals()))

# Call get_hostname function
get_hostname()

# Input for username and password
user = input("Please enter username: ")
passw = getpass()

# Set up napalm to push config
driver = napalm.get_network_driver('junos')
device = driver(hostname=host, username=user, password=passw)

# Napalm connecting to device
print('Connecting to device...')
device.open()

# Napalm loading rendered template and loading to device
print('Loading replacement candidate ...')
device.load_merge_candidate(filename='rendered_template.conf')

# Diffing current config with merged config
print('\nDiff:')
print(device.compare_config())

# Call check_commit function, while passing question and choices vars
check_commit(question='\nWould you like to commit these changes? (yes/no): ', choices=['yes', 'no'])

# Closing napalm connection
device.close()
