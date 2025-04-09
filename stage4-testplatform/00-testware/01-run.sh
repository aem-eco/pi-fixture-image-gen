#!/usr/bin/bash -e

# Create home folders required for testware
mkdir -p "${ROOTFS_DIR}/home/productionUser/LocalReports"
mkdir -p "${ROOTFS_DIR}/home/productionUser/Testware_Logs"
mkdir -p "${ROOTFS_DIR}/home/productionUser/AEM_Firmware"

# Create the files for desktop config with permissions
install -m 644 files/pcmanfm.conf "${ROOTFS_DIR}/home/productionUser/.config/pcmanfm/LXDE-pi/"
install -m 644 files/desktop-items-NOOP-1.conf "${ROOTFS_DIR}/home/productionUser/.config/pcmanfm/LXDE-pi/"

# Files needed for STM32 Programmer
mkdir -p "${ROOTFS_DIR}/home/STM32CubeProgrammer"
cp -r "files/STM32CubeProgrammer" "${ROOTFS_DIR}/home/STM32CubeProgrammer"
chmod 744 "${ROOTFS_DIR}/home/STM32CubeProgrammer/bin/STM32_Programmer_CLI"

# Create python venv and install API key file
# activation of the venv and installation of packages
python -m venv "${ROOTFS_DIR}/home/productionUser/pyVenv"
source "${ROOTFS_DIR}/home/productionUser/pyVenv/bin/activate"
pip install pip --upgrade --no-input
pip install cython --no-input
pip install gpiod --no-input
pip install pyinstrument --no-input
pip install pyserial --no-input
pip install regex --no-input
pip install requests --no-input
pip install termcolor --no-input
install -m 644 files/_env_vars.pth "${ROOTFS_DIR}/home/productionUser/pyVenv/lib/python3.11/site-packages/_env_vars.pth"
deactivate

# Install the first run shell script to run on the first OS boot
# Runs the tasks that require the OS to be built
install -m 777 files/firtrun.sh "${ROOTFS_DIR}/boot/firmware/firstrun.sh"
