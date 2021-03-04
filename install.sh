#!/bin/bash
# Print intro
echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~
 _   ___  __
| | | \ \/ /      Prayag Jain | Hax Guru
| |_| |\  /       YouTube: https://youtube.com/c/haxguru
|  _  |/  \       GitHub: https://github.com/Prayag2
|_| |_/_/\_\      Email: prayagjain2@gmail.com

~~~~~~~~~~~~~~~~~~~~~~~~~~~'
echo 'Installing konsave...'

# Copy 'konsave' to ~/.local/bin/
mkdir -p ~/.local/bin
cp ./konsave ~/.local/bin
chmod +x ~/.local/bin/konsave

# Done
echo 'Installed successfully! You can now delete this folder.'
echo "Try 'konsave -h' for more info!"
