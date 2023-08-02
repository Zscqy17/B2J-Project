from pythonosc import dispatcher
from pythonosc import osc_server

def print_the_port(unused_addr, args):
    print("Received OSC message: {0}".format(args))

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/theport", print_the_port)

server = osc_server.ThreadingOSCUDPServer(("192.168.80.89", 20000), dispatcher)
print("Serving on {}".format(server.server_address))