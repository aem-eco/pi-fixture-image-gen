################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: LT26T.py
# | Date: 2025-03-18
# | Rev: 1.1
# | Change By: Everly Larche
# | ECO Ref: LXP-371
#  ----------------
# | Project Name: DSP2 Bed-of-Nails
# | Developer: Everly Larche
# | File Description: A translation/formatting layer for NMEA messages to Quectel GPS IC using RS232
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

## IMPORTS ##
from src.Testware_Modules.Protocols.RS232 import RS232

from dataclasses import dataclass
from typing import List
import time

################################################################

## CLASS DEFINITION AND METHODS ##
class NMEA:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # NMEA Message
    Provides the constants and basic structure of a NMEA message.
    Also provides methods for calculating and checking the NMEA checksum.
    """

    SENTENCE_START:str      = "$"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Denotes the start of a NMEA message string.
    """

    FIELD_DELIMINTER:str    = ","
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Data field delimiter within the NMEA message string.
    """

    CHECKSUM_IDENTIFIER:str = "*"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Identifies the start of the checksum portion of the NMEA string.
    """

    SENTENCE_END:str        = "\r\n"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Denotes the end of the NMEA message.
    """

    @dataclass
    class Message:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        talkerID:str
        sentenceFormatter:str
        fields:List[str]
        checksum:str|None=None

    
    def __init__(self) -> None:
        return None
    

    def formatMessage(self, message:Message) -> str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param message: The `NMEA.Message` datatype containing all the required elements to construct the final NMEA string.
        """

        nmeaMessage:str = ""
        nmeaMessage += self.SENTENCE_START
        nmeaMessage += message.talkerID
        nmeaMessage += message.sentenceFormatter
        for field in message.fields:
            nmeaMessage += (self.FIELD_DELIMINTER + field)
        nmeaMessage += self.CHECKSUM_IDENTIFIER
        nmeaMessage += message.checksum[2:]
        nmeaMessage += self.SENTENCE_END

        return nmeaMessage
    

    def _checksumCalc(self, stringToCalc:str, existingChecksumValue:int|None=None) -> str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.1

        :param stringToCalc: The portion of the string to be used for checksum calculation as described in NMEA-0183
        :param existingChecksumValue: Used if we are checking a response. This should be the int representation of the checksum portion of the NMEA string.

        :returns: The checksum (exclusive-or) value calculated. For message checks this should be identical to the passed checksum value.
        """

        checksum:int = 0

        for character in stringToCalc:
            checksum = (checksum ^ ord(character))

        return hex(checksum)
    

    def generateChecksum(self, message:Message) -> Message:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :params message: the `NMEA.Message` object who needs a checksum applied
        :returns: The same `NMEA.Message` with the checksum field filled. If the field was already filled, it is overwritten.

        ## Create the NMEA Message Checksum
        NMEA Checksums are calculated with an EXCLUSIVE OR of all characters including the field delimiter, between
        but not including the sentence start character and the checksum field character (ex between the `$` and `*`).

        This checksum is 8-bits long.

        Source: L26-DR&L26-P&L26-T&LC98S_Series_GNSS_Protocol_Specification.pdf page 12
        """

        stringToCaluclate:str = message.talkerID + message.sentenceFormatter
        for field in message.fields:
            stringToCaluclate += (self.FIELD_DELIMINTER + field)

        message.checksum = self._checksumCalc(stringToCaluclate)

        return message
    

    def calculateValidChecksum(self, message:str) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param message: The received NMEA-style message as a string

        :returns bool: Either True if the checksum is valid or False if invalid.

        ## Check the Received Checksum is Valid
        Works in the same way as the generator, taking the applicable portion of the message,
        preform an exclusive-oring on each character. The result should be the same as the input.
        """

        # Remove the '$' and anything after (inclusive) of the '*'
        partialString:str = message[1:].split(self.CHECKSUM_IDENTIFIER, 1)
        receivedChecksum:str = partialString[1]
        calculated = self._checksumCalc(partialString[0])[2:]

        return (receivedChecksum == calculated)


class Quectel_Serial(RS232):
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # Quectel Serial Communications
    Using `RS232` as the base class, apply additional functionality of message formatting or post-processing.

    This class will disable the periodic messge outputs of the Quectel to ensure
    data is transmitted and received cleanly. Outputs will be re-enabled after funtion calls.
    """

    SUPPLIER_TALKER_ID:str = "PSTM"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The Quectel NMEA message supplier ID for manufacturing commands.
    """

    QUECTEL_L26_T_S89_BAUD:int = 115200
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The defualt baud rate of the L26-T-S89 as per the product information guide.
    """

    QUECTEL_L26_T_S89_DATABITS:int = 8
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The defualt byte size of the L26-T-S89 as per the typical setup in the NMEA-0183 spec.
    """

    QUECTEL_L26_T_S89_PARITY:str = RS232.PARITY_NONE
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The defualt parity setting of the L26-T-S89 as per the typical setup in the NMEA-0183 spec.
    """

    QUECTEL_L26_T_S89_STOPBITS:int = 1
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The defualt number of stopbits of the L26-T-S89 as per the typical setup in the NMEA-0183 spec.
    """

    PERIODIC_MESSAGE_DISABLE_HIGH:str = "00000000"
    """
    .. versionadded:: 1.1
    .. versionchanged:: 1.1

    See datasheet pg. 81 for more information.
    """

    PERIODIC_MESSAGE_DESIABLE_LOW:str = "00000000"
    """
    .. versionadded:: 1.1
    .. versionchanged:: 1.1

    See datasheet pg. 81 for more information.
    """

    PERIODIC_MESSAGE_DISABLE_RATE:str = "1"
    """
    .. versionadded:: 1.1
    .. versionchanged:: 1.1

    The rate of the NMEA 2 list, using the same for NMEA 1.
    See datasheet pg. 81 for more information.
    """

    PERIODIC_MESSAGE_LIST_ID:str = "0"
    """
    .. versionadded:: 1.1
    .. versionchanged:: 1.1

    The ID of the CFGMSGL to affect. 0 == NMEA list for 1Hz messages.
    See datasheet pg. 81 for more information.
    """

    L26T_FACTORY_RESET_CMD:str = "$PSTMRESTOREPAR*11\r\n"
    L26T_SAVE_PARAMETER_CMD:str = "$PSTMSAVEPAR*58\r\n"
    L26T_REBOOT_CMD:str = "$PSTMSRR*49\r\n"

    L26T_RESET_ACKN:str = "PSTMRESTOREPAROK"

    PERIODIC_MESSAGE_ENABLE_DESFUALT:NMEA.Message = NMEA.Message(
        talkerID =          SUPPLIER_TALKER_ID,
        sentenceFormatter = "CFGMSGL",
        fields = [
            PERIODIC_MESSAGE_LIST_ID,
            PERIODIC_MESSAGE_DISABLE_RATE,
            "0x00180056",
            "0x7ec20010"
        ]
    )


    def __init__(self, uartAddress:int) -> None:
        # Initialize the RS232 and UART levels to communicate with device
        super().__init__(
            address = uartAddress,
            baudRate = self.QUECTEL_L26_T_S89_BAUD,
            byteSize = self.QUECTEL_L26_T_S89_DATABITS,
            parity = self.QUECTEL_L26_T_S89_PARITY,
            stopBits = self.QUECTEL_L26_T_S89_STOPBITS,
            uartARS232Lvl=True,
            uartBRS232Lvl=True
        )

        self.internalUARTsel:int = 1
        self.chattyModeDisabled:bool = False
        self.NMEA = NMEA()
        return None
    

    def _get1HzMessageConfig(self) -> str:
        """
        
        """

        raise NotImplementedError("Not implimented. Class will only SET the configuration.")
    

    def _set1HzMessageConfig(self, disable:bool=True) -> None:
        """
        .. versionadded:: 1.1
        .. versionchanged:: 1.1
        """

        _defualt:NMEA.Message = self.PERIODIC_MESSAGE_ENABLE_DESFUALT
        _defualt = self.NMEA.generateChecksum(_defualt)
        _defualtString:str = self.NMEA.formatMessage(_defualt)

        _disabled:NMEA.Message = NMEA.Message(
            talkerID = self.SUPPLIER_TALKER_ID,
            sentenceFormatter = "CFGMSGL",
            fields = [
                self.PERIODIC_MESSAGE_LIST_ID,
                self.PERIODIC_MESSAGE_DISABLE_RATE,
                self.PERIODIC_MESSAGE_DESIABLE_LOW,
                self.PERIODIC_MESSAGE_DISABLE_HIGH
            ]
        )
        _disabled = self.NMEA.generateChecksum(_disabled)
        _disabledString:str = self.NMEA.formatMessage(_disabled)

        if disable:
            self.sendCmd(_disabledString, activeUART=self.internalUARTsel)
        elif not disable:
            self.sendCmd(_defualtString, activeUART=self.internalUARTsel)

        self.sendCmd(self.L26T_SAVE_PARAMETER_CMD, activeUART=self.internalUARTsel) # SAVE
        self.sendCmd(self.L26T_REBOOT_CMD, activeUART=self.internalUARTsel)     # RESET
        time.sleep(2)   # Wait for the device to complete SW RESET

        return None
    

    def _checkMessageListDisable(func) -> object:
        """
        .. versionadded:: 1.1
        .. versionchanged:: 1.1
        """

        def wrapper(*args):
            if not args[0].chattyModeDisabled:
                args[0]._set1HzMessageConfig()
                args[0].receiveASAP(args[0].internalUARTsel) # clear rx fifo
                args[0].chattyModeDisabled = True
            else:
                pass
            
            return func(*args)

        return wrapper


    @_checkMessageListDisable
    def getVersionInfo(self) -> str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns: Part of the NMEA reply continaing the version information.

        ## Reading the Version Information from the Quectel GPS IC
        Designed for the L26-T-S89.

        This method constructs the `NMEA.Message` object, gets the NMEA string and sends it via
        the RS232 base class. After receiving the message, split the string to isolate the desired field value.
        """

        message:NMEA.Message = NMEA.Message(
            talkerID = self.SUPPLIER_TALKER_ID,
            sentenceFormatter = "GETPAR",
            fields = ["1500"]
        )

        message = self.NMEA.generateChecksum(message)
        rawStringToSend:str = self.NMEA.formatMessage(message)

        self.sendCmd(rawStringToSend, activeUART=self.internalUARTsel)
        rawStringResponse = self.receiveASAP(self.internalUARTsel)
        if "-9999" == rawStringResponse: return rawStringResponse
        else: rawStringResponse = rawStringResponse.split("\r\n")[0] # The return message includes the command after the response. This removes the cmd.

        if not self.NMEA.calculateValidChecksum(rawStringResponse): raise BufferError(f"Received buffer: {rawStringResponse} contains an invlaid checksum or message body!")

        rawStringResponse = rawStringResponse.split(NMEA.FIELD_DELIMINTER)[2]
        rawStringResponse = rawStringResponse.split(NMEA.CHECKSUM_IDENTIFIER)[0]

        return rawStringResponse
    

    @_checkMessageListDisable
    def getAntennaStatus(self) -> str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns: A string of any of the following: 'Connected', 'Disconnected', 'Invalid Impedance', 'Error'.

        ## Reading the Status of the Quectel Antenna Connection
        This method will construct a `NMEA.Message` and transact the data via the in herited RS232 class.
        When the reply is received, the NMEA string is isolated for the `<AntStatus>` field and a return value is determined
        from this field.


        See below for a table of the possible status conditions:
        
        | Status String | Anetnna Condition | Quectel Code |
        | ------------- | ----------------- | ------------ |
        | Connected | Normal operation | 0 |
        | Disconnected | Antenna Unitialized | -1 |
        | Invalid Impedance | Open/Short | 1/2 | 
        """

        message:NMEA.Message = NMEA.Message(
            talkerID = self.SUPPLIER_TALKER_ID,
            sentenceFormatter = "CFGMSGL",
            fields = ["0", "1", "00000000", "00000010"]
        )

        message = self.NMEA.generateChecksum(message)
        rawStringToSend:str = self.NMEA.formatMessage(message)
        self.sendCmd(rawStringToSend, self.internalUARTsel)
        self.sendCmd(self.L26T_SAVE_PARAMETER_CMD, self.internalUARTsel)
        self.sendCmd(self.L26T_REBOOT_CMD, self.internalUARTsel)
        time.sleep(5)
        self.receiveASAP(self.internalUARTsel)

        rawStringResponse:str = self.receiveASAP(self.internalUARTsel)
        if "-9999" == rawStringResponse: return "-9999"
        rawStringResponse = rawStringResponse[:-2] # Remove <CR><LF>
        if not self.NMEA.calculateValidChecksum(rawStringResponse): raise BufferError(f"Received buffer: {rawStringResponse} contains an invlaid checksum or message body!")

        status:int = int(rawStringResponse.split(NMEA.FIELD_DELIMINTER)[1])

        match status:
            case 0:
                return "Connected"
            case -1:
                return "Disconnected"
            case 1|2:
                return "Invalid Impedance"
            case _:
                return "Error"
            

    def resetToFactory(self) -> str:
        """
        .. versionadded:: 1.1
        .. versionchanged:: 1.1
        """

        self.receiveASAP(self.internalUARTsel) # reset rx fifo

        self.sendCmd(self.L26T_FACTORY_RESET_CMD, self.internalUARTsel)
        # ensure the L26T ACKN the reset cmd
        reply:str = self.receiveASAP(self.internalUARTsel)
        if self.L26T_RESET_ACKN not in reply:
            raise ValueError("UNABLE TO RESET L26T to FACTORY, COULD NOT FIND 'OK' IN REPLY. ABORTING.")
        else:
            self.sendCmd(self.L26T_REBOOT_CMD, self.internalUARTsel)
            return "RESET"

################################################################

## OTHER CODE ##

################################################################

# EOF