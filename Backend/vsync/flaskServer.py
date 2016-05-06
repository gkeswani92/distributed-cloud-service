import xmlrpclib
import sys
import json
import uuid

from flask import Flask,request
from werkzeug.contrib.cache import SimpleCache

#Proxy server used for RPC communication between the flask process and Master server
proxy = 0
flask_port = 0

#Initializing the flask application and its local cache
app = Flask(__name__)
cache = SimpleCache()

#Time a key value pair will be stored in the local cache
timeout = 2 * 60

# setup some global variables and stub data
userDBSR = {'testUserSR': 'testPassword'}
userDBSP = {'testUserSP': 'testPassword'}
serviceID = 1;
serviceData = []
serviceData.append({'id':'1', 'name':'Bob the Gardner', 'type':'Gardening', 'location':'test location', 'radius':'25', 'cost':'60', 'description':'My name is Bob', 'rating': "-1", 'availability':'yes'})
serviceData.append({'id':'2', 'name':'Bob the Plumber', 'type':'Plumbing', 'location':'test location', 'radius':'25', 'cost':'65', 'description':'My name is Bob', 'rating': "4", 'availability':'yes'})
serviceID += 1
serviceID += 1

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
    global flask_port
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
def index():
    return "Currently connected to flask port: {0}".format(str(flask_port))

@app.route("/postService", methods=['POST'])
def postService():
    '''
        Accept post service request and stores it in cache and in the DHT
    '''
    #Retrieving the details of the service posted
    name = request.form.get('name')
    service_type = request.form.get('type')
    location = request.form.get('location')
    cost = request.form.get('cost')
    description = request.form.get('description')

    #Every posted service will have a unique UUID as its service id
    serviceID = str(uuid.uuid1())

    if name and service_type and location and cost and description:
        serviceObj = {  "id"            : serviceID,
                        "name"          : name,
                        "type"          : service_type,
                        "location"      : location,
                        "cost"          : cost,
                        "description"   : description,
                        "availability"  : 0 }

        try:
            #Storing the service id under its service_type for first lookup
            message1 = proxy.putService(service_type, serviceID)

            #Storing the complete service details keyed by the service id
            message2 = proxy.putService(serviceID, json.dumps(serviceObj))

            reply = { "status"    : 0,
                      "message"   : "Success. {0} . {1}".format(message1, message2),
                      "serviceID" : serviceID }

        except Exception as e:
            reply = { "status"    : 1,
                      "message"   : "Failure",
                      "error"     : str(e) }

    else:
        reply = { "status"    : 1,
                  "message"   : "Did not receive all parameters" }

    return json.dumps(reply, indent=4, separators=(',', ': '))

@app.route("/getService",methods=['GET'])
def getServiceProvider():
    '''
        Gets the service, if any, of the requested type and at the request location
    '''
    #Retrieving the details of the service posted
    location = request.args.get('location')
    service_type = request.args.get('serviceType')

    #Getting the service providers for the requested service type
    provider = proxy.getServiceProvider(service_type, location)

    if provider is not None:
        provider = json.loads(provider)
        if provider.get("status") == 0:
            reply = { "status" : 0,
                      "data"   : provider,
                      "error"  : ""}
        else:
            reply = { "status" : 1,
                      "data"   : provider,
                      "error"  : "No service provider found" }

    else:
        reply = { "status" : 1,
                "error"  : "No data retrieved from VSync" }

    return json.dumps(reply, indent=4, separators=(',', ': '))

# authenticate users - stub created by Andy
@app.route("/authenticate",methods=['GET','POST'])
def authUsers():
    if request.method == 'GET':
        username = request.args.get('username')
        password = request.args.get('password')
        userType = request.args.get('userType')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        userType = request.form.get('userType')

    if userType == 'sr':
        if username not in userDBSR:
            return json.dumps({'status': 1, 'message':'User Not Exist'})
        elif userDBSR[username] == password:
            return json.dumps({'status': 0, 'message':'Login Success'})
        else:
            return json.dumps({'status': 1, 'message':'Login Invalid'})

    if userType == 'sp':
        if username not in userDBSP:
            return json.dumps({'status': 1, 'message':'User Not Exist'})
        elif userDBSP[username] == password:
            return json.dumps({'status': 0, 'message':'Login Success'})
        else:
            return json.dumps({'status': 1, 'message':'Login Invalid'})

