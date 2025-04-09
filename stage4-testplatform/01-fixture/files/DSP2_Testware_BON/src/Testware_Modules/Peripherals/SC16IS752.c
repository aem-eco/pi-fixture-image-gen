// -------------
// Base includes
// -------------

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <features.h>
#include <time.h>
#include <fcntl.h>          // Provides open(), O_RDWR
#include <unistd.h>         // Provides read() write()
#include <linux/i2c-dev.h>  // Provides I2C constants for ioctl: I2C_RDWR
#include <linux/i2c.h>      // Provides i2c_msg
#include <sys/ioctl.h>      // Provides ioctl()


// --------------------------------------------
// SC16IS752 Register Base Locations
// Defined in the format: <register-name>_<R/W>
// --------------------------------------------

#define RHR_R 0x00          // Receive-Holding Register
#define THR_W 0x00          // Transmit-Holdiing Register
#define IER_RW 0x01         // Interrupt Enable Register
#define FCR_W 0x02          // FIFO Control Register
#define IIR_R 0x02          // Interrupt Identification Register
#define LCR_RW 0x03         // Line Control Register
#define MCR_RW 0x04         // Modem Control Register
#define LSR_R 0x05          // Line Status Register
#define MSR_R 0x06          //
#define SPR_RW 0x07         //
#define TCR_RW 0x06         // [Accessible only when EFR[4] = logic 1, and MCR[2] = logic 1]
#define TLR_RW 0x07         // [Accessible only when EFR[4] = logic 1, and MCR[2] = logic 1]
#define TXLVL_R 0x08        // Transmit FIFO Character Count Register
#define RXLVL_R 0x09        // Receive FIFO Character Count Register
#define IODir_RW 0x0A       // GPIO Directionality Setting Register
#define IOState_RW 0x0B     // GPIO Logic State Get/Set Register
#define IOIntEN_RW 0x0C     // GPIO State Change Interrupt Enable Register
#define IOControl_RW 0x0E   // [Use bit[3] to preform software reset]
#define EFCR_RW 0x0F        // 
#define DLL_RW 0x00         // [Special Register set is accessible only when LCR[7] = logic 1 and LCR is not 0xBF]
#define DLH_RW 0x01         // [Special Register set is accessible only when LCR[7] = logic 1 and LCR is not 0xBF]
#define EFR_RW 0x02         // Enhanced Feature Register [Enhanced Features Registers are only accessible when LCR = 0xBF]
#define XON1_RW 0x04        // [Enhanced Features Registers are only accessible when LCR = 0xBF]
#define XON2_RW 0x05        // [Enhanced Features Registers are only accessible when LCR = 0xBF]
#define XOFF1_RW 0x06       // [Enhanced Features Registers are only accessible when LCR = 0xBF]
#define XOFF2_RW 0x07       // [Enhanced Features Registers are only accessible when LCR = 0xBF]


// -----------------
// Program Constants
// -----------------

#define i2c_bus 1
#define MAX_BUFF_SIZE 5120
#define MAX_CHAR_TIMEOUT 64

#define BREAK_MASK 0x40
#define FIFO_RESET_MASK 0x06
#define THR_EMPTY_MASK 0x60         // LSR[6..5] - all tx indicatiors show DONE
#define DATA_IN_RX_FIFO_MASK 0x01   // LSR[0]


// ------------------
// Function Prototyes
// ------------------

