-- Create Teams table
CREATE TABLE Teams (
    team_id INT AUTO_INCREMENT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    stadium VARCHAR(100),
    founded_year INT,
    manager VARCHAR(100)
);

-- Create Players table
CREATE TABLE Players (
    player_id INT AUTO_INCREMENT PRIMARY KEY,
    team_id INT,
    player_name VARCHAR(100) NOT NULL,
    position VARCHAR(50),
    nationality VARCHAR(50),
    date_of_birth DATE,
    height DECIMAL(5,2),
    weight DECIMAL(5,2),
    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
);

-- Create Matches table
CREATE TABLE Matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    home_team_id INT,
    away_team_id INT,
    match_date DATE,
    stadium VARCHAR(100),
    home_score INT,
    away_score INT,
    status ENUM('Completed', 'Upcoming', 'Ongoing') NOT NULL,
    FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES Teams(team_id)
);

-- Create Player_Stats table
CREATE TABLE Player_Stats (
    stat_id INT AUTO_INCREMENT PRIMARY KEY,
    player_id INT,
    match_id INT,
    goals INT,
    assists INT,
    yellow_cards INT,
    red_cards INT,
    minutes_played INT,
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    FOREIGN KEY (match_id) REFERENCES Matches(match_id)
);

-- Create Team_Stats table
CREATE TABLE Team_Stats (
    team_stat_id INT AUTO_INCREMENT PRIMARY KEY,
    team_id INT,
    season VARCHAR(20),
    matches_played INT,
    wins INT,
    draws INT,
    losses INT,
    goals_scored INT,
    goals_conceded INT,
    points INT,
    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
);

ALTER TABLE Players
CHANGE COLUMN weight market_value BIGINT;
