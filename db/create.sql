DROP TABLE IF EXISTS Bids CASCADE;
DROP TABLE IF EXISTS Drone_States_History CASCADE;
DROP TABLE IF EXISTS Drone_States CASCADE;
DROP TABLE IF EXISTS Ports CASCADE;
DROP TABLE IF EXISTS Requests CASCADE;
DROP TABLE IF EXISTS Request_States CASCADE;
DROP TABLE IF EXISTS Fly_States CASCADE;
DROP TABLE IF EXISTS Drones CASCADE;
DROP TABLE IF EXISTS Students CASCADE;
DROP TABLE IF EXISTS Teams CASCADE;


CREATE TABLE Teams(
	team_id VARCHAR(255) PRIMARY KEY,
	is_logged_in BOOLEAN,
	password VARCHAR(255)
);


CREATE TABLE Students(
	stanford_id VARCHAR(255) PRIMARY KEY,
	name VARCHAR(255),
	team_id VARCHAR(255) REFERENCES Teams(team_id)
);

CREATE TABLE Drones(
  team_id VARCHAR(255) REFERENCES Teams(team_id),
  drone_id INTEGER,
  is_physical BOOLEAN,
  PRIMARY KEY (team_id, drone_id)
);

-- TODO: Define possible fly states and load them automatically to DB.
CREATE TABLE Fly_States(
  state VARCHAR(255) PRIMARY KEY,
  description TEXT
);

-- Options: WAITING, NOT_SENT, SENT, NOT_ACCEPTED, ACCEPTED, ALL_ACCEPTED, ASSIGNED, DONE, FAILED
CREATE TABLE Request_States(
  state VARCHAR(255) PRIMARY KEY,
  description TEXT
);

CREATE TABLE Ports(
  port_id INTEGER PRIMARY KEY,
	longitude VARCHAR(255),
  latitude VARCHAR(255),
  altitude VARCHAR(255)
);

CREATE TABLE Requests(
  request_id SERIAL NOT NULL PRIMARY KEY,
	sent_to INTEGER,  -- number of teams the request was sent to.
  k_passengers INTEGER,      -- Number of passengers
  time_requested TIMESTAMP,  -- time at which we send the reqeust (listed in the csv file)
  time_assigned TIMESTAMP,   -- time we sent the task to the team.
  time_completed TIMESTAMP,  -- time team completes the task, if state is 'DONE'
  time_expected TIMESTAMP,   -- time we expect bid to finish at.
  expected_price FLOAT,      -- Average price for bid of this type.
  price_f_slope FLOAT,
  state VARCHAR(255) REFERENCES Request_States(state), -- See options in Request_States
  from_port INTEGER REFERENCES Ports(port_id),  -- Pickup Port
  to_port INTEGER REFERENCES Ports(port_id),    -- Delivery Port
  CONSTRAINT k_passengers_check CHECK (k_passengers >= 0 AND k_passengers <= 4)
);


CREATE TABLE Drone_States_History(
  record_id SERIAL NOT NULL PRIMARY KEY,
  team_id VARCHAR(255),
	drone_id INTEGER,
	time_stamp TIMESTAMP,
	longitude VARCHAR(255),
	latitude VARCHAR(255),
  altitude VARCHAR(255),
	velocity VARCHAR(255),  -- string representing list i.e. "[1.3,2,3]"
	k_passengers INTEGER,
  battery_left FLOAT,
	state VARCHAR(255), -- TODO: REFERENCES Fly_States
  next_port INTEGER REFERENCES Ports(port_id),
  fulfilling INTEGER REFERENCES Requests(request_id),
  CONSTRAINT battery_check CHECK (battery_left >= 0 AND battery_left <= 100),
  CONSTRAINT k_passengers_check CHECK (k_passengers >= 0 AND k_passengers <= 4),
  FOREIGN KEY (team_id, drone_id) REFERENCES Drones(team_id, drone_id)
);

CREATE TABLE Drone_States(
  team_id VARCHAR(255),
  drone_id VARCHAR(255),
  record_id INTEGER REFERENCES Drone_States_History(record_id),
  PRIMARY KEY (team_id, drone_id)
);

CREATE TABLE Bids(
  bid_id SERIAL NOT NULL PRIMARY KEY,
  price FLOAT,
  seconds_expected INTEGER,
	drone_id INTEGER,
  accepted BOOLEAN, -- True if team accepted the bid.
  won BOOLEAN, -- True if team won the bid
  team_id VARCHAR(255),
  request_id INTEGER REFERENCES Requests(request_id),
  CONSTRAINT price_check CHECK (price >= 0),
	FOREIGN KEY (team_id, drone_id) REFERENCES Drones(team_id, drone_id)
);
