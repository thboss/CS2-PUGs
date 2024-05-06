"""
Create base tables
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        'CREATE TYPE team_method AS ENUM(\'captains\', \'autobalance\', \'random\');',
        'DROP TYPE team_method;'
    ),
    step(
        'CREATE TYPE captain_method AS ENUM(\'volunteer\', \'rank\', \'random\');',
        'DROP TYPE captain_method;'
    ),
    step(
        'CREATE TYPE map_method AS ENUM(\'veto\', \'random\');',
        'DROP TYPE map_method;'
    ),
    step(
        'CREATE TYPE game_mode AS ENUM(\'competitive\', \'wingman\');',
        'DROP TYPE game_mode;'
    ),
    step(
        'CREATE TYPE team AS ENUM(\'team1\', \'team2\', \'spec\', \'none\');',
        'DROP TYPE team;'
    ),
    step(
        (
            'CREATE TABLE guilds(\n'
            '    id BIGSERIAL PRIMARY KEY,\n'
            '    linked_role BIGINT DEFAULT NULL,\n'
            '    category BIGINT DEFAULT NULL\n,'
            '    waiting_channel BIGINT DEFAULT NULL,\n'
            '    leaderboard_channel BIGINT DEFAULT NULL,\n'
            '    results_channel BIGINT DEFAULT NULL\n'
            ');'
        ),
        'DROP TABLE guilds;'
    ),
    step(
        (
            'CREATE TABLE lobbies(\n'
            '    id SERIAL PRIMARY KEY,\n'
            '    guild BIGINT DEFAULT NULL REFERENCES guilds (id) ON DELETE CASCADE,\n'
            '    capacity SMALLINT NOT NULL DEFAULT 10,\n'
            '    team_method team_method NOT NULL DEFAULT \'captains\',\n'
            '    captain_method captain_method NOT NULL DEFAULT \'volunteer\',\n'
            '    map_method map_method NOT NULL DEFAULT \'veto\',\n'
            '    game_mode game_mode NOT NULL DEFAULT \'competitive\',\n'
            '    connect_time SMALLINT NOT NULL DEFAULT 300,\n'
            '    lobby_channel BIGINT DEFAULT NULL,\n'
            '    last_message BIGINT DEFAULT NULL\n'
            ');'
        ),
        'DROP TABLE lobbies;'
    ),
    step(
        (
            'CREATE TABLE matches(\n'
            '    id VARCHAR(64) PRIMARY KEY,\n'
            '    game_server_id VARCHAR(64) DEFAULT NULL,\n'
            '    guild BIGINT DEFAULT NULL REFERENCES guilds (id) ON DELETE CASCADE,\n'
            '    channel BIGINT DEFAULT NULL,\n'
            '    message BIGINT DEFAULT NULL,\n'
            '    category BIGINT DEFAULT NULL,\n'
            '    team1_channel BIGINT DEFAULT NULL,\n'
            '    team2_channel BIGINT DEFAULT NULL,\n'
            '    team1_name VARCHAR(32) DEFAULT NULL,\n'
            '    team2_name VARCHAR(32) DEFAULT NULL,\n'
            '    map_name VARCHAR(32) DEFAULT NULL,\n'
            '    rounds_played SMALLINT NOT NULL DEFAULT 0,\n'
            '    team1_score SMALLINT NOT NULL DEFAULT 0,\n'
            '    team2_score SMALLINT NOT NULL DEFAULT 0,\n'
            '    connect_time SMALLINT NOT NULL DEFAULT 300,\n'
            '    canceled BOOL NOT NULL DEFAULT false,\n'
            '    finished BOOL NOT NULL DEFAULT false,\n'
            '    winner team NOT NULL DEFAULT \'none\',\n'
            '    api_key VARCHAR(32) DEFAULT NULL\n'
            ');'
        ),
        'DROP TABLE matches;'
    ),
    step(
        (
            'CREATE TABLE users(\n'
            '    id BIGSERIAL UNIQUE,\n'
            '    steam_id BIGSERIAL UNIQUE\n'
            ');'
        ),
        'DROP TABLE users;'
    ),
    step(
        (
            'CREATE TABLE player_stats(\n'
            '    match_id VARCHAR(32) DEFAULT NULL REFERENCES matches (id) ON DELETE CASCADE,\n'
            '    user_id BIGINT DEFAULT NULL REFERENCES users (id) ON DELETE CASCADE,\n'
            '    steam_id BIGINT DEFAULT NULL,\n'
            '    team team NOT NULL DEFAULT \'none\',\n'
            '    kills SMALLINT DEFAULT 0,\n'
            '    deaths SMALLINT DEFAULT 0,\n'
            '    assists SMALLINT DEFAULT 0,\n'
            '    mvps SMALLINT DEFAULT 0,\n'
            '    headshots SMALLINT DEFAULT 0,\n'
            '    k2 SMALLINT DEFAULT 0,\n'
            '    k3 SMALLINT DEFAULT 0,\n'
            '    k4 SMALLINT DEFAULT 0,\n'
            '    k5 SMALLINT DEFAULT 0,\n'
            '    score SMALLINT DEFAULT 0\n'
            ');'
        ),
        'DROP TABLE player_stats;' 
    ),
    step(
        (
            'CREATE TABLE lobby_users(\n'
            '    lobby_id INTEGER REFERENCES lobbies (id) ON DELETE CASCADE,\n'
            '    user_id BIGINT REFERENCES users (id) ON DELETE CASCADE,\n'
            '    CONSTRAINT lobby_user_pkey PRIMARY KEY (lobby_id, user_id)\n'
            ');'
        ),
        'DROP TABLE lobby_users;'
    ),
    step(
        (
            'CREATE TABLE spectators(\n'
            '    guild_id BIGINT REFERENCES guilds (id) ON DELETE CASCADE,\n'
            '    user_id BIGINT REFERENCES users (id) ON DELETE CASCADE,\n'
            '    CONSTRAINT spectator_pkey PRIMARY KEY (guild_id, user_id)\n'
            ');'
        ),
        'DROP TABLE spectators;'
    )
]
