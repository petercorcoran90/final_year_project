LOAD DATA INFILE '/Users/petercorcoran/python/matches_final.csv'
INTO TABLE Matches
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(match_id, home_team_id, away_team_id, match_date, stadium, home_score, away_score, status);

