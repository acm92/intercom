# Implementing a Data-Flow Control algorithm.

import sounddevice as sd
import numpy as np
import struct

from intercom_binaural import Intercom_binaural

if __debug__:
    import sys

class Intercom_dfc(Intercom_binaural):

    def init(self, args):
        
		Intercom_binaural.init(self, args)
		self.send_packet_format = f"!HB{self.frames_per_chunk//8}B"
        
		#Firstly, We establish the number of bitplanes sent
		#After that, we declare the current chunk number
		#Finally, the declaration of bitplanes received per chunk
        self.number_of_bitplanes = 16*self.number_of_channels
        self.current_chunk_number = 0
        self.bitplane_recieved = 0
		

	def receive_and_buffer(self):
        
		message, source_address = self.receiving_sock.recvfrom(Intercom_binaural.MAX_MESSAGE_SIZE)
        
		#Assign to each variable the packet received
        chunk_number, bitplane_number, *bitplane = struct.unpack(self.packet_format, message)
        
		#Variable bitplane to format the received array
        bitplane = np.asarray(bitplane, dtype=np.uint8)
        
		#Unpacking bits in the original indata format
        bitplane = np.unpackbits(bitplane)
		
        #Format array to int16
        bitplane = bitplane.astype(np.int16)
		
  
		#Save the chunk in the respective bitplane. We use OR operator to store in our bidimensional array correctly.
		#Otherwise, we would overwrite values in columns which we don't want to.
		self._buffer[chunk_number % self.cells_in_buffer][:, bitplane_number%self.number_of_channels] |= (bitplane << bitplane_number//self.number_of_channels)
        

        #If a change of chunk occurred
		if(current_chunk_number] < chunk_number):
            
			#If we have received less bitplanes in the current chunk than in the previous chunk, 
			#we update the number of bitplanes that must be sent in the next chunk 
			#computing a weighted average with the received and sent bitplanes.
			
			#We need to check if the received number of bitplanes is less than the previous chunk
			#If that's the case, we increase said number that will be sent the nect chunk
			#...

        self._buffer[chunk_number % self.cells_in_buffer][:, bitplane_number%self.number_of_channels] |= (bitplane << bitplane_number//self.number_of_channels)

        return chunk_number
		
		
		#Legacy from intercom_binaural
    def record_send_and_play_stereo(self, indata, outdata, frames, time, status):
        indata[:,0] -= indata[:,1]
        self.record_and_send(indata)
        self._buffer[self.played_chunk_number % self.cells_in_buffer][:,0] += self._buffer[self.played_chunk_number % self.cells_in_buffer][:,1]
        self.play(outdata)

    def record_and_send(self, indata):
        
        self.saved[self.played_chunk_number % self.cells_in_buffer] = 0
        
		for bitplane_number in range(self.number_of_channels*16-1, -1, -1):
           
            #Declare variable with the bits we need from indata. If a negative bit is encountered, with & 1 no more ones are moved
			bitplane = (indata[:, bitplane_number%self.number_of_channels] >> bitplane_number//self.number_of_channels) & 1
            
			#Format to unsigned 8 bit
            bitplane = bitplane.astype(np.uint8)
            
			#Packing array
            bitplane = np.packbits(bitplane)
            
			#Building the message with all needed information
            message = struct.pack(self.packet_format, self.recorded_chunk_number, bitplane_number, *bitplane)
            
			#Sending message
            self.sending_sock.sendto(message, (self.destination_IP_addr, self.destination_port))
		
		#Increased +1 the number of chunks sent when all bitplanes sent 
        self.recorded_chunk_number = (self.recorded_chunk_number + 1) % self.MAX_CHUNK_NUMBER
	
	
	def play(self, outdata):
        chunk = self._buffer[self.played_chunk_number % self.cells_in_buffer]
        self._buffer[self.played_chunk_number % self.cells_in_buffer] = self.generate_zero_chunk()
        self.played_chunk_number = (self.played_chunk_number + 1) % self.cells_in_buffer
        outdata[:] = chunk
        
		if __debug__:
            sys.stderr.write("."); sys.stderr.flush()

if __name__ == "__main__":
    intercom = Intercom_dfc()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()