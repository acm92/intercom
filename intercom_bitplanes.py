# Adding a buffer.

import sounddevice as sd
import numpy as np
import struct
from intercom_buffer import Intercom_buffer
from intercom import Intercom

if __debug__:
    import sys

class Intercom_bitplanes(Intercom_buffer):

    def init(self, args):
        Intercom_buffer.init(self, args)
        self.packet_format = f"!HBB{self.frames_per_chunk//8}B"

    def run(self):

        self.recorded_chunk_number = 0
        self.played_chunk_number = 0

        def receive_and_buffer():
            
            #Same as intercom_buffer but adding the most significant column with an "or" operation,
            #in order to place right the column of most significant bits.
            #The operation is repeated as many columns and channels there are.
        
            message, source_address = self.receiving_sock.recvfrom(Intercom.MAX_MESSAGE_SIZE)
            chunk_number, significantCol, channelNum, *bitplane = struct.unpack(self.packet_format, message)
                  
            bitplane8 = np.asarray(bitplane, dtype = np.uint8)  
            bitplane_unpack = np.unpackbits(bitplane8)          
            bitplane16 = bitplane_unpack.astype(np.int16) 		#Unpacking and final conversion to int16
            
            #We store bitplane16 in a specific buffer and channel position 
            self._buffer[chunk_number % self.cells_in_buffer][:,channelNum] |= (bitplane16 << significantCol)
            
            return chunk_number        

        def record_send_and_play(indata, outdata, frames, time, status):
            for significantCol in range(15,-1,-1):

                #For each channel dictated by significantCol, we store all columns of each channel 
                #of that significantCol position. For instance, having bitplane 15, for each channel in that 15th position
                #we store the indata of that 15th column.
                bitArray = (indata & (1 << significantCol)) >> significantCol
                #print(indata)

                for channelNum in range(self.number_of_channels): 
                    channelArray = bitArray[:, channelNum]
                    
                    int8 = channelArray.astype(np.uint8)   #channel conversion to 8bit integer
                    channelpack8 = np.packbits(int8)       #packing
                    message = struct.pack(self.packet_format, self.recorded_chunk_number, significantCol, channelNum, *channelpack8)
                    self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))

            self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER
            chunk = self._buffer[self.played_chunk_number % self.cells_in_buffer]
            self._buffer[self.played_chunk_number % self.cells_in_buffer] = self.generate_zero_chunk()
            self.played_chunk_number = (self.played_chunk_number + 1) % self.cells_in_buffer
            outdata[:] = chunk
            #print(outdata)
            
            if __debug__:
                sys.stderr.write("."); sys.stderr.flush()

        with sd.Stream(samplerate=self.frames_per_second, blocksize=self.frames_per_chunk, dtype=np.int16, channels=self.number_of_channels, callback=record_send_and_play):
            print("-=- Press CTRL + c to quit -=-")
            first_received_chunk_number = receive_and_buffer()
            self.played_chunk_number = (first_received_chunk_number - self.chunks_to_buffer) % self.cells_in_buffer
            while True:
                receive_and_buffer()

if __name__ == "__main__":
    intercom = Intercom_bitplanes()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()