DELIMITER //

CREATE TRIGGER after_match_update
AFTER UPDATE ON matches
FOR EACH ROW
BEGIN
    IF NEW.status = 'Completed' THEN
        -- Update home team stats
        UPDATE team_stats
        SET 
            matches_played = matches_played + 1,
            goals_scored = goals_scored + NEW.home_score,
            goals_conceded = goals_conceded + NEW.away_score,
            wins = wins + IF(NEW.home_score > NEW.away_score, 1, 0),
            draws = draws + IF(NEW.home_score = NEW.away_score, 1, 0),
            losses = losses + IF(NEW.home_score < NEW.away_score, 1, 0),
            points = points + 
                     (3 * IF(NEW.home_score > NEW.away_score, 1, 0)) + -- 3 points for a win
                     (1 * IF(NEW.home_score = NEW.away_score, 1, 0))    -- 1 point for a draw
        WHERE team_id = NEW.home_team_id;

        -- Update away team stats
        UPDATE team_stats
        SET 
            matches_played = matches_played + 1,
            goals_scored = goals_scored + NEW.away_score,
            goals_conceded = goals_conceded + NEW.home_score,
            wins = wins + IF(NEW.away_score > NEW.home_score, 1, 0),
            draws = draws + IF(NEW.away_score = NEW.home_score, 1, 0),
            losses = losses + IF(NEW.away_score < NEW.home_score, 1, 0),
            points = points + 
                     (3 * IF(NEW.away_score > NEW.home_score, 1, 0)) + -- 3 points for a win
                     (1 * IF(NEW.away_score = NEW.home_score, 1, 0))    -- 1 point for a draw
        WHERE team_id = NEW.away_team_id;
    END IF;
END //

DELIMITER ;