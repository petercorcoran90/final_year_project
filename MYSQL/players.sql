LOAD DATA INFILE '/Users/petercorcoran/python/players_cleaned.csv'  -- Replace with the actual path to your file
INTO TABLE Players
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(player_id, team_id, player_name, position, nationality, date_of_birth, height, market_value);
