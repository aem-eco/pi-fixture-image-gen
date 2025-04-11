#!/usr/bin/bash -e

# Create home folders required for testware
on_chroot << EOF
mkdir -p "/home/prod/LocalReports"
mkdir -p "/home/prod/Testware_Logs"
mkdir -p "/home/prod/AEM_Firmware"
EOF

# Create the files for desktop config with permissions
on_chroot << EOF
mkdir -p "/home/prod/.config/pcmanfm/LXDE-pi"
EOF
install -m 644 files/pcmanfm.conf "${ROOTFS_DIR}/home/prod/.config/pcmanfm/LXDE-pi/"
install -m 644 files/desktop-items-NOOP-1.conf "${ROOTFS_DIR}/home/prod/.config/pcmanfm/LXDE-pi/"

# Files needed for STM32 Programmer
#on_chroot << EOF
#mkdir -p "/home/STM32CubeProgrammer"
#EOF
cp -r "/home/Test-Measurement-AEM/stm32cubeprog-linux-arm/STM32CubeProgrammer" "${ROOTFS_DIR}/home"
on_chroot << EOF
chmod 744 "/home/STM32CubeProgrammer/bin/STM32_Programmer_CLI"
EOF

# Create python venv and install API key file
# activation of the venv and installation of packages
on_chroot << EOF
/usr/bin/python3.11 -m venv "/home/prod/pyVenv"
source "/home/prod/pyVenv/bin/activate"
pip install pip --upgrade --no-input
pip install cython --no-input
pip install gpiod --no-input
pip install pyinstrument --no-input
pip install pyserial --no-input
pip install regex --no-input
pip install requests --no-input
pip install termcolor --no-input
deactivate
EOF
install -m 644 files/_env_vars.pth "${ROOTFS_DIR}/home/prod/pyVenv/lib/python3.11/site-packages/_env_vars.pth"

# Install the first run shell script to run on the first OS boot
# Runs the tasks that require the OS to be built
#install -m 777 files/firtrun.sh "${ROOTFS_DIR}/boot/firmware/firstrun.sh"
