# AA 241x: Spring 2018 
## Summary

Welcome to the documentation for Stanford AA 241x: Spring 2018. Here we will describe the architecture for our Automated Drone Bidding System which goal is to simulate Uber Elevate's eVTOL service using DJI drones.

During a simulation, we will have 2 types of servers running: MainServer and TeamServer. There will be one MainServer running (by the class admins) and one TeamServer running for every team in the simulation. The MainServer can communicate will all the TeamServers, while TeamServers cannot communicate with each other. 

Each team has multiple drones flying (only one physical one). Each physical drone is a DJI Spark and is controlled by a Remote Controller.  An Android device running our version of a DJI app is connected to the RC. This app receives information from a server running on the Team's computer, which is used to control the drone.

In the next sections we will provide the necessary documentation for the teams to communicate with the MainServer  through their respective TeamServers and for teams to control their drones.

## MainServer <-> TeamServer Communication

The MainServer is connected with the TeamServers using the Twisted protocol. To start communication, the admins will first launch the MainServer and be open for communication. IP address and Port number will be provided to the teams. To initiate communication teams should simply run their **TeamServer** program, which has everything set up for communication. Make sure to install all the requirements in **requirements.txt** and use python3. 

Teams should make sure that they have all the logic implemented once they run their server. To send a json message to the server, call `self.sendToServer(<json_string>)`, which is in the `TeamClientSideProtocol` class. When teams send messages to MainServer, they must include a `type` field. They types will be defined below. 

The communication should follow the structure below:

1. Authentication: Team sends message to Main to be authenticated by the system. If a team does not do this, any message they send will be ignored. 

> Team to Main: 
> `{'type': 'auth','team-id': team_id,'password': password}`
>  *Note: The team_id and password should be established beforehand.*


> Main to Team: 
> `{'type': 'response',result: 'success' or 'error','msg': msg}`
> *Note: msg is optional. In this case its sent on error, and it describes the reason for the error.* 

2.  Now that we have established communication between the TeamServers and the MainServer, there are multiple things that can happen. The team can log out, send drone state information, can submit a bid, or can accept/reject a bid that is offered to them.  


## TeamServer <-> Android App <-> Drone Communication

