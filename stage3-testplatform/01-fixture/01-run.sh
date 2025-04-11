#!/usr/bin/bash -e

# Clone GitHub Release into home directory
#wget "https://github.com/aem-eco/DSP2_Testware/releases/latest" --directory-prefix "${ROOTFS_DIR}/home/prod"
cp -r files/DSP2_Testware_BON "${ROOTFS_DIR}/home/prod/DSP2_Testware_BON"
on_chroot << EOF
chmod -R 766 "/home/prod/DSP2_Testware_BON"
EOF

cp -r files/DSP2_Testware_FWUpload "${ROOTFS_DIR}/home/prod/DSP2_Testware_FWUpload"
on_chroot << EOF
chmod -R 766 "/home/prod/DSP2_Testware_FWUpload"
EOF

# Create Desktop Shortcut for running the testware
# If more than one shortcut is needed, duplicate this section and change as needed
on_chroot << EOF
mkdir -p "/home/prod/Desktop"
EOF

on_chroot << EOF
touch "/home/prod/Desktop/Start_BON.sh"
cat > "/home/prod/Desktop/Start_BON.sh" <<- "EOS"
#!/user/bin/bash
cd /home/prod/DSP2_Testware_BON
source /home/prod/pyVenv/bin/activate
python /home/prod/DSP2_Testware_BON/main.py
EOS
chmod 744 "/home/prod/Desktop/Start_BON.sh"

touch "/home/prod/Desktop/Start_FWUpload.sh"
cat > "/home/prod/Desktop/Start_FWUpload.sh" <<- "EOS"
#!/user/bin/bash
cd /home/prod/DSP2_Testware_FWUpload
source /home/prod/pyVenv/bin/activate
python /home/prod/DSP2_Testware_FWUpload/main.py
EOS
chmod 744 "/home/prod/Desktop/Start_FWUpload.sh"
EOF