# remove service from availability list when it is declared off on device - stub created by Andy
@app.route("/deleteService",methods=['POST'])
def deleteService():
    id = request.form.get('serviceID')
    # insert logic here to delete the service object
    reply = {}
    reply["status"] = 0
    reply["message"] = "success"
    return json.dumps(reply)

# /users
# GET: return a list of all users
# POST: required parameters include firstname, lastname, and email. Return user_id
@app.route("/users",methods=['GET','POST'])
def users():
    if request.method == 'GET':
        return "Return a list of users"
    elif request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        return "user_id"
    else:
        return "invalid input"

# /users/<id>
# GET: return information about the user
# POST: update info of the user
@app.route("/users/<uid>",methods=['GET','POST'])
def user(uid):
    if request.method == 'GET':
        return json.dumps({'firstname': 'first',
                'lastname':'last',
                'email':'email'})
    elif request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        return json.dumps({'status':0,
                'firstname':firstname,
                'lastname':lastname,
                'email':email})
    else:
        return "invalid input"

# /users/<id>/services
# GET: return all services by this user
# POST: required parameters: service_name, create a new service for this user
@app.route("/users/<uid>/services",methods=['GET','POST'])
def services(uid):
    if request.method == 'GET':
        return json.dumps({'service_id':0,
                'service_name':'service',
                'service_status':'status',
                'service_starttime':'starttime',
                'service_endtime':'endtime'})
    elif request.method == 'POST':
        service_name = request.form.get('service_name')
        return json.dumps({'status':0,
                'service_name':service_name})
    else:
        return "invalid input"

# /users/<uid>/services/<sid>
# GET: return this particular service by this user
# POST: required parameters: service_name, edit the service for this user
@app.route("/users/<uid>/services/<sid>",methods=['GET','POST'])
def service(uid,sid):
    if request.method == 'GET':
        return json.dumps({'service_id':0,
                'service_name':'service',
                'service_status':'status',
                'service_starttime':'starttime',
                'service_endtime':'endtime'})
    elif request.method == 'POST':
        return json.dumps({'service_id':0,
                'service_name':'service',
                'service_status':'status',
                'service_starttime':'starttime',
                'service_endtime':'endtime'})
    else:
        return "invalid input"

@app.route("/balancing_get",methods=['GET'])
def balancing_get():
    location = request.args.get('location')
    return "Currently connected to flask port: {0} Location: {1}".format(str(flask_port), location)

@app.route("/balancing_post",methods=['POST'])
def balancing_post():
    location = request.form.get('location')
    return "Currently connected to flask port: {0} Location: {1}".format(str(flask_port), location)

@app.route("/testcache",methods=['POST'])
def testCache():
    '''
        Receives a key value pair via a POST request and stores the pair into the
        DHT and the local cache
    '''
    global timeout
    if request.method == 'POST':
        key = request.args.get('key')
        value = request.args.get('value')
        cache.set(key, value, timeout=timeout)
        cached_entry = cache.get(key)
        return "Cached entry: {0}".format(cached_entry)

@app.route("/testput",methods=['POST'])
def testput():
    '''
        Receives a key value pair via a POST request and stores the pair into the
        DHT and the local cache
    '''
    global timeout
    if request.method == 'POST':
        key = request.args.get('key')
        value = request.args.get('value')

        if key is not None and value is not None:
            #Storing the key value pair in the DHT
            proxy.putDHT(key,value)

            #Storing the key value pair in the cache for 5 mins
            cache.set(key, value, timeout=timeout)

            return json.dumps({'status':0,'message':'Flask port %s: Key %s and Value %s have been stored in the DHT and cache' %(flask_port,key,value)})
        else:
            return "Key: {0} Value: {1} Invalid paramaters".format(key, value)