int open_i2c_fd(uint8_t bus);                                                                       // I2C Handle Functions
void close_i2c_fd(int fd);                                                                          //
void write_i2c_data(int fd, uint8_t dev_address, uint8_t dev_register, unsigned char* data_byte_array, int length);  //
void read_i2c_data(int fd, uint8_t dev_address, uint8_t dev_register, unsigned char* data_read_byte_array, int length);   //
uint8_t get_internal_register(uint8_t internal_uart_select, uint8_t base_address);                                             // SC16IS752 Handle Functions
void setup_uart(uint8_t dev_address, uint8_t internal_uart_select, uint8_t dll, uint8_t dlh, uint8_t mcr, uint8_t lcr);        //
void send_break(uint8_t dev_address, uint8_t internal_uart_select, int duration_ns);                                           //
void reset_fifos(uint8_t dev_address, uint8_t internal_uart_select, long xtal_freq);                                           //
int get_thr_empty_satus(int fd, uint8_t dev_address, uint8_t internal_uart_select);                                                    //
void transmit_data(uint8_t dev_address, uint8_t internal_uart_select, char* data_byte_array, int length, long delay_ns);                      //
uint8_t poll_line_status(int fd, uint8_t dev_address, uint8_t internal_uart_select);                                                   //
int get_rx_fifo_count(int fd, uint8_t dev_address, uint8_t internal_uart_select);                                                      //
void receive_data(uint8_t dev_address, uint8_t internal_uart_select, long delay_ns, char* master_data);                                          //
void setup_gpio(uint8_t dev_address, uint8_t internal_uart_select, uint8_t pin, uint8_t is_output);                            //
void write_gpio(uint8_t dev_address, uint8_t internal_uart_select, uint8_t pin, uint8_t high_low);                             //
uint8_t read_gpio(uint8_t dev_address, uint8_t internal_uart_select, uint8_t pin);                                             //


// ---------
// Functions
// ---------

// # ------------------- I2C Functions ------------------- # //

/// @brief Opens and gets the file-descriptor for a file at location `/dev/i2c-x` where `x` is the bus.
/// @param bus The int representing the bus number ex. 0, 1, etc
/// @return int - File Descriptor
int open_i2c_fd(uint8_t bus)
{
    char filename[12];
    snprintf(filename, 11, "/dev/i2c-%i", bus);
    int fd = open(filename, O_RDWR);
    return fd;
}


/// @brief Closes the handle to the File-Descriptor from `open_i2c_fd`
/// @param fd The int returned from an open() call
void close_i2c_fd(int fd)
{
    close(fd);
    return;
}


/// @brief Given the following params, prepend the register byte to a new buffer and write to the open i2c fd after setting up via ioctl()
/// @param dev_address 7-bit I2C slave address to write to
/// @param dev_register 8-bit I2C sub-address of the device where we want data to go (a.k.a. the register)
/// @param data_byte_array Pointer to the buffer of data we wish to write to the dev_register
/// @param length Length of the buffer to write to the i2c device @ dev_register
void write_i2c_data(int fd, uint8_t dev_address, uint8_t dev_register, unsigned char* data_byte_array, int length)
{
    unsigned char* register_buffer = malloc(length+1);
    register_buffer[0] = dev_register;
    for (int i=0; i<length; i++)
    {
        register_buffer[i+1] = data_byte_array[i];
    }

    struct i2c_msg array_of_messages[] = {
        { dev_address, 0, length+1, register_buffer }
    };

    struct i2c_rdwr_ioctl_data ioctl_messages = {
        array_of_messages,
        1
    };

    int err = ioctl(fd, I2C_RDWR, &ioctl_messages);         // Preforms N number of operations to the device with reapted start bits

    if (err < 0) {printf("ERROR WITH I2C WRITE COMMAND\n");}

    free(register_buffer);
    return;
}


/// @brief 
/// @param dev_address 7-bit I2C slave address to write to
/// @param dev_register 
/// @param length Length of the buffer to read to the i2c device @ dev_register
/// @return Pointer to buffer used to read from device - MUST BE freed() when caller is done with data
void read_i2c_data(int fd, uint8_t dev_address, uint8_t dev_register, unsigned char* data_read_byte_array, int length)
{
    unsigned char* register_buffer = malloc(1);
    register_buffer[0] = dev_register;

    struct i2c_msg device_data[] = {
        {dev_address, 0, 1, register_buffer},
        {dev_address, I2C_M_RD, length, data_read_byte_array}
    };

    struct i2c_rdwr_ioctl_data ioctl_messages = {
        device_data,
        2
    };

    int err = ioctl(fd, I2C_RDWR, &ioctl_messages);

    if (err < 0) {printf("ERROR WITH I2C READ COMMAND\n");}

    free(register_buffer);
    return;
}


