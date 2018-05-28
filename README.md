# AA 241x: Spring 2018
## Summary

Welcome to the documentation for Stanford AA 241x: Spring 2018. Here we will describe the architecture for our Automated Drone Bidding System which goal is to simulate Uber Elevate's eVTOL service using DJI drones.

During a simulation, we will have 2 types of servers running: `MainServer (MainServer.py)` and `TeamServer (MainServer.py)`. There will be one 	`MainServer` running (by the class admins) and one `TeamServer` running for every team in the simulation. The `MainServer` has a two-way communication with the `TeamServer`s, while `TeamServer`s cannot communicate with each other.

Each team has multiple drones flying (only one physical one). **The drone_id of the physical drone must be 0**. Each physical drone is a DJI Spark and is controlled by a RemoteController which has an Android device plugged in to it.  The Android device runs our own version of the DJI This app receives information from a server running on the Team's computer, which is used to control the drone.

In the next sections we will provide the necessary documentation for the teams to communicate with the `MainServer` through their respective `TeamServer`s and for teams to control their drones.

## MainServer <-> TeamServer Communication

The` MainServer` is connected with the `TeamServers` using the `Twisted` protocol. To start communication, the admins will first launch the MainServer and be open for communication. IP address and Port number will be provided to the teams. To initiate communication teams should simply run their `TeamServer.py` program, which has everything set up for communication. Make sure to run `TeamServer.py <team_id> <password>`  to be able to login. Also make sure to install all the requirements in `requirements.txt` using `pip install -r requirements.txt` and use python3.

Teams should make sure that they have all the logic implemented once they run their server. To send a json message to the server, call `self.sendToServer(<json_string>)`, which is in the `TeamClientSideProtocol` class. When teams send messages to MainServer, they must include a `'type'` field. The types will be defined below.

The files that teams MUST finish are described below. Simply search and complete  all the TODOs:

''''''''''
# FILL THIS UP!!!!!
'''''''''''

The communication should follow the structure below:

###  1. Authentication:
Team sends message to Main to be authenticated by the system. If a team does not do this, any message they send will be ignored.

> Auth request: Team sends 'auth' message to login. Teams must let us know what their team_id and password is beforehand.
 ```
 # TeamServer -> MainServer
{
  'type': 'auth',
  'team_id': (int),       # ID of team.
  'password': (string)    # Password used for login.
 }
 ````

> Auth response: Server responds back with auth result.
 ```
 # MainServer -> TeamServer
 {
  'type': 'response',
  'result': (text),      # 'error' OR 'success'.
  'msg': (text)          # Describes error in case there is one. None if no error.
 }
 ```

### 2.  Operation
Now that we have established communication between the `TeamServer`s and the `MainServer`, there are multiple things that can happen. The team can log out, send drone state information, can submit a bid, or can accept/reject a bid that is offered to them.  Lets define some of the protocols that will be going on at the same time.

#### i. Bid Broadcasting

The `MainServer` will first load all the requests from a csv file written by the admins. Every request has a certain timestamp, which denotes at what time the request will be broadcasted. At that time, `MainServer` will send a flight request to all `TeamServer`s, which must respond back whether they want to bid or not. If they do, they must specify estimated times for the flight and their bid price. Once a confirms/starts a task, pickups up passengers (from port `from_port`) drone finishes its task, or if something goes unexpected, the team must send a task update.

>  Bid Broadcast:  `MainServer` sends a message with the following format to the teams.
```
 # MainServer -> TeamServer
{
  'type': 'request',
  'request': {
     'request_id': (int),       # Used to identify the request.
     'k_passengers': (int),     # Number of passengers for request. This might affect prices.
     'time_expected':  (int),   # How much time the trip should take, in seconds, on average.
     'price_expected': (float), # Price expected. Teams should bid close to this price, but there is no restriction.
     'from_port': (int),        # Port for pickup.
     'to_port': (int)           # Port for delivery.
  }
}
 ```

> Bidding: The TeamServers respond back with their bid decision. **IMPORTANT NOTE**: teams must write function that determines if they want to bid, calculate their ETA and the price they want to set. We will set a timeout of 5~10 seconds to let teams respond. After we receive all responses, we decide who wins the bid, and we send back the results to all teams that submitted bids. The API for those results are described in the following section.
```
# TeamServer -> MainServer
{ 'type': 'bid',
  'bid': {
     'request_id': (int),      # Request that team wants to fulfill.
	 'accepted': (bool) .      # True if submitting bid. Next attributes must be filled if True, leave None if False.
     'drone_id': (int),        # Drone that will fulfill the request.
	 'seconds_expected': (int),# Number of seconds that team expect trip to take. Time starts when the team confirms the task.
						       # Teams will be penalized if they do not fulfill the request on time. Helps determine if team will
						       # win the bid.
     'price': (float)          # bid price. This helps determine if teams will win the bid.
  }
}
```

> Task: Now that teams have submitted their bids, `MainServer` decides which team 'wins' the request and send that information back to the teams.  

```
# TeamServer -> MainServer
{
  'type': 'bid_result',
  'result': (text),             # 'win' or 'lose'
  'task': {                     # Task is ONLY sent to the team who wins the bid.
     'request_id': (int),       # Request which team must fulfill, with the drone which they specified.
     'k_passengers': (int),     # The next properties are the same ones from request.
     'time_expected': (datetime), # Time we expect you to finish task.
     'price': (float),          # Price we are paying.
     'from_port': (int),        #
     'to_port': (int),          #
  }
}
```

> Task Update: The team must send an update of the task once its done or if something happens.
```
# TeamServer -> MainServer
{
  'type': 'task_update'
  'status': (text)         # 'pickup', 'success' or 'failure'    
  'msg': (option)          # Describes what happened if there is a failure. None if success.
}
```

#### ii. Drone states

Every X seconds, `TeamServers` must send the  `MainServer` their drone state information, so we can keep track of the state of the world. The message must have the following format. The state 'type' must be either 'physical' (for physical drone) or 'simulation' (for simulation drone). 'pax' must be an int representing the number of passengers. 'battery_left' must be 0 <= x <= 100. 'fulfilling' must be the request_id of the request the drone is fulfilling, or None. 'state' must be 'working' or 'not_working'.

```
# TeamServer -> MainServer
{
  'type': 'drone_state'
  'drone_state': {
	  'drone_id': (int),         # ID of drone being updated.
	  'longitude': (text),       #
	  'latitude': (text),        #
	  'altitude': (text),        #
	  'velocity': (list size 3), # [vx, vy, vz] Velocity vector.
	  'k_passengers': (int),     #
	  'battery_left': (float),   # 0 <= x <= 100
	  'state': (text),           # 'working' or 'not_working'
	  'fulfilling': (bool),      # True if drone is fulfilling a request.
	  'next_port': (int),        # Port where drone is headed to if fulfilling is True.
								 # i.e. if drone is looking for passenger, then next_port = from_port.
								 # if drone has passengers, then next_port = to_port. None if fulfilling is false.  
  }
}
```

#### iii. Responses

Every time the `TeamServer` sends a message to the `MainServer`, the `MainServer` will send a response back acknowledging the message. Note that for  	`'type': 'auth'`, this response message differs. The team can ignore this message, but make sure to be aware if they receive an error response. **Make sure to be receiving the correct responses.**
 ```
 # MainServer -> TeamServer
 {
  'type': 'response',
  'result': (text),      # 'error' OR 'thanks'.
  'msg': (text)          # Describes error in case there is one. None if no error.
 }
 ```

## TeamServer <-> Android App <-> Drone Communication
