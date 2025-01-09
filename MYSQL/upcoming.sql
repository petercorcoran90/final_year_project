CREATE VIEW UpcomingMatches AS
SELECT 
    matches.match_id,
    teams_home.team_name AS home_team,
    teams_away.team_name AS away_team,
    matches.match_date,
    matches.status,
    matches.home_score,
    matches.away_score
FROM 
    matches
JOIN 
    teams AS teams_home ON matches.home_team_id = teams_home.team_id
JOIN 
    teams AS teams_away ON matches.away_team_id = teams_away.team_id
WHERE 
    matches.status = 'upcoming';
