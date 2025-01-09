DELIMITER //

CREATE PROCEDURE GetTopSaves(IN num_players INT)
BEGIN
    SELECT 
        players.player_name,
        SUM(player_stats.saves) AS total_saves
    FROM 
        player_stats
    JOIN 
        players ON player_stats.player_id = players.player_id
    GROUP BY 
        players.player_id, players.player_name
    ORDER BY 
        total_saves DESC
    LIMIT num_players;
END //

DELIMITER ;
