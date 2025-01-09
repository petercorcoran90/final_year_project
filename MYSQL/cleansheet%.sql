DELIMITER //

CREATE FUNCTION GetCleanSheetPercentage(team_id INT) RETURNS FLOAT
DETERMINISTIC
BEGIN
    DECLARE clean_sheet_percentage FLOAT;
    DECLARE total_matches INT;
    DECLARE clean_sheets INT;
    
    -- Ensure the WHERE clause uniquely identifies a single row
    SELECT matches_played 
    INTO total_matches 
    FROM team_stats 
    WHERE team_id = team_id
    LIMIT 1; -- Adding LIMIT 1 to ensure only one row is returned
    
    -- Count clean sheets from the matches table
    SELECT COUNT(*) 
    INTO clean_sheets 
    FROM matches 
    WHERE 
        (home_team_id = team_id AND away_score = 0) 
        OR 
        (away_team_id = team_id AND home_score = 0);
    
    -- Calculate clean sheet percentage
    SET clean_sheet_percentage = (clean_sheets / total_matches) * 100;
    RETURN clean_sheet_percentage;
END //

DELIMITER ;