// # ------------------- SC16IS752 Functions ------------------- # //

/// @brief 
/// @param internal_uart_select 
/// @param base_address 
/// @return Offset internal register address based on the used uart (A or B)
uint8_t get_internal_register(uint8_t internal_uart_select, uint8_t base_address)
{
    uint8_t channnelBits = internal_uart_select << 1;
    uint8_t baseAddressBits = base_address << 3;
    uint8_t correctedRegisterAddress = 0x00 | baseAddressBits | channnelBits;
    return correctedRegisterAddress;
}

/// @brief Given the calaculated register values to set the UART, write to the device in order specified by the datasheet to startup the UART.
/// @param dev_address 
/// @param internal_uart_select 
/// @param dll Clock Divisor Low Byte
/// @param dlh Clock Divisor High Byte
/// @param mcr Modem Control Register Value
/// @param lcr Line Control Register Value
void setup_uart(uint8_t dev_address, uint8_t internal_uart_select, uint8_t dll, uint8_t dlh, uint8_t mcr, uint8_t lcr)
{
    uint8_t corrected_LCR_address = get_internal_register(internal_uart_select, LCR_RW);
    uint8_t corrected_DLL_address = get_internal_register(internal_uart_select, DLL_RW);
    uint8_t corrected_DLH_address = get_internal_register(internal_uart_select, DLH_RW);
    uint8_t corrected_EFR_address = get_internal_register(internal_uart_select, EFR_RW);
    uint8_t corrected_MCR_address = get_internal_register(internal_uart_select, MCR_RW);
    uint8_t corrected_FCR_address = get_internal_register(internal_uart_select, FCR_W);
    uint8_t corrected_IER_address = get_internal_register(internal_uart_select, IER_RW);

    char* buffer = malloc(1 * sizeof(char));
    int fd = open_i2c_fd(i2c_bus);

    buffer[0] = 0x80;
    write_i2c_data(fd, dev_address, corrected_LCR_address, buffer, 1);

    buffer[0] = dlh;
    write_i2c_data(fd, dev_address, corrected_DLH_address, buffer, 1);

    buffer[0] = dll;
    write_i2c_data(fd, dev_address, corrected_DLL_address, buffer, 1);

    buffer[0] = 0xBF;
    write_i2c_data(fd, dev_address, corrected_LCR_address, buffer, 1);

    buffer[0] = 0x10;
    write_i2c_data(fd, dev_address, corrected_EFR_address, buffer, 1);

    buffer[0] = lcr;
    write_i2c_data(fd, dev_address, corrected_LCR_address, buffer, 1);

    buffer[0] = mcr;
    write_i2c_data(fd, dev_address, corrected_MCR_address, buffer, 1);

    buffer[0] = 0xBF;
    write_i2c_data(fd, dev_address, corrected_LCR_address, buffer, 1);

    buffer[0] = 0x00;
    write_i2c_data(fd, dev_address, corrected_EFR_address, buffer, 1);

    buffer[0] = lcr;
    write_i2c_data(fd, dev_address, corrected_LCR_address, buffer, 1);

    buffer[0] = 0x01;
    write_i2c_data(fd, dev_address, corrected_FCR_address, buffer, 1);

    buffer[0] = 0x07;
    write_i2c_data(fd, dev_address, corrected_IER_address, buffer, 1);

    free(buffer);
    close_i2c_fd(fd);
    return;
}

/// @brief 
/// @param dev_address 
/// @param internal_uart_select 
/// @param duration_ns 
void send_break(uint8_t dev_address, uint8_t internal_uart_select, int duration_ns)
{
    // get lcr register
    // write lcr with break mask
    // wait for n ms
    // write the saved lcr value to stop the break
    uint8_t lcr;
    uint8_t corrected_LCR_address = get_internal_register(internal_uart_select, LCR_RW);

    struct timespec break_time, break_remaining;
    break_time.tv_sec = 0;
    break_time.tv_nsec = duration_ns;

    int fd = open_i2c_fd(i2c_bus);

    char *read_buffer = malloc(1 * sizeof(char));
    read_i2c_data(fd, dev_address, corrected_LCR_address, read_buffer, 1);
    lcr = read_buffer[0];
    free(read_buffer);

    char *write_buffer = malloc(1 * sizeof(char));
    write_buffer[0] = lcr | BREAK_MASK;
    write_i2c_data(fd, dev_address, corrected_LCR_address, write_buffer, 1);

    nanosleep(&break_time, &break_remaining);

    write_buffer[0] = lcr;
    write_i2c_data(fd, dev_address, corrected_LCR_address, write_buffer, 1);

    free(write_buffer);
    close_i2c_fd(fd);
    return;
}

