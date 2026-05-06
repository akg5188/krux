# The MIT License (MIT)

# Copyright (c) 2021-2023 Krux contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#!/bin/bash

device=$1
locale=$2
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

# Create screenshots directory
rm -rf simulator/screenshots && mkdir -p simulator/screenshots

# Create an sd folder and a fresh settings.json file
mkdir -p simulator/sd && rm -f simulator/sd/settings.json
echo "{\"settings\": {\"i18n\": {\"locale\": \"$locale\"}}}" > simulator/sd/settings.json

# Create a flash folder for Amigo-local settings such as the boot PIN lock
mkdir -p simulator/flash && rm -f simulator/flash/boot_lock.json

# Create an encrypted mnemonic file to generate "Load -> From Storage" screenshots
encrypted_mnemonics="{\"d668b8b7\": {\"version\": 0, \"key_iterations\": 100000, \"data\": \"haAyMxF\
mOVkBE5QixIeJl7P0dYKVeOiuhNodO+qyI2lA+veFUxcXben1OZvKOqTbWNI2Oj8SROTpooiS/4WJdA==\"}, \"a56dfd6c\": \
{\"version\": 0, \"key_iterations\": 100000, \"data\": \"PY9fBDrqtv2ZyZF47CsZ5QucxzXmOxaJJtjkngEQTfH\
LyLgHTQ3oX8AbZR6+UXBXZUB+eSOHwJZm1jCO8AaBxQ==\"}}"
echo "$encrypted_mnemonics" > simulator/sd/seeds.json

run_simulator() {
    PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src \
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    .venv/bin/python simulator/simulator.py "$@"
}

# Sequences

# Login
run_simulator --sequence sequences/logo.txt --sd --device $device
run_simulator --sequence sequences/about.txt --sd --device $device
run_simulator --sequence sequences/self-check-login.txt --sd --device $device
run_simulator --sequence sequences/boot-lock-setup.txt --sd --device $device
run_simulator --sequence sequences/boot-lock-unlock.txt --sd --device $device
rm -f simulator/flash/boot_lock.json
run_simulator --sequence sequences/load-mnemonic-options.txt --sd --device $device
run_simulator --sequence sequences/secondary-steel-restore.txt --sd --device $device
run_simulator --sequence sequences/new-mnemonic-options.txt  --sd --device $device
run_simulator --sequence sequences/new-mnemonic-cards.txt  --sd --device $device
run_simulator --sequence sequences/new-mnemonic-hex.txt  --sd --device $device
run_simulator --sequence sequences/load-mnemonic-sequence.txt  --sd --device $device
run_simulator --sequence sequences/load-mnemonic-double-mnemonic.txt  --sd --device $device
run_simulator --sequence sequences/edit-mnemonic.txt  --sd --device $device

# Home
run_simulator --sequence sequences/home-options.txt --sd --device $device
run_simulator --sequence sequences/encrypt-mnemonic.txt --sd --device $device
run_simulator --sequence sequences/extended-public-key-wpkh.txt --sd --device $device
run_simulator --sequence sequences/extended-public-key-wsh.txt --sd --device $device
run_simulator --sequence sequences/wallet-descriptor-wsh.txt --sd --device $device
# run_simulator --sequence sequences/wallet-descriptor-wpkh.txt --sd --device $device
run_simulator --sequence sequences/wallet-descriptor-exp-tr-minis.txt  --sd --device $device
run_simulator --sequence sequences/bip85.txt --sd --device $device
run_simulator --sequence sequences/mnemonic-xor.txt --sd --device $device
run_simulator --sequence sequences/secondary-mnemonic.txt --sd --device $device
run_simulator --sequence sequences/scan-address.txt --sd --device $device
run_simulator --sequence sequences/list-address.txt --sd --device $device
run_simulator --sequence sequences/export-address.txt --sd --device $device
run_simulator --sequence sequences/sign-psbt.txt  --sd --device $device
run_simulator --sequence sequences/sign-message.txt --sd  --device $device
run_simulator --sequence sequences/sign-message-at-address.txt --sd --device $device
run_simulator --sequence sequences/self-check-home.txt --sd --device $device
run_simulator --sequence sequences/web3.txt --sd --device $device
run_simulator --sequence sequences/web3-connect-okx.txt --sd --device $device
run_simulator --sequence sequences/web3-connect-bitget.txt --sd --device $device
run_simulator --sequence sequences/web3-connect-metamask.txt --sd --device $device
run_simulator --sequence sequences/web3-connect-rabby.txt --sd --device $device
run_simulator --sequence sequences/web3-connect-tokenpocket.txt --sd --device $device
run_simulator --sequence sequences/web3-sign.txt --sd --device $device
run_simulator --sequence sequences/web3-relay-sign.txt --sd --device $device
run_simulator --sequence sequences/web3-okx-relay-sign.txt --sd --device $device
run_simulator --sequence sequences/web3-typed.txt --sd --device $device
run_simulator --sequence sequences/web3-transaction.txt --sd --device $device
run_simulator --sequence sequences/web3-typed-transaction.txt --sd --device $device

# Tools
run_simulator --sequence sequences/tools-datum-tool.txt  --sd --device $device
run_simulator --sequence sequences/tools-check-sd.txt  --sd --device $device
# run_simulator --sequence sequences/tools-create-QR.txt  --sd --device $device
# run_simulator --sequence sequences/tools-mnemonic.txt  --sd --device $device
run_simulator --sequence sequences/tools-device-tests-test-suite.txt  --sd --device $device
run_simulator --sequence sequences/tools-print-test-qr.txt  --sd --device $device
run_simulator --sequence sequences/tools-descriptor-addresses.txt --sd --device $device
run_simulator --sequence sequences/tools-flash.txt  --sd --device $device
run_simulator --sequence sequences/tc-flash-hash.txt --sd --device $device

# Settings
run_simulator --sequence sequences/all-settings.txt --sd --device $device

# Other
run_simulator --sequence sequences/qr-transcript.txt --sd --printer --device $device
run_simulator --sequence sequences/print-qr.txt --sd --printer --device $device
