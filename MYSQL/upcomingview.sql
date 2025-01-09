CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `upcomingmatches` AS
    SELECT 
        `matches`.`match_id` AS `match_id`,
        `teams_home`.`team_name` AS `home_team`,
        `teams_away`.`team_name` AS `away_team`,
        `matches`.`match_date` AS `match_date`
    FROM
        ((`matches`
        JOIN `teams` `teams_home` ON ((`matches`.`home_team_id` = `teams_home`.`team_id`)))
        JOIN `teams` `teams_away` ON ((`matches`.`away_team_id` = `teams_away`.`team_id`)))
    WHERE
        (`matches`.`status` = 'upcoming')
	ORDER BY 
        `matches`.`match_date` ASC;
        