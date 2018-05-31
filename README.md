---


---

<h1 id="aa-241x-spring-2018">AA 241x: Spring 2018</h1>
<h2 id="summary">Summary</h2>
<p>Welcome to the documentation for Stanford AA 241x: Spring 2018. Here we will describe the architecture for our Automated Drone Bidding System which goal is to simulate Uber Elevate’s eVTOL service using DJI drones.</p>
<p>During a simulation, we will have 2 types of servers running: <code>MainServer (MainServer.py)</code> and <code>TeamServer (MainServer.py)</code>. There will be one 	<code>MainServer</code> running (by the class admins) and one <code>TeamServer</code> running for every team in the simulation. The <code>MainServer</code> has a two-way communication with the <code>TeamServer</code>s, while <code>TeamServer</code>s cannot communicate with each other.</p>
<p>Each team has multiple drones flying (only one physical one). <strong>The drone_id of the physical drone must be 0</strong>. Each physical drone is a DJI Spark and is controlled by a RemoteController which has an Android device plugged in to it.  The Android device runs our own version of the DJI This app receives information from a server running on the Team’s computer, which is used to control the drone.</p>
<p>In the next sections we will provide the necessary documentation for the teams to communicate with the <code>MainServer</code> through their respective <code>TeamServer</code>s and for teams to control their drones.</p>
<h2 id="mainserver---teamserver-communication">MainServer &lt;-&gt; TeamServer Communication</h2>
<p>The<code>MainServer</code> is connected with the <code>TeamServers</code> using the <code>Twisted</code> protocol. To start communication, the admins will first launch the MainServer and be open for communication. IP address and Port number will be provided to the teams. To initiate communication teams should simply run their <code>TeamServer.py</code> program, which has everything set up for communication. Make sure to run <code>TeamServer.py &lt;team_id&gt; &lt;password&gt;</code>  to be able to login. Also make sure to install all the requirements in <code>requirements.txt</code> using <code>pip install -r requirements.txt</code> and use python3.</p>
<p>Teams should make sure that they have all the logic implemented once they run their server. To send a json message to the server, call <code>self.sendToServer(&lt;json_string&gt;)</code>, which is in the <code>TeamClientSideProtocol</code> class. When teams send messages to MainServer, they must include a <code>'type'</code> field. The types will be defined below.</p>
<p><strong>Teams MUST get the <a href="http://TeamServer.py">TeamServer.py</a> and other relevant files from us to be able and complete all the TODOs listed. Please ask us questions if there is any confusion.</strong></p>
<p>The communication should follow the structure below:</p>
<h3 id="authentication">1. Authentication:</h3>
<p>Team sends message to Main to be authenticated by the system. If a team does not do this, any message they send will be ignored.</p>
<blockquote>
<p>Auth request: Team sends ‘auth’ message to login. Teams must let us know what their team_id and password is beforehand.</p>
</blockquote>
<pre><code># TeamServer -&gt; MainServer
{
 'type': 'auth',
 'team_id': (int),       # ID of team.
 'password': (string)    # Password used for login.
}
</code></pre>
<blockquote>
<p>Auth response: Server responds back with auth result.</p>
</blockquote>
<pre><code># MainServer -&gt; TeamServer
{
 'type': 'response',
 'result': (text),      # 'error' OR 'success'.
 'msg': (text)          # Describes error in case there is one. None if no error. 
}
</code></pre>
<h3 id="operation">2.  Operation</h3>
<p>Now that we have established communication between the <code>TeamServer</code>s and the <code>MainServer</code>, there are multiple things that can happen. The team can log out, send drone state information, can submit a bid, or can accept/reject a bid that is offered to them.  Lets define some of the protocols that will be going on at the same time.</p>
<h4 id="i.-bid-broadcasting">i. Bid Broadcasting</h4>
<p>The <code>MainServer</code> will first load all the requests from a csv file written by the admins. Every request has a certain timestamp, which denotes at what time the request will be broadcasted. At that time, <code>MainServer</code> will send a flight request to all <code>TeamServer</code>s, which must respond back whether they want to bid or not. If they do, they must specify estimated times for the flight and their bid price. Once a confirms/starts a task, pickups up passengers (from port <code>from_port</code>) drone finishes its task, or if something goes unexpected, the team must send a task update.</p>
<blockquote>
<p>Bid Broadcast:  <code>MainServer</code> sends a message with the following format to the teams.</p>
</blockquote>
<pre><code> # MainServer -&gt; TeamServer
{ 
  'type': 'request',
  'request': {
     'request_id': (int),       # Used to identify the request. 
     'k_passengers': (int),     # Number of passengers for request. This might affect prices. 
     'expected_price': (float), # Expected price. Teams should bid close to this price, but there is no restriction.
     'from_port': (int),        # Port for pickup. 
     'to_port': (int)           # Port for delivery.
  }
}
</code></pre>
<blockquote>
<p>Bidding: The TeamServers respond back with their bid decision. <strong>IMPORTANT NOTE</strong>: teams must write function that determines if they want to bid, calculate their ETA and the price they want to set. We will set a timeout of 5~10 seconds to let teams respond. After we receive all responses, we decide who wins the bid, and we send back the results to all teams that submitted bids. The API for those results are described in the following section. <strong>PLEASE DO NOT SUBMIT  TWO DIFFERENT BIDS WITH THE SAME DRONE IF YOU HAVE NOT YET RECEIVED THE FIRST BID RESULTS UNLESS YOU ARE CONFIDENT THAT YOU CAN FULFILL BOTH BIDS</strong></p>
</blockquote>
<pre><code># TeamServer -&gt; MainServer
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
</code></pre>
<blockquote>
<p>Task: Now that teams have submitted their bids, <code>MainServer</code> decides which team ‘wins’ the request and send that information back to the teams.</p>
</blockquote>
<pre><code># TeamServer -&gt; MainServer
{ 
  'type': 'bid_result',
  'result': (text),             # 'win' or 'lose'
  'request_id': (int), 			# Request which team must fulfill,
  'task': {                     # Task is ONLY sent to the team who wins the bid. Must be fulfilled with the drone which they specified, listed on the task.  
     'k_passengers': (int),     # The next properties are the same ones from request, and they will be left as None if result is 'lose'.
     'time_expected': (datetime), # Time we expect you to finish task. 
     'price': (float),          # Price we are paying.
     'from_port': (int),        #
     'to_port': (int),          #
	 'drone_id': (int)          #
  }
}
</code></pre>
<blockquote>
<p>Task Update: The team must send an update of the task once its done or if something happens. Send ‘confirm’ to confirm that you will perform the task that we sent. Send ‘deny’ if you will not perform the task . ‘pickup’ when you pick up a passengers. ‘success’ if you deliver the passenger, and ‘failure’ if you fail to deliver the passengers. When you send a ‘pickup’ or ‘success’ message, make sure that you have sent the state of the drone at hand very recently (before sending the message), since we will check your location and make sure that the location of the from_port/to_port is close in distance from your drones last reported location.</p>
</blockquote>
<pre><code># TeamServer -&gt; MainServer
{
  'type': 'task_update'
  'request_id': (int)
  'status': (text)         # 'confirm','deny', 'pickup', 'success' or 'failure'    
  'msg': (option)          # Describes what happened if there is a failure. None if success. 
}
</code></pre>
<h4 id="ii.-drone-states">ii. Drone states</h4>
<p>Every X seconds, <code>TeamServers</code> must send the  <code>MainServer</code> their drone state information, so we can keep track of the state of the world. The message must have the following format. The state ‘type’ must be either ‘physical’ (for physical drone) or ‘simulation’ (for simulation drone). ‘pax’ must be an int representing the number of passengers. ‘battery_left’ must be 0 &lt;= x &lt;= 100. ‘fulfilling’ must be the request_id of the request the drone is fulfilling, or None. ‘state’ must be ‘working’ or ‘not_working’.</p>
<pre><code># TeamServer -&gt; MainServer
{
  'type': 'drone_state'
  'drone_state': {
	  'drone_id': (int),         # ID of drone being updated. 
	  'longitude': (text),       # 
	  'latitude': (text),        #
	  'altitude': (text),        #
	  'velocity': (list size 3), # [vx, vy, vz] Velocity vector.
	  'k_passengers': (int),     #
	  'battery_left': (float),   # 0 &lt;= x &lt;= 100
	  'state': (text),           # 'working' or 'not_working' 
	  'fulfilling': (bool),      # True if drone is fulfilling a request. 
	  'next_port': (int),        # Port where drone is headed to if fulfilling is True. 
								 # i.e. if drone is looking for passenger, then next_port = from_port. 
								 # if drone has passengers, then next_port = to_port. None if fulfilling is false.  
  }
}
</code></pre>
<h4 id="iii.-responses">iii. Responses</h4>
<p>Every time the <code>TeamServer</code> sends a message to the <code>MainServer</code>, the <code>MainServer</code> will send a response back acknowledging the message. Note that for  	<code>'type': 'auth'</code>, this response message differs. The team can ignore this message, but make sure to be aware if they receive an error response. <strong>Make sure to be receiving the correct responses.</strong></p>
<pre><code># MainServer -&gt; TeamServer
{
 'type': 'response',
 'result': (text),      # 'error' OR 'thanks'.
 'msg': (text)          # Describes error in case there is one. None if no error. 
}
</code></pre>
<h2 id="teamserver---android-app---drone-communication">TeamServer &lt;-&gt; Android App &lt;-&gt; Drone Communication</h2>
<p>Running / Compiling:</p>
<ol>
<li>
<p>To download the app onto an Android device, you will first need to download Android Studio (from here: <a href="https://developer.android.com/studio/">https://developer.android.com/studio/</a>). Then, open Android Studio and select “Open an existing Android Studio project”, opening the ENTIRE DroneController folder.</p>
</li>
<li>
<p>Enable USB debugging on your Android device. This can be done in the settings. Plug your device into your laptop via USB and run the application from Android studio (using the green play button). Default settings should be fine, but if not, then use build tool “28.0.0 rc1” with SDK 26 to compile this app. The app should be able run on any device with SDK version ≥ 19 (i.e. ≥ Android 4.4).</p>
</li>
</ol>
<p>IMPORTANT: When you open the app for the first time, you must be connected to the internet. The app will need to download necessary tools used for connecting with the drone. Only after you see the “SDK Registration Succeeded” message may you connect to the drone’s WiFi network.</p>
<ol start="3">
<li>Now we’re ready to test the communication. We are using python3 for this code (python2 will give you weird error messages!). On your laptop, install the packages python-socketio, eventlet, and flask. You can do this with the command</li>
</ol>
<p>pip install package_name</p>
<p>where package_name is the name of the desired package.</p>
<ol start="4">
<li>
<p>Run the attached <a href="http://socketio-server.py">socketio-server.py</a> program in your terminal.</p>
</li>
<li>
<p>In your terminal, run the command</p>
</li>
</ol>
<p>ABS_PATH/platform-tools/adb reverse tcp:9001 tcp:9090</p>
<p>where ABS_PATH is the absolute path to the folder containing your SDK Tools. adb is a command line utility provided in the Android SDK tools that allows for port forwarding. You can find the correct location of the SDK folder by going to Tools --&gt; SDK Manager in Android Studio. For example, the command that I run is</p>
<p>/Users/andrewchang/Library/Android/sdk/platform-tools/adb</p>
<p>Otherwise, you can download the standalone SDK tools here: <a href="https://developer.android.com/studio/releases/platform-tools">https://developer.android.com/studio/releases/platform-tools</a></p>
<p>Make sure that the second port number is consistent with that which you used in the socketio-server program!</p>
<p>IMPORTANT: THIS MUST BE DONE EVERY TIME YOU RECONNECT YOUR DEVICE TO YOUR LAPTOP!</p>
<ol start="6">
<li>
<p>In the app, make sure “<a href="http://127.0.0.1:9001">http://127.0.0.1:9001</a>” is in the URL input box and click “connect”. You should be able to see “connect xxxxxx (a long hexadecimal id)” in the python output and see an Android Toast saying “Connect!”</p>
</li>
<li>
<p>To connect with the Spark, connect with the drone’s WiFi network and click the “Open” button in the home page of the app. In the new page, click “Get Drone State.” You will be able to see the updated drone state in your python terminal. In the Android Studio log, you will able to see the commands sent from the laptop to the Android app.</p>
</li>
<li>
<p>The implementation of the controls is left up to the individual groups. To start, look at the FlyTask in DroneControlActivity.</p>
</li>
</ol>
<p>Extra Information:</p>
<p>Network Connection:<br>
The Android app uses <a href="http://Socket.io">Socket.io</a> (somewhat like a WebSocket client/server) to send “events” with associated JSON data for communication.</p>
<p>Get Drone State:<br>
After connecting to the <a href="http://Socket.io">Socket.io</a> server and connecting with the drone, you can click “Get Drone State” to poll drone state every second (you can change the frequency yourself in DroneControlActivity.java). The drone state (in JSON Format) will be shown on the screen and will be sent to the <a href="http://Socket.io">Socket.io</a> server, after which the server may respond to the state information.</p>
<p>Control Drone:<br>
After the drone takes off and we finish all the drone configuration, we would like to set the target position (longitude, latitude and altitude) and velocity (vx, vy, vz) and then click “Fly to” to let it fly to a specific position. The current code has some basic code, which should be completed by students. [PENDING UPDATES: ADDITIONAL CODE MAY BE PROVIDED]</p>

