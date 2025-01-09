DELIMITER //

CREATE PROCEDURE GetTopAssists(IN num_players INT)
BEGIN
    SELECT 
        players.player_name,
        SUM(player_stats.goalAssist) AS total_assists
    FROM 
        player_stats
    JOIN 
        players ON player_stats.player_id = players.player_id
    GROUP BY 
        players.player_id, players.player_name
    ORDER BY 
        total_assists DESC
    LIMIT num_players;
END //

DELIMITER ;
