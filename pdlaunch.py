# Proxmox Desktop Launcher
# Requires Python 3+ (was written against 3.9) and the 'requests' module
# Try 'pip install requests' or 'python -m pip install requests

### USER CONFIGURABLE VARIABLES ###

# Sometimes we'll get a random Invalid CSRF Token error, this is how many times we'll retry before failing
attempts = 5

# Path of the temp directory where we should store the VV file
# On *nix systems this will probably be /tmp
# On recent Windows systems this will probably be C:/Users/[your username here]/AppData/Local/Temp
# Remember to use forward slashes for windows paths
temp = '/tmp'

# Path to your remote-viewer executable, including the filename
viewer = '/usr/bin/virt-viewer'

# Start viewer in fullscreen? True/False
fullscreen = True

### DO NOT EDIT BELOW THIS LINE ###

# Imports
import sys
import requests
import subprocess

# Present credentials to proxy, get a ticket and a token
def get_ticket(host,username,password):
    post_data = {'username':username,'password':password}
    uri = 'https://'+host+':8006/api2/json/access/ticket'
    response = requests.post(uri, data=post_data, verify=False)
    return([response.json()['data']['ticket'],response.json()['data']['CSRFPreventionToken']])

# Use the ticket we just got to retrieve the config for the VM we want to connect to
def get_proxy_config(node,proxy,vmid,ticket):
    cookies = {'PVEAuthCookie':ticket[0]}
    headers = {'CSRFPreventionToken':ticket[1]}
    data = {'proxy':proxy}
    uri = 'https://'+proxy+':8006/api2/json/nodes/'+node+'/qemu/'+vmid+'/spiceproxy'
    response = requests.post(uri, headers=headers, cookies=cookies, data=data, verify=False)
    return(response)

# Write the config out to a temporary file and point remote-viewer at it
def write_and_start(output,temp,viewer,fullscreen):
    temp = temp + "/pdlaunch.vv"
    outputfile = open(temp, "w")
    outputfile.write("[virt-viewer]\n")
    for key in output:
        outputfile.write(str(key) + '=' + str(output[key]) + '\n')
    outputfile.close()
    args = []

    # Build the viewer command to execute
    args.append(viewer)
    if fullscreen: args.append('-f')
    args.append(temp)

    # Start the viewer
    viewer_start = subprocess.Popen(args)

# MAIN
# Check to make sure we got the right (or at least the right number of) arguments
if len(sys.argv) == 6:
    # Make the specified number of attempts, getting a fresh ticket and CSRF token each time
    while attempts > 0:
        ticket = get_ticket(sys.argv[3],sys.argv[1],sys.argv[2])
        proxy_config = get_proxy_config(sys.argv[3],sys.argv[4],sys.argv[5],ticket)
        if "200" in str(proxy_config):
            write_and_start(proxy_config.json()['data'],temp,viewer,fullscreen)
            break
        else:
            print("Connection attempt failed, retrying.")
            attempts = attempts-1
else:
    print("Usage: pdlaunch.py [username@context] [password] [node] [proxy] [vmid]")