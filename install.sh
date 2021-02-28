#!/bin/bash
# Print intro
echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~
 _   ___  __
| | | \ \/ /      Prayag Jain | Hax Guru
| |_| |\  /       YouTube: https://youtube.com/c/haxguru
|  _  |/  \       GitHub: https://github.com/Prayag2
|_| |_/_/\_\      Email: prayagjain2@gmail.com

~~~~~~~~~~~~~~~~~~~~~~~~~~~'
echo 'Installing consave...'

# Copy 'consave' to ~/.local/bin/
cp ./consave ~/.local/bin
chmod +x ~/.local/bin/consave

# Done
echo 'Installed successfully! You can now delete this folder.'
echo "Try 'consave -h' for more info!"
