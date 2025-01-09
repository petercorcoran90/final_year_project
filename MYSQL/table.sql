CREATE VIEW PremierLeagueTable AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY (wins * 3 + draws) DESC, (goals_scored - goals_conceded) DESC) AS position,
    teams.team_name,
    team_stats.matches_played,
    team_stats.wins,
    team_stats.draws,
    team_stats.losses,
    team_stats.goals_scored,
    team_stats.goals_conceded,
    (team_stats.goals_scored - team_stats.goals_conceded) AS goal_difference,
    (team_stats.wins * 3 + team_stats.draws) AS points
FROM 
    teams
JOIN 
    team_stats ON teams.team_id = team_stats.team_id
ORDER BY 
    points DESC, goal_difference DESC;