DROP TABLE IF EXISTS Bids;
DROP TABLE IF EXISTS Drone_States;
DROP TABLE IF EXISTS Ports;
DROP TABLE IF EXISTS Requests;
DROP TABLE IF EXISTS Request_States;
DROP TABLE IF EXISTS Fly_States;
DROP TABLE IF EXISTS Drones;
DROP TABLE IF EXISTS Students;
DROP TABLE IF EXISTS Teams;


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

-- INSERT INTO Team_Login VALUES(1, 't1', 'FALSE'); --

CREATE TABLE Drones(
  team_id VARCHAR(255) REFERENCES Teams(team_id),
  drone_id VARCHAR(255),
  is_physical BOOLEAN,
  PRIMARY KEY (team_id, drone_id)
);

CREATE TABLE Fly_States(
  state VARCHAR(255) PRIMARY KEY,
  description TEXT
);

CREATE TABLE Request_States(
  state VARCHAR(255) PRIMARY KEY,
  description TEXT
);

CREATE TABLE Requests(
  request_id VARCHAR(255) PRIMARY KEY,
  time_requested TEXT,
  time_assigned TEXT,
  time_completed TEXT,
  price_f_slope FLOAT,
  state VARCHAR(255) REFERENCES Request_States(state)
);

CREATE TABLE Ports(
  port_id VARCHAR(255) PRIMARY KEY,
  latitude VARCHAR(255),
  longitude VARCHAR(255),
  altitude VARCHAR(255)
);

-- TODO: Consider using PostGIS for spatial data. --
CREATE TABLE Drone_States(
  team_id VARCHAR(255),
  drone_id VARCHAR(255),
  time_stamp TEXT,
  battery_left FLOAT,
  k_passengers INTEGER,
  latitude VARCHAR(255),
  longitude VARCHAR(255),
  altitude VARCHAR(255),
  velocity FLOAT,
  from_port VARCHAR(255) REFERENCES Ports(port_id),
  to_port VARCHAR(255) REFERENCES Ports(port_id),
  fulfilling VARCHAR(255) REFERENCES Requests(request_id),
  CONSTRAINT battery_check CHECK (battery_left >= 0 AND battery_left <= 100),
  CONSTRAINT k_passengers_check CHECK (k_passengers >= 0 AND k_passengers <= 4),
  FOREIGN KEY (team_id, drone_id) REFERENCES Drones(team_id, drone_id)
);

CREATE TABLE Bids(
  bid_id VARCHAR(255),
  price FLOAT,
  succeeded BOOLEAN
  CONSTRAINT price_check CHECK (price >= 0)
);