@app.route("/testget",methods=['GET'])
def testget():
    '''
        Reads the key from the call and first checks it the corresponding value is in
        the cache. If found, it returns the value. If not, it uses RPC to call its
        master server with a DHT_GET call
    '''
    display_message = None

    #IF a key was passed in through the URL, we try to look it up in the cache or DHT
    if request.method == 'GET':
        key = request.args.get('key')
        if key is not None:
            cached_entry = cache.get(key)

            #If the key value pair was in the cache, return it
            #Else, look in the DHT
            if cached_entry is not None:
                display_message = "Result from Cache: {0} on flask port {1}".format(cached_entry, flask_port)
            else:
                dht_entry = proxy.getDHT(key)
                if dht_entry is not None:
                    display_message = "Result from DHTGet: {0} on flask port {1}".format(dht_entry, flask_port)
                else:
                    display_message = "Result could not be found in the cache or the DHT on flask port {0}".format(flask_port)
        else:
            display_message = "No key was passed to the testGet method"

    return display_message

######################GCM + Other Stub Functions######################
from gcm import GCM
gcm = GCM("AIzaSyAY0H3hUW5jHoUZQgqyNrQvScRqrNOmqhk")
counter = 0 # this counter is only used to generate different messages everytime
device_token = {}

@app.route("/registerAndroidDeviceForGCMPush",methods=['POST'])
def registerAndroidDeviceForGCMPush():
    global device_token
    user_email = request.form.get("username")
    user_type = request.form.get("userType")
    new_token = request.form.get("new_push_device_token")
    
    if user_email not in device_token:
	    device_token[user_email] = new_token
    elif user_email in device_token and device_token[user_email] != new_token:
        device_token[user_email] = new_token

    data = {}
    data["status"] = "0"
    print device_token
    return json.dumps(data)

@app.route("/sendTestPush",methods=['GET','POST'])
def sendTestPush():
    global device_token
    global counter
    if (counter % 5) == 0:
        data = {'messageTitle': 'Test PUSH Message', 'data': 'This is a test PUSH message'}
    elif (counter % 5) == 1:
        data = {'messageTitle': 'Test PUSH Message', 'data': 'Hello World!'}
    elif (counter % 5) == 2:
        data = {'messageTitle': 'Test PUSH Message', 'data': 'How are you doing today?'}
    elif (counter % 5) == 3:
        data = {'messageTitle': 'Test PUSH Message', 'data': 'Welcome to Handy!'}
    elif (counter % 5) == 4:
        data = {'messageTitle': 'Test PUSH Message', 'data': 'Someone has requested your service!'}
	
    print device_token.values()

    # JSON request
    response = gcm.json_request(registration_ids=device_token.values(), data=data)

    counter = counter+1
    data = {}
    data["status"] = "0"
    return json.dumps(data)

@app.route("/createUser",methods=['POST'])
def createUser():
    username = request.form.get("username")
    password = request.form.get("password")
    user_type = request.form.get("userType")
    if user_type == 'sp':
        userDBSP[username] = password
    if user_type == 'sr':
        userDBSR[username] = password
    reply = {}
    reply["status"] = 0
    reply["message"] = "success"
    return json.dumps(reply)

@app.route("/updateService",methods=['POST'])
def updateService():
    id = request.form.get('serviceID')
    name = request.form.get('name')
    type = request.form.get('type')
    location = request.form.get('location')
    cost = request.form.get('cost')
    description = request.form.get('description')
    # insert logic here to delete the service object
    reply = {}
    reply["status"] = 0
    reply["message"] = "Success"
    return json.dumps(reply)

@app.route("/changeServiceAvailability",methods=['POST'])
def changeServiceAvailability():
    id = request.form.get('serviceID')
    # insert logic here to delete the service object
    reply = {}
    reply["status"] = 0
    reply["message"] = "Success"
    return json.dumps(reply)

#########################################################

if __name__ == "__main__":
    startFlaskServer(sys.argv[1])
