#!/usr/bin/env python
import pyotp
import keyring
import requests
import os
import json
import getpass

import subprocess
import tempfile
from datetime import datetime

config_file = os.path.expanduser("~/.config/nersc-2fa.json")

def load_config(fname):
    with open(fname, 'r') as f:
        config = json.load(f)
    return config["user"], keyring.get_password(config['target'], config['user']), config["url"], config["seed"], config["target"]

def save_config(fname, user, password, url, seed, target):
    keyring.set_password(target, user, password)
    with open(fname, 'w') as f:
        json.dump(dict(user=user, url=url, seed=seed, target=target), f, indent=2)

try:
    user, password, url, seed, target = load_config(config_file)
    print("Configuration read from {}".format(config_file))

except Exception as e:

    # === User === #
    default_user = getpass.getuser()
    user = raw_input("User (default: {}): ".format(default_user))
    if user == "":
        user = default_user

    # === Password === #
    password = getpass.getpass()

    # === Seed === #
    while True:
        seed = raw_input("Token seed: ")
        try:
             pyotp.TOTP(seed).now()
        except:
            print("This is not a valid token.")
        else:
            break

    # === Target === #
    default_target = "nersc"
    target = raw_input("Target file name (default: {}): ".format(default_target))
    if target == "":
        target = default_target

    # === URL === #
    default_url = 'https://sshproxy.nersc.gov/create_pair/default/'
    while True:
        url = raw_input("Target URL (default: {}): ".format(default_url))
        if url == "":
            url = default_url
        try:
            if requests.post(url).status_code == 401:
                break
            else:
                print("Not a valid URL: does not return 401")
        except:
            print("Not a valid URL: exception occurs")

    save_config(config_file, user, password, url, seed, target)
    print("Saved configuration to {}".format(config_file))

def get_cert(user, password, seed):
    r = requests.post(url, auth=(user, password + pyotp.TOTP(seed).now()))
    if r.status_code == 401:
        raise RuntimeError("Failed to authenticate. Server response:\n{0.text}".format(r))
    elif r.status_code == 200:
        return r.text
    else:
        raise RuntimeError("HTTP error {0.status_code:d} {0.reason}. Server response:\n{0.text}".format(r))

def deploy_cert(cert, location):
    with open(location, 'w') as f:
        f.write(cert)
    os.chmod(location, 0600)

def is_cert_valid(location):
    if not os.path.isfile(location):
        return False
    with open(location, 'r') as f:
        text = f.read()
        if "ssh-rsa" not in text:
            return False
        text = text[text.find("ssh-rsa"):]
    tfile = tempfile.NamedTemporaryFile()
    tfile.write(text)
    tfile.flush()
    output = subprocess.check_output(["ssh-keygen", "-L", "-f", tfile.name])
    if "Valid" not in output:
        return False
    output = output[output.find("Valid"):]
    output = output[output.find("to")+3:output.find("\n")]
    t = datetime.strptime(output, "%Y-%m-%dT%H:%M:%S")
    return t > datetime.now()

cert_location = os.path.expanduser("~/.ssh/" + target)

if not is_cert_valid(cert_location):
    print("Updating certificate ...")
    deploy_cert(get_cert(user, password, seed), cert_location)
else:
    print("The certificate is still valid, nothing to do")
