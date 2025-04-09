#!/usr/bin/bash -e

# Clone GitHub Release into home directory
#wget "https://github.com/aem-eco/DSP2_Testware/releases/latest" --directory-prefix "${ROOTFS_DIR}/home/productionUser"
cp -r files/DSP2_Testware_BON "${ROOTFS_DIR}/home/productionUser/DSP2_Testware_BON"
chmod -r 766 "${ROOTFS_DIR}/home/productionUser/DSP2_Testware_BON"

# Create Desktop Shortcut for running the testware
# If more than one shortcut is needed, duplicate this section and change as needed
cat > "${ROOTFS_DIR}/home/productionUser/Desktop/Start_BON.sh" <<- "EOF"
#!/user/bin/bash
cd /home/productionUser/DSP2_Testware_BON
source /home/productionUser/pyVenv/bin/activate
python /home/productionUser/DSP2_Testware_BON/main.py
EOF
chmod 744 "${ROOTFS_DIR}/home/productionUser/Desktop/Start_BON.sh"
