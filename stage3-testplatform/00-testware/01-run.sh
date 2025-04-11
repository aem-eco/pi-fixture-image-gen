#!/usr/bin/bash -e

# Create home folders required for testware
install -v -o 1000 -g 1000 -d "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/LocalReports"
install -v -o 1000 -g 1000 -d "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/Testware_Logs"
install -v -o 1000 -g 1000 -d "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/AEM_Firmware"

# Create the files for desktop config with permissions
install -m 644 "files/wallpaper.png" "${ROOTFS_DIR}/usr/share/aem-defualt-wallpaper/wallpaper.png"
install -v -o 1000 -g 1000 -d "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/.config/pcmanfm/LXDE-pi/"
install -v -o 1000 -g 1000 -m 666 "files/desktop-items-NOOP-1.conf" "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/.config/pcmanfm/LXDE-pi/desktop-items-NOOP-1.conf"
install -v -o 1000 -g 1000 -m 666 "files/pcmanfm.conf" "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/.config/pcmanfm/LXDE-pi/pcmanfm.conf"

# Files needed for STM32 Programmer
install -v -o 1000 -g 1000 -m 766 -D "${ROOTFS_DIR}/home/STM32CubeProgrammer" -t "/home/Test-Measurement-AEM/stm32cubeprog-linux-arm/STM32CubeProgrammer/*"

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
install -v -o 1000 -g 1000 -m 666 files/_env_vars.pth "${ROOTFS_DIR}/home/prod/pyVenv/lib/python3.11/site-packages/_env_vars.pth"

# Install the first run shell script to run on the first OS boot
# Runs the tasks that require the OS to be built
#install -m 777 files/firtrun.sh "${ROOTFS_DIR}/boot/firmware/firstrun.sh"
