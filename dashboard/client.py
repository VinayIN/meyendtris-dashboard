import zmq
import logging
import os
import argparse

logging.basicConfig(level=logging.INFO)

class Client:
    def __init__(self, host="127.0.0.1", port="18812", logger_port="18813"):
        self.host = host
        self.port = port
        self.logger_port = logger_port
        self._sub = None
        self._req = None


    def connect(self, request_reply: bool = False, pub_sub: bool = False):
        ctx = zmq.Context()
        if pub_sub:  
            sub = ctx.socket(zmq.SUB)
            sub.connect(f'tcp://{self.host}:{self.logger_port}')
            sub.subscribe("")
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
    parser.add_argument("--COMMAND", dest="COMMAND", action="store_true",
                        help="Client to communicate with server in command mode")
    parser.add_argument("--LOGGER", dest="LOGGER", action="store_true",
                        help="Client to communicate with server in logger mode")
    args = parser.parse_args()
    
    client = Client()
    client.send(ping=True)
    try:
        while True:
            client.send(command=args.COMMAND)
            if args.LOGGER: client.sub_logger()
    except KeyboardInterrupt:
        print("exiting")
