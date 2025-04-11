#!/usr/bin/bash -e

# Ensure a desktop folder is made
install -v --owner ${FIRST_USER_NAME} -g 1000 -m 666 -d "${ROOTFS_DIR}/home/Desktop"

# Create copies of the test code in the new file-system
# Also create desktop shortcuts to each of the applicable main.py files, starting their pyVenv
for package in $TESTWARE_FOLDER_NAMES
do
    install -v --owner ${FIRST_USER_NAME} -g 1000 -m 766 -D "${ROOTFS_DIR}/home/${package}" -t "files/${package}/*"

    on_chroot << EOF
    touch "/home/${FIRST_USER_NAME}/Desktop/Start_${package}.sh"
    cat > "/home/${FIRST_USER_NAME}/Desktop/Start_${package}.sh" <<- "EOS"
    cd /home/${FIRST_USER_NAME}/${package}
    source /home/${FIRST_USER_NAME}/pyVenv/bin/activate
    python3.11 /home/${FIRST_USER_NAME}/${package}/main.py
    EOS

    chmod 766 "/home/${FIRST_USER_NAME}/Desktop/Start_${package}.sh"
    chown "/home/${FIRST_USER_NAME}/Desktop/Start_${package}.sh" ${FIRST_USER_NAME}
EOF
done
