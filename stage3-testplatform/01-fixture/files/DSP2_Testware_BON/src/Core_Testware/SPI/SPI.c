// -------------
// Base includes
// -------------

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <fcntl.h>              // Provides open(), O_RDWR
#include <unistd.h>             // Provides read() write()
#include <sys/ioctl.h>          // Provides ioctl()
#include <linux/spi/spidev.h>
#include <linux/spi/spi.h>
#include <linux/types.h>


// -----------------
// Program Constants
// -----------------


// ------------------
// Function Prototyes
// ------------------

int openBus(uint8_t bus_A, uint8_t bus_B);
void closeBus(int fd);

int readWriteSPI(uint8_t bus_A, uint8_t bus_B, char* rxBuffer, char* txBuffer, uint32_t bufferLen, uint32_t devClockspeed, uint32_t devSPImode);


// ---------
// Functions
// ---------

// # ------------------- SPI Functions ------------------- # //

/// @brief Open the file and return the descriptor as int
/// @param bus_A The primary SPI bus
/// @param bus_B The chip-select line to use (set by python, but linux needs one to use)
/// @return int representing the file descriptor (fd)
int openBus(uint8_t bus_A, uint8_t bus_B)
{
    // ex. /dev/spidev0.0
    char filename[15];
    snprintf(filename, 14, "/dev/spidev%i", bus_A);
    char tailend[3];
    snprintf(tailend, 3, ".%i", bus_B);
    strcat(filename, tailend);
    int fd = open(filename, O_RDWR);
    if (fd < 0) {printf("cERR:: ERROR OPENING SPI BUS DEVICE fd=(%i)\r\ncERR:: filename: %s\r\n", fd, filename); return -9999;}
    else {return fd;}
}


/// @brief Closes the open file with the system
/// @param fd File descriptor
void closeBus(int fd)
{
    close(fd);
    return;
}


/// @brief After python sets 
/// @param bus_A The primary SPI bus
/// @param bus_B The SPI bus chip-select line, not used by testware but needed for linux driver
/// @param rxBuffer 
/// @param txBuffer 
/// @param bufferLen Length of the rx & tx buffers (must be same length)
/// @param devClockspeed Override of the defualt clock speed used
/// @param devSPImode Override of the defualt SPI mode from 0..3
/// @return An int representing any error state, normal operation should be 0
int readWriteSPI(uint8_t bus_A, uint8_t bus_B, char* rxBuffer, char* txBuffer, uint32_t bufferLen, uint32_t devClockspeed, uint32_t devSPImode)
{
    // Assume python already set the DIO for CS
    // Generate SPI IOC object
    // set up with IOCTL
    // initiate data transmission

    struct spi_ioc_transfer message;
    message.tx_buf      = (unsigned long)txBuffer;
    message.rx_buf      = (unsigned long)rxBuffer;
    message.len         = bufferLen;
    message.speed_hz    = devClockspeed;
    
    int fd = openBus(bus_A, bus_B);
    int ret = 0;

    ret = ioctl(fd, SPI_IOC_WR_MODE32, &devSPImode);
    if (ret < 0) {printf("cERR:: Unable to set the SPI mode, bad IOCTL response (%i)\r\n", ret); closeBus(fd); return -9999;}

    ret = ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &devClockspeed);
    if (ret <0) {printf("cERR:: Unable to set the SPI bus speed, bad IOCTL response (%i)\r\n", ret); closeBus(fd); return -9999;}

    ret = ioctl(fd, SPI_IOC_MESSAGE(1), &message);
    if (ret < 0) {printf("cERR:: Unable to transfer SPI message, bad IOCTL response (%i)\r\n", ret); closeBus(fd); return -9999;}

    closeBus(fd);
    return 0;
}