/// @brief 
/// @param dev_address 
/// @param internal_uart_select 
/// @param xtal_freq 
void reset_fifos(uint8_t dev_address, uint8_t internal_uart_select, long xtal_freq)
{
    // get fcr
    // mask with reset
    // write fcr
    // wait for 2 XTAL clocks

    uint8_t fcr;
    uint8_t corrected_fcr_address = get_internal_register(internal_uart_select, FCR_W);

    int xtal_period_ns = ((1/xtal_freq) * 100000000); // 1-period in seconds to nanoseconds

    struct timespec xtal_delay, xtal_delay_remaining;
    xtal_delay.tv_sec = 0;
    xtal_delay.tv_nsec = (xtal_period_ns * 4); // Wait for 2 XTAL clocks as per datasheet

    int fd = open_i2c_fd(i2c_bus);

    //char *read_buffer = malloc(1 * sizeof(char));
    //read_i2c_data(fd, dev_address, corrected_fcr_address, read_buffer, 1);
    //fcr = read_buffer[0];
    //free(read_buffer);

    char *write_buffer = malloc(1 * sizeof(char));
    write_buffer[0] = FIFO_RESET_MASK;
    write_i2c_data(fd, dev_address, corrected_fcr_address, write_buffer, 1);

    nanosleep(&xtal_delay, &xtal_delay_remaining);

    free(write_buffer);
    close_i2c_fd(fd);
    return;
}

/// @brief 
/// @param dev_address 
/// @param internal_uart_select 
/// @return 
int get_thr_empty_satus(int fd, uint8_t dev_address, uint8_t internal_uart_select)
{
    uint8_t corrected_LSR_address = get_internal_register(internal_uart_select, LSR_R);
    
    char* read_buffer = malloc(1 * sizeof(char));
    read_i2c_data(fd, dev_address, corrected_LSR_address, read_buffer, 1);
    int thr_status = read_buffer[0];
    free(read_buffer);

    return (thr_status & THR_EMPTY_MASK);
}

// Purpose of this function is to wrap `write_i2c_data` and wait until the TX FIFO has completed the transmit task.
// ### Order of operations:
// 1. Gets the TXFIFO register for the selected UART
// 2. Using `write_i2c_data` push the data to the appropriate register of the `SC61IS752` in use
// 3. Enter a loop where the break condition is there is no remaining chars to transmit over the serial line
//    This ensures the function blocks subsequent read(s) or operations on the `SC16IS752` until the transmit is complete.
void transmit_data(uint8_t dev_address, uint8_t internal_uart_select, char* data_byte_array, int length, long delay_ns)
{
    uint8_t corrected_TX_register = get_internal_register(internal_uart_select, THR_W);
    int thr_status;

    struct timespec delay_timer, remaining;
    delay_timer.tv_sec = 0;
    delay_timer.tv_nsec = delay_ns*32;

    int fd = open_i2c_fd(i2c_bus);

    thr_status = get_thr_empty_satus(fd, dev_address, internal_uart_select);
    write_i2c_data(fd, dev_address, corrected_TX_register, data_byte_array, length);
    thr_status = get_thr_empty_satus(fd, dev_address, internal_uart_select);

    // check the LSR instead for LSR[5] == 1
    // Datasheet says when THR is empty it is safe for the host to load more data in
    // so before continuing we want to ensure this is returned to 0

    while (thr_status < 1)
    {
        thr_status = get_thr_empty_satus(fd, dev_address, internal_uart_select);
        nanosleep(&delay_timer, &remaining);
    }

    close_i2c_fd(fd);
    nanosleep(&delay_timer, &remaining);
    return;
}

