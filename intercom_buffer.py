import sounddevice as sd                                                        # https://python-sounddevice.readthedocs.io
import numpy                                                                    # https://numpy.org/
import argparse                                                                 # https://docs.python.org/3/library/argparse.html
import socket                                                                   # https://docs.python.org/3/library/socket.html
import queue     

from intercom import Intercom

if __debug__:
    import sys

class Intercom_buffer(Intercom):

    def init(self, args):
        Intercom.init(self, args)

    def run(self):
        sending_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiving_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listening_endpoint = ("0.0.0.0", self.listening_port)
        receiving_sock.bind(listening_endpoint)

        l = list()  #We use list instead of a Queue, in order to perform the sort() method. 

        def receive_and_buffer():
            message, source_address = receiving_sock.recvfrom(Intercom.max_packet_size)
            l.append(message)     #The element is indexed at the end of the list
            l.sort(reverse=True)        #We sort the list in descending order 
            
        def record_send_and_play(indata, outdata, frames, time, status):
            sending_sock.sendto(indata, (self.destination_IP_addr, self.destination_port))
            try:
                message = l[-1]         #We extract the last element of the list
            except IndexError:          #If the list is empty
                message = numpy.zeros((self.samples_per_chunk, self.number_of_channels), self.dtype)
            outdata[:] = numpy.frombuffer(message, numpy.int32).reshape(self.samples_per_chunk, self.number_of_channels)
            if __debug__:
                sys.stderr.write("."); sys.stderr.flush()

        with sd.Stream(samplerate=self.samples_per_second, blocksize=self.samples_per_chunk, dtype=self.dtype, channels=self.number_of_channels, callback=record_send_and_play):
            print('-=- Press <CTRL> + <C> to quit -=-')
            while True:
                receive_and_buffer()


    def add_args(self):
        parser = argparse.ArgumentParser(description="Real-time intercom", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument("-s", "--samples_per_chunk", help="Samples per chunk.", type=int, default=1024)
        parser.add_argument("-r", "--samples_per_second", help="Sampling rate in samples/second.", type=int, default=44100)
        parser.add_argument("-c", "--number_of_channels", help="Number of channels.", type=int, default=2)
        parser.add_argument("-b", "--bytes_per_sample", help="Depth in bytes of the samples of audio.", type=int, default=2)
        parser.add_argument("-p", "--mlp", help="My listening port.", type=int, default=4444)
        parser.add_argument("-i", "--ilp", help="Interlocutor's listening port.", type=int, default=4444)
        parser.add_argument("-a", "--ia", help="Interlocutor's IP address or name.", type=str, default="localhost")
        return parser

    #def add_args(self):
    #   parser = Intercom.add_args(self)
    

if __name__ == "__main__":
    intercom = Intercom_buffer()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()
