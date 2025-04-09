#!/usr/bin/bash -e

# Clone GitHub Release into home directory
wget "https://github.com/aem-eco/<<REPO NAME HERE>>/releases/latest" --directory-prefix "${ROOTFS_DIR}/home/productionUser"

# Create Desktop Shortcut for running the testware
# If more than one shortcut is needed, duplicate this section and change as needed
cat > "${ROOTFS_DIR}/home/productionUser/Desktop/Start_Test.sh" <<- "EOF"
#!/user/bin/bash
cd /home/productionUser/**REPO FOLDER NAME HERE**
source /home/productionUser/pyVenv/bin/activate
python /home/productionUser/**REPO FOLDER NAME HERE**/main.py
EOF
chmod 744 "${ROOTFS_DIR}/home/productionUser/Desktop/Start_Test.sh"