/// @brief 
/// @param dev_address 
/// @param internal_uart_select 
/// @return uint8 - 0x00 if no data to be received, 0x01 if data is ready to be received (at least 1 character)
uint8_t poll_line_status(int fd, uint8_t dev_address, uint8_t internal_uart_select)
{
    uint8_t corrected_LSR_address = get_internal_register(internal_uart_select, LSR_R);

    char* read_buffer = malloc(1);
    read_i2c_data(fd, dev_address, corrected_LSR_address, read_buffer, 1);
    int rx_data_ready = read_buffer[0];
    free(read_buffer);

    return (rx_data_ready & DATA_IN_RX_FIFO_MASK);
}

/// @brief 
/// @param dev_address 
/// @param internal_uart_select 
/// @return 
int get_rx_fifo_count(int fd, uint8_t dev_address, uint8_t internal_uart_select)
{
    uint8_t corrected_RXLVL_address = get_internal_register(internal_uart_select, RXLVL_R);

    char* read_buffer = malloc(1);
    read_i2c_data(fd, dev_address, corrected_RXLVL_address, read_buffer, 1);
    int rx_count = read_buffer[0];
    free(read_buffer);

    return rx_count;
}

/// @brief 
/// @param dev_address 
/// @param internal_uart_select 
/// @param end_of_msg_termination 
/// @param eom_length 
/// @return 
void receive_data(uint8_t dev_address, uint8_t internal_uart_select, long delay_ns, char* master_data)
{
    uint8_t corrected_RXFIFO_address = get_internal_register(internal_uart_select, RHR_R);
    int count_of_rx_chars=0, length_of_dynamic_array=0;
    uint8_t characters_ready_to_RX;
    uint16_t timeout_counter = 0;

    uint8_t existing_data = 0; // Flag to know if we need to malloc (0) or realloc (1) later

    struct timespec delay_timer, remaining;
    delay_timer.tv_sec = 0;
    delay_timer.tv_nsec = delay_ns;

    int fd = open_i2c_fd(i2c_bus);

    while ((characters_ready_to_RX < 1) && (count_of_rx_chars < 1))
    {
        characters_ready_to_RX = poll_line_status(fd, dev_address, internal_uart_select);
        count_of_rx_chars = get_rx_fifo_count(fd, dev_address, internal_uart_select);
    }

    get_FIFO_count:
        if (timeout_counter > MAX_CHAR_TIMEOUT) {goto leave_loop;}
        count_of_rx_chars = get_rx_fifo_count(fd, dev_address, internal_uart_select);

        if (count_of_rx_chars < 1)
        {
            timeout_counter ++;
            if (delay_ns > 0)
            {
                nanosleep(&delay_timer, &remaining);    // Delay may be required for low baud rates, disabled for high (ex 115200)
            }
            goto get_FIFO_count;                    // Restart the loop
        }
                                       
    if (0 == existing_data)
    {
        read_i2c_data(fd, dev_address, corrected_RXFIFO_address, master_data, count_of_rx_chars);
        length_of_dynamic_array = count_of_rx_chars;
        existing_data = 1;
    }
    else if (1 == existing_data)
    {
        read_i2c_data(fd, dev_address, corrected_RXFIFO_address, master_data+(sizeof(char)*length_of_dynamic_array), count_of_rx_chars);
        length_of_dynamic_array += count_of_rx_chars;
    }

    timeout_counter = 0;    // Reset the timeout since we just got some data
    goto get_FIFO_count;    // After getting the data, lets check back with the RXLVL register to see if more data is avaliable

    leave_loop:
        close_i2c_fd(fd);
        return;
}

