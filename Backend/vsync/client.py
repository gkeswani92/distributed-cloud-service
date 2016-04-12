import xmlrpclib
import sys
from flask import Flask

#Proxy server used for RPC communication between the flask process and Master server
proxy = 0
app = Flask(__name__)

def initializeRPC(id):
    '''
        Initializes the RPC tunnel between flask and the master server by using
        the XML proxy with address "localhost:(8000+id)"
    '''
    global proxy
    try:
        port = 9000 + int(id)
        address = "http://localhost:{0}/".format(port)
        proxy = xmlrpclib.ServerProxy(address)
        return True
    except Exception as e:
        print("Could not establish RPC tunnel to proxy")
        return False

def startFlaskServer(id):
    '''
        Initializes the RPC tunnel at "localhost:(8000+id)" and the flask server
        at "0.0.0.0:(5000+id)"
    '''
    #Connect RPC tunnel to send requests to the correct address and port
    rpc_flag = initializeRPC(id)

    if rpc_flag:
        #Flask server starts running at '0.0.0.0:(5000+id)'
        flask_host = '0.0.0.0'
        flask_port = 5000 + int(id)
        app.run(host = flask_host, port = flask_port, debug="True")
        print("Flask server starting up on {0} and {1}".format(flask_host, flask_port))
    else:
        print("Did not start flask server")

@app.route("/")
def hello():
    return "Hello ... I got called"
    #proxy.putDHT("TestKey","TestValue")
    #return str(flask_port) + "Result from DHTGet: %s" % proxy.getDHT("TestKey")
    #return proxy.welcome_page();

@app.route("/testput")
def testput():
    #print "Hello ... I got called"
    proxy.putDHT("Guarav","Tanvi")
    #return str(flask_port) + "Result from DHTGet: %s" % proxy.getDHT("TestKey")
    return "DHTPut called"
@app.route("/testget")
def testget():
    #print "Hello ... I got called"
    #proxy.putDHT("TestKey","TestValue")
    return "Result from DHTGet: %s" % proxy.getDHT("Guarav")
    #return proxy.welcome_page();


if __name__ == "__main__":
    startFlaskServer(sys.argv[1])
