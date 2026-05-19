import socket       ## For creating UDP socket
import threading    ## For running the listener in a separate thread
import time         ## Used for timestamps

class UDPListener:
    def __init__(self, ip: str, port: int, callback):
        self.ip = ip                ## IP address to listen on
        self.port = port            ## Port to listen on
        self.callback = callback    ## Function to call with received data

        self.socket = None          ## Holds UDP socket
        self.thread = None          ## Background thread for listening
        self.running = False        ## Controls the listener loop

    ########### Start Listener #############

    def start(self):
        self.running = True         ## Set running flag to True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  ## Create UDP socket
        self.socket.bind((self.ip, self.port))  ## Bind socket to IP and port
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)  ## Create background thread for listening
        self.thread.start()         ## Start the listener thread

        print(f"UDP Listener started on {self.ip}:{self.port}")  ## Log that listener has started

    ########### Main Listen Loop ############

    def _listen_loop(self):
        while self.running:
            try:
                raw_data, addr = self.socket.recvfrom(4096)  ## Receive data from socket
                timestamp = time.perf_counter()  ## Get current timestamp
                self.callback(raw_data, timestamp, addr)  ## Call the callback with received data and timestamp
            except Exception as e:
                print(f"Error in UDP listener: {e}")  ## Log any exceptions that occur

    ############ Stop Listener ##############

    def stop(self):
        self.running = False        ## Set running flag to False to stop the loop
        if self.socket:
            self.socket.close()     ## Close the UDP socket
        print("UDP Listener stopped")  ## Log that listener has stopped