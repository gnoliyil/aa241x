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

-- TODO: Define possible request states, and load them automatically to DB.
CREATE TABLE Request_States(
  state VARCHAR(255) PRIMARY KEY,
  description TEXT
);

CREATE TABLE Ports(
  port_id INTEGER PRIMARY KEY,
  latitude VARCHAR(255),
  longitude VARCHAR(255),
  altitude VARCHAR(255)
);

CREATE TABLE Requests(
  request_id VARCHAR(255) PRIMARY KEY,
  k_passengers INTEGER,
  time_requested TIMESTAMP,
  time_assigned TIMESTAMP,
  time_completed TIMESTAMP,
  time_expected TIMESTAMP,
  price_expected FLOAT,
  price_f_slope FLOAT,
  state VARCHAR(255) REFERENCES Request_States(state),
  from_port INTEGER REFERENCES Ports(port_id),
  to_port INTEGER REFERENCES Ports(port_id),
  CONSTRAINT k_passengers_check CHECK (k_passengers >= 0 AND k_passengers <= 4)
);

-- TODO: Consider using PostGIS for spatial data. --
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
	state VARCHAR(255),
  next_port INTEGER REFERENCES Ports(port_id),
  fulfilling VARCHAR(255) REFERENCES Requests(request_id),
  CONSTRAINT battery_check CHECK (battery_left >= 0 AND battery_left <= 100),
  CONSTRAINT k_passengers_check CHECK (k_passengers >= 0 AND k_passengers <= 4),
  FOREIGN KEY (team_id, drone_id) REFERENCES Drones(team_id, drone_id)
);

CREATE TABLE Drone_States(
  team_id VARCHAR(255),
  drone_id VARCHAR(255),
  record_id INTEGER REFERENCES Drone_States_History(record_id),
  PRIMARY KEY (team_id, drone_id),
  FOREIGN KEY (record_id) REFERENCES Drone_States_History(record_id)
);

CREATE TABLE Bids(
  bid_id SERIAL NOT NULL PRIMARY KEY,
  price FLOAT,
  time_estimated_arrival TIMESTAMP,
  accepted BOOLEAN, /* rename */
  succeeded BOOLEAN,
  team_id VARCHAR(255),
  request_id VARCHAR(255),
  CONSTRAINT price_check CHECK (price >= 0),
  FOREIGN KEY (team_id) REFERENCES Teams(team_id),
  FOREIGN KEY (request_id) REFERENCES Requests(request_id)
);
