nersc-2fa
=========

A seamless way to get a temporary ssh certificate for NERSC machines.

Installation
------------

1. Install dependencies

```
pip install pyotp keyring
```

2. Clone this repo

```
git clone https://github.com/pulkin/nersc-2fa.git
```

3. Run the script

```
./nersc-2fa.py
```

Then, enter your login, password, and the generated token seed.

**Warning!** All your login credentials will be stored plain-text in `.config/nersc-2fa.json` file. It is your responsibility to keep this file safe.

Usage
-----
```
./nersc-2fa.py
```
The script checks the certificate and updates it if needed.
