import zmq
import logging
import os
import argparse

logging.basicConfig(level=logging.DEBUG)

class Client:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = "18812"
        self.log = True
        self._sub = None
        self._req = None

    def connect(self, request_reply: bool = False, pub_sub: bool = False):
        ctx = zmq.Context()
        if pub_sub:  
            sub = ctx.socket(zmq.SUB)
            sub.setsockopt(zmq.LINGER, 0)
            sub.connect(f'tcp://{self.host}:{self.port}')
            return sub
        if request_reply:
            req = ctx.socket(zmq.REQ)
            req.setsockopt(zmq.LINGER, 0)
            req.connect(f'tcp://{self.host}:{self.port}')
            return req
        raise ValueError("Need a parameter to either connect to request_reply or pub_sub")
    

    def receive(self):
        self._req = self._req if isinstance(self._req, zmq.Socket) else self.connect(request_reply=True)
        message = self._req.recv_string()
        print("------")
        print(message)
        if "command_mode" in message :
            self.send(command=True)

    def send(self, ping=False, command=False, default_message="Whisper from client..."):
        self._req = self._req if isinstance(self._req, zmq.Socket) else self.connect(request_reply=True)         
        if ping:
            self._req.send_string(f"Connected with {os.getlogin()}")
            self.receive()
            return
        if command:
            print("|\n"*4)
            print(">> Enter a command to send to server")
            cmd = input(">> ")
            self._req.send_string(cmd)
            self.receive()
            return
        self._req.send_string(default_message)
        self.receive()
        

    def sub_logger(self):
        self._sub = self._sub if self._sub else self.connect(pub_sub=True)
        self._sub.setsockopt(zmq.SUBSCRIBE, b"")
        level_name, message = self._sub.recv_multipart()
        level_name = level_name.decode('ascii').lower()
        message = message.decode('ascii')
        if message.endswith('\n'):
            # trim trailing newline, which will get appended again
            message = message[:-1]
        log = getattr(logging, level_name)
        log(message)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--MODE", dest="MODE", choices=["logger", "command"],
                        help="Client to communicate with server in either command/logger mode")
    args = parser.parse_args()
    client = Client()
    client.send(ping=True)
    try:
        while True:
            if not args.MODE:
                # WhisperMode
                client.send()
            if args.MODE == "command":
                # CommandMode
                client.send(command=True)
            if args.MODE == "logger":
                # LoggerMode
                client.sub_logger()
    except KeyboardInterrupt:
        print("exiting")