/// @brief For the slected pin, set its GPIO state as input (0x00) or output (0x01)
/// @param dev_address 7-bit I2C slave address to write to
/// @param internal_uart_select Current in use UART to calculate register offsets 0x00 or 0x01 (A or B)
/// @param pin GPIO pin as per SC16IS752 datasheet range [7..0]
/// @param is_output Either 0x00 input or 0x01 output state to write to pin
void setup_gpio(uint8_t dev_address, uint8_t internal_uart_select, uint8_t pin, uint8_t is_output)
{
    // get the current port setup, mask with current pin and re-write to device

    uint8_t corrected_IODir_address = get_internal_register(internal_uart_select, IODir_RW);
    uint8_t current_port_state;
    uint8_t current_pin_state;
    uint8_t new_port_state;
    uint8_t pin_mask = 0x01 << pin;

    unsigned char *read_buffer = malloc(1 * sizeof(unsigned char));
    unsigned char *write_buffer = malloc(1 * sizeof(unsigned char));

    int fd = open_i2c_fd(i2c_bus);

    read_i2c_data(fd, dev_address, corrected_IODir_address, read_buffer, 1);
    current_port_state = read_buffer[0];

    current_pin_state = (current_port_state & pin_mask) >> pin;
    if (current_pin_state != is_output)                         
    {
        new_port_state = current_port_state ^ pin_mask;
        write_buffer[0] = new_port_state;
        write_i2c_data(fd, dev_address, corrected_IODir_address, write_buffer, 1);
    }

    free(write_buffer);
    free(read_buffer);
    close_i2c_fd(fd);
    return;
}

/// @brief For the slected pin, set its GPIO state as low (0x00) or high (0x01) for an output pin
/// @param dev_address 7-bit I2C slave address to write to
/// @param internal_uart_select Current in use UART to calculate register offsets 0x00 or 0x01 (A or B)
/// @param pin GPIO pin as per SC16IS752 datasheet range [7..0]
/// @param high_low 0x00 or 0x01 to set the output pin state low or high
void write_gpio(uint8_t dev_address, uint8_t internal_uart_select, uint8_t pin, uint8_t high_low)
{
    uint8_t corrected_IOState_address = get_internal_register(internal_uart_select, IOState_RW);
    uint8_t current_io_state;
    uint8_t current_pin_state;
    uint8_t new_io_state;
    uint8_t pin_mask = 0x01 << pin;

    int fd = open_i2c_fd(i2c_bus);

    char *read_buffer = malloc(1 * sizeof(char));
    read_i2c_data(fd, dev_address, corrected_IOState_address, read_buffer, 1);
    current_io_state = read_buffer[0];
    free(read_buffer);

    current_pin_state = (current_io_state & pin_mask) >> pin;
    if (current_pin_state != high_low)
    {
        new_io_state = current_io_state ^ pin_mask;                         // If the state is different from what we want, flip the bit
        char *write_buffer = malloc(1 * sizeof(char));                                     // Prepare a buffer and write the new port state
        write_buffer[0] = new_io_state;
        write_i2c_data(fd, dev_address, corrected_IOState_address, write_buffer, 1);
        free(write_buffer);
    }

    close_i2c_fd(fd);
    return;
}

/// @brief For the selected pin, return its state as 0x00 (Low), or 0x01 (High)
/// @param dev_address 7-bit I2C slave address to write to
/// @param internal_uart_select Current in use UART to calculate register offsets 0x00 or 0x01 (A or B)
/// @param pin GPIO pin as per SC16IS752 datasheet range [7..0]
/// @return 0x00 or 0x01 if the selected pin is Low or High accordingly
uint8_t read_gpio(uint8_t dev_address, uint8_t internal_uart_select, uint8_t pin)
{
    uint8_t corrected_IOState_address = get_internal_register(internal_uart_select, IOState_RW);
    uint8_t pin_mask;
    uint8_t pin_value;
    uint8_t port_value;

    pin_mask = 0x01 << pin;

    int fd = open_i2c_fd(i2c_bus);

    char *read_buffer = malloc(1 * sizeof(char));
    read_i2c_data(fd, dev_address, corrected_IOState_address, read_buffer, 1);
    port_value = read_buffer[0];
    free(read_buffer);

    pin_value = (port_value & pin_mask) >> pin;

    close_i2c_fd(fd);
    return pin_value;
}