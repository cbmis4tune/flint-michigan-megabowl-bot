import sqlite3
from pathlib import Path


# =============================================================
# DATABASE CONFIG
# =============================================================

DATABASE_PATH = Path(
    "megabowl.db"
)


# =============================================================
# CONNECTION
# =============================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


# =============================================================
# INITIALIZE DATABASE
# =============================================================

def initialize_database():
    with get_connection() as connection:

        # -----------------------------------------------------
        # DRAFT STATE
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draft_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),

                active INTEGER NOT NULL DEFAULT 0,

                current_pick INTEGER NOT NULL DEFAULT 1,

                total_teams INTEGER,

                total_rounds INTEGER,

                draftboard_channel_id INTEGER,

                draftboard_message_id INTEGER
            )
            """
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO draft_state (
                id,
                active,
                current_pick
            )
            VALUES (
                1,
                0,
                1
            )
            """
        )

        # -----------------------------------------------------
        # DRAFT ORDER
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draft_order (
                draft_position INTEGER PRIMARY KEY,

                espn_team_id INTEGER NOT NULL,

                team_name TEXT NOT NULL
            )
            """
        )

        # -----------------------------------------------------
        # DRAFT PICKS
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draft_picks (
                overall_pick INTEGER PRIMARY KEY,

                round_number INTEGER NOT NULL,

                pick_in_round INTEGER NOT NULL,

                espn_team_id INTEGER NOT NULL,

                team_name TEXT NOT NULL,

                espn_player_id INTEGER NOT NULL UNIQUE,

                player_name TEXT NOT NULL,

                position TEXT NOT NULL,

                nfl_team TEXT,

                discord_user_id INTEGER,

                picked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # -----------------------------------------------------
        # TEAM CLAIMS
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS team_claims (
                discord_user_id INTEGER PRIMARY KEY,

                espn_team_id INTEGER NOT NULL UNIQUE,

                team_name TEXT NOT NULL,

                claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # -----------------------------------------------------
        # PICK OWNERSHIP
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draft_pick_ownership (
                overall_pick INTEGER PRIMARY KEY,

                round_number INTEGER NOT NULL,

                pick_in_round INTEGER NOT NULL,

                original_espn_team_id INTEGER NOT NULL,

                original_team_name TEXT NOT NULL,

                current_espn_team_id INTEGER NOT NULL,

                current_team_name TEXT NOT NULL,

                traded INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        # -----------------------------------------------------
        # COMPLETED PICK TRADES
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draft_pick_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                pick_a INTEGER NOT NULL,

                pick_a_from_team_id INTEGER NOT NULL,

                pick_a_from_team_name TEXT NOT NULL,

                pick_a_to_team_id INTEGER NOT NULL,

                pick_a_to_team_name TEXT NOT NULL,

                pick_b INTEGER NOT NULL,

                pick_b_from_team_id INTEGER NOT NULL,

                pick_b_from_team_name TEXT NOT NULL,

                pick_b_to_team_id INTEGER NOT NULL,

                pick_b_to_team_name TEXT NOT NULL,

                discord_user_id INTEGER NOT NULL,

                traded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # -----------------------------------------------------
        # TRADE PROPOSALS
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draft_trade_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                pick_a INTEGER NOT NULL,

                pick_b INTEGER NOT NULL,

                proposer_discord_user_id INTEGER NOT NULL,

                recipient_discord_user_id INTEGER NOT NULL,

                proposer_team_id INTEGER NOT NULL,

                proposer_team_name TEXT NOT NULL,

                recipient_team_id INTEGER NOT NULL,

                recipient_team_name TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'PENDING',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                resolved_at TIMESTAMP
            )
            """
        )

        # -----------------------------------------------------
        # FEATURE REQUESTS
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feature_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                discord_user_id INTEGER NOT NULL,

                discord_username TEXT NOT NULL,

                subject TEXT NOT NULL,

                description TEXT NOT NULL,

                priority TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'OPEN',

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
            )
            """
        )

        connection.commit()


# =============================================================
# DRAFT STATE
# =============================================================

def get_draft_state():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_state
            WHERE id = 1
            """
        ).fetchone()


def end_draft():
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE draft_state
            SET active = 0
            WHERE id = 1
            """
        )

        connection.commit()


# =============================================================
# DRAFT ORDER
# =============================================================

def get_draft_order():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_order
            ORDER BY draft_position
            """
        ).fetchall()


# =============================================================
# INITIALIZE PICK OWNERSHIP
# =============================================================

def initialize_draft_pick_ownership():
    draft_state = get_draft_state()
    draft_order = get_draft_order()

    if not draft_order:
        return

    total_teams = draft_state[
        "total_teams"
    ]

    total_rounds = draft_state[
        "total_rounds"
    ]

    if (
        total_teams is None
        or total_rounds is None
    ):
        return

    with get_connection() as connection:

        existing_count = (
            connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM draft_pick_ownership
                """
            ).fetchone()["count"]
        )

        if existing_count > 0:
            return

        for round_number in range(
            1,
            total_rounds + 1,
        ):
            for pick_in_round in range(
                1,
                total_teams + 1,
            ):
                overall_pick = (
                    (round_number - 1)
                    * total_teams
                    + pick_in_round
                )

                if round_number % 2 == 1:
                    draft_position = (
                        pick_in_round
                    )

                else:
                    draft_position = (
                        total_teams
                        - pick_in_round
                        + 1
                    )

                team = draft_order[
                    draft_position - 1
                ]

                connection.execute(
                    """
                    INSERT INTO draft_pick_ownership (
                        overall_pick,
                        round_number,
                        pick_in_round,

                        original_espn_team_id,
                        original_team_name,

                        current_espn_team_id,
                        current_team_name,

                        traded
                    )
                    VALUES (
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        0
                    )
                    """,
                    (
                        overall_pick,
                        round_number,
                        pick_in_round,

                        team[
                            "espn_team_id"
                        ],

                        team[
                            "team_name"
                        ],

                        team[
                            "espn_team_id"
                        ],

                        team[
                            "team_name"
                        ],
                    ),
                )

        connection.commit()


# =============================================================
# START NEW DRAFT
# =============================================================

def start_new_draft(
    draft_order,
    total_rounds,
):
    total_teams = len(
        draft_order
    )

    with get_connection() as connection:

        connection.execute(
            """
            DELETE FROM draft_picks
            """
        )

        connection.execute(
            """
            DELETE FROM draft_order
            """
        )

        connection.execute(
            """
            DELETE FROM draft_pick_ownership
            """
        )

        connection.execute(
            """
            DELETE FROM draft_pick_trades
            """
        )

        connection.execute(
            """
            DELETE FROM draft_trade_proposals
            """
        )

        for draft_position, team in enumerate(
            draft_order,
            start=1,
        ):
            connection.execute(
                """
                INSERT INTO draft_order (
                    draft_position,
                    espn_team_id,
                    team_name
                )
                VALUES (?, ?, ?)
                """,
                (
                    draft_position,
                    team[
                        "espn_team_id"
                    ],
                    team[
                        "team_name"
                    ],
                ),
            )

        connection.execute(
            """
            UPDATE draft_state
            SET
                active = 1,
                current_pick = 1,
                total_teams = ?,
                total_rounds = ?,
                draftboard_channel_id = NULL,
                draftboard_message_id = NULL
            WHERE id = 1
            """,
            (
                total_teams,
                total_rounds,
            ),
        )

        connection.commit()

    initialize_draft_pick_ownership()


# =============================================================
# PICK OWNERSHIP
# =============================================================

def get_pick_owner(
    overall_pick,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_pick_ownership
            WHERE overall_pick = ?
            """,
            (
                overall_pick,
            ),
        ).fetchone()


def get_all_pick_ownership():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_pick_ownership
            ORDER BY overall_pick
            """
        ).fetchall()


# =============================================================
# CURRENT DRAFT TEAM
# =============================================================

def get_current_draft_team():
    state = get_draft_state()

    if not state[
        "active"
    ]:
        return None

    current_pick = state[
        "current_pick"
    ]

    total_teams = state[
        "total_teams"
    ]

    total_rounds = state[
        "total_rounds"
    ]

    if (
        current_pick is None
        or total_teams is None
        or total_rounds is None
    ):
        return None

    total_picks = (
        total_teams
        * total_rounds
    )

    if (
        current_pick < 1
        or current_pick > total_picks
    ):
        return None

    round_number = (
        (
            current_pick - 1
        )
        // total_teams
        + 1
    )

    pick_in_round = (
        (
            current_pick - 1
        )
        % total_teams
        + 1
    )

    owner = get_pick_owner(
        current_pick
    )

    if owner is None:
        return None

    return {
        "overall_pick": (
            current_pick
        ),

        "round_number": (
            round_number
        ),

        "pick_in_round": (
            pick_in_round
        ),

        "team": {
            "espn_team_id": owner[
                "current_espn_team_id"
            ],

            "team_name": owner[
                "current_team_name"
            ],
        },

        "original_team": {
            "espn_team_id": owner[
                "original_espn_team_id"
            ],

            "team_name": owner[
                "original_team_name"
            ],
        },

        "traded": bool(
            owner[
                "traded"
            ]
        ),
    }


# =============================================================
# SAVE DRAFT PICK
# =============================================================

def save_draft_pick(
    espn_player_id,
    player_name,
    position,
    nfl_team,
    discord_user_id,
):
    current = (
        get_current_draft_team()
    )

    if current is None:
        raise ValueError(
            "There is no active draft pick."
        )

    team = current[
        "team"
    ]

    overall_pick = current[
        "overall_pick"
    ]

    round_number = current[
        "round_number"
    ]

    pick_in_round = current[
        "pick_in_round"
    ]

    with get_connection() as connection:

        existing_player = (
            connection.execute(
                """
                SELECT *
                FROM draft_picks
                WHERE espn_player_id = ?
                """,
                (
                    espn_player_id,
                ),
            ).fetchone()
        )

        if existing_player is not None:
            raise ValueError(
                "That player has already been drafted."
            )

        connection.execute(
            """
            INSERT INTO draft_picks (
                overall_pick,
                round_number,
                pick_in_round,

                espn_team_id,
                team_name,

                espn_player_id,
                player_name,

                position,
                nfl_team,

                discord_user_id
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                overall_pick,
                round_number,
                pick_in_round,

                team[
                    "espn_team_id"
                ],

                team[
                    "team_name"
                ],

                espn_player_id,
                player_name,

                position,
                nfl_team,

                discord_user_id,
            ),
        )

        state = connection.execute(
            """
            SELECT *
            FROM draft_state
            WHERE id = 1
            """
        ).fetchone()

        total_picks = (
            state[
                "total_teams"
            ]
            * state[
                "total_rounds"
            ]
        )

        next_pick = (
            overall_pick
            + 1
        )

        if (
            overall_pick
            >= total_picks
        ):
            connection.execute(
                """
                UPDATE draft_state
                SET
                    current_pick = ?,
                    active = 0
                WHERE id = 1
                """,
                (
                    next_pick,
                ),
            )

        else:
            connection.execute(
                """
                UPDATE draft_state
                SET current_pick = ?
                WHERE id = 1
                """,
                (
                    next_pick,
                ),
            )

        connection.commit()

    return {
        "overall_pick": (
            overall_pick
        ),

        "round_number": (
            round_number
        ),

        "pick_in_round": (
            pick_in_round
        ),

        "team": {
            "espn_team_id": team[
                "espn_team_id"
            ],

            "team_name": team[
                "team_name"
            ],
        },

        "traded": current[
            "traded"
        ],
    }


# =============================================================
# DRAFT PICKS
# =============================================================

def get_all_draft_picks():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_picks
            ORDER BY overall_pick
            """
        ).fetchall()


def get_drafted_player_ids():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT espn_player_id
            FROM draft_picks
            """
        ).fetchall()

    return {
        row[
            "espn_player_id"
        ]
        for row in rows
    }


def get_last_draft_pick():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_picks
            ORDER BY overall_pick DESC
            LIMIT 1
            """
        ).fetchone()


# =============================================================
# UNDO LAST PICK
# =============================================================

def undo_last_draft_pick():
    last_pick = (
        get_last_draft_pick()
    )

    if last_pick is None:
        return None

    with get_connection() as connection:

        connection.execute(
            """
            DELETE FROM draft_picks
            WHERE overall_pick = ?
            """,
            (
                last_pick[
                    "overall_pick"
                ],
            ),
        )

        connection.execute(
            """
            UPDATE draft_state
            SET
                current_pick = ?,
                active = 1
            WHERE id = 1
            """,
            (
                last_pick[
                    "overall_pick"
                ],
            ),
        )

        connection.commit()

    return last_pick


# =============================================================
# DRAFTBOARD MESSAGE
# =============================================================

def save_draftboard_message(
    channel_id,
    message_id,
):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE draft_state
            SET
                draftboard_channel_id = ?,
                draftboard_message_id = ?
            WHERE id = 1
            """,
            (
                channel_id,
                message_id,
            ),
        )

        connection.commit()


# =============================================================
# TEAM CLAIMS
# =============================================================

def get_team_claim_by_user(
    discord_user_id,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM team_claims
            WHERE discord_user_id = ?
            """,
            (
                discord_user_id,
            ),
        ).fetchone()


def get_team_claim_by_team(
    espn_team_id,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM team_claims
            WHERE espn_team_id = ?
            """,
            (
                espn_team_id,
            ),
        ).fetchone()


def get_all_team_claims():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM team_claims
            ORDER BY team_name
            """
        ).fetchall()


def claim_team(
    discord_user_id,
    espn_team_id,
    team_name,
):
    with get_connection() as connection:

        existing_user_claim = (
            connection.execute(
                """
                SELECT *
                FROM team_claims
                WHERE discord_user_id = ?
                """,
                (
                    discord_user_id,
                ),
            ).fetchone()
        )

        existing_team_claim = (
            connection.execute(
                """
                SELECT *
                FROM team_claims
                WHERE espn_team_id = ?
                """,
                (
                    espn_team_id,
                ),
            ).fetchone()
        )

        if (
            existing_team_claim
            and existing_team_claim[
                "discord_user_id"
            ]
            != discord_user_id
        ):
            raise ValueError(
                (
                    "That fantasy team has "
                    "already been claimed."
                )
            )

        if existing_user_claim:
            connection.execute(
                """
                DELETE FROM team_claims
                WHERE discord_user_id = ?
                """,
                (
                    discord_user_id,
                ),
            )

        connection.execute(
            """
            INSERT INTO team_claims (
                discord_user_id,
                espn_team_id,
                team_name
            )
            VALUES (?, ?, ?)
            """,
            (
                discord_user_id,
                espn_team_id,
                team_name,
            ),
        )

        connection.commit()


def remove_team_claim(
    discord_user_id,
):
    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM team_claims
            WHERE discord_user_id = ?
            """,
            (
                discord_user_id,
            ),
        )

        connection.commit()


# =============================================================
# VALIDATE FUTURE PICK
# =============================================================

def validate_trade_pick(
    overall_pick,
):
    state = get_draft_state()

    total_teams = state[
        "total_teams"
    ]

    total_rounds = state[
        "total_rounds"
    ]

    current_pick = state[
        "current_pick"
    ]

    if (
        total_teams is None
        or total_rounds is None
    ):
        raise ValueError(
            "No draft has been initialized."
        )

    total_picks = (
        total_teams
        * total_rounds
    )

    if (
        overall_pick < 1
        or overall_pick > total_picks
    ):
        raise ValueError(
            f"Overall pick {overall_pick} does not exist."
        )

    if (
        current_pick is not None
        and overall_pick < current_pick
    ):
        raise ValueError(
            (
                f"Overall pick {overall_pick} "
                "has already been made."
            )
        )

    ownership = get_pick_owner(
        overall_pick
    )

    if ownership is None:
        raise ValueError(
            (
                f"Ownership for overall pick "
                f"{overall_pick} could not be found."
            )
        )

    return ownership


# =============================================================
# TRADE / SWAP TWO DRAFT PICKS
# =============================================================

def trade_draft_picks(
    pick_a,
    pick_b,
    discord_user_id,
):
    if pick_a == pick_b:
        raise ValueError(
            "A draft pick cannot be traded for itself."
        )

    owner_a = validate_trade_pick(
        pick_a
    )

    owner_b = validate_trade_pick(
        pick_b
    )

    team_a_id = owner_a[
        "current_espn_team_id"
    ]

    team_a_name = owner_a[
        "current_team_name"
    ]

    team_b_id = owner_b[
        "current_espn_team_id"
    ]

    team_b_name = owner_b[
        "current_team_name"
    ]

    if team_a_id == team_b_id:
        raise ValueError(
            (
                "Both draft picks are already owned "
                "by the same fantasy team."
            )
        )

    with get_connection() as connection:

        cursor = connection.execute(
            """
            INSERT INTO draft_pick_trades (
                pick_a,

                pick_a_from_team_id,
                pick_a_from_team_name,

                pick_a_to_team_id,
                pick_a_to_team_name,

                pick_b,

                pick_b_from_team_id,
                pick_b_from_team_name,

                pick_b_to_team_id,
                pick_b_to_team_name,

                discord_user_id
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                pick_a,

                team_a_id,
                team_a_name,

                team_b_id,
                team_b_name,

                pick_b,

                team_b_id,
                team_b_name,

                team_a_id,
                team_a_name,

                discord_user_id,
            ),
        )

        trade_id = cursor.lastrowid

        connection.execute(
            """
            UPDATE draft_pick_ownership
            SET
                current_espn_team_id = ?,
                current_team_name = ?,
                traded = 1
            WHERE overall_pick = ?
            """,
            (
                team_b_id,
                team_b_name,
                pick_a,
            ),
        )

        connection.execute(
            """
            UPDATE draft_pick_ownership
            SET
                current_espn_team_id = ?,
                current_team_name = ?,
                traded = 1
            WHERE overall_pick = ?
            """,
            (
                team_a_id,
                team_a_name,
                pick_b,
            ),
        )

        connection.commit()

    return {
        "trade_id": (
            trade_id
        ),

        "pick_a": {
            "overall_pick": (
                pick_a
            ),

            "round_number": owner_a[
                "round_number"
            ],

            "pick_in_round": owner_a[
                "pick_in_round"
            ],

            "previous_team_id": (
                team_a_id
            ),

            "previous_team_name": (
                team_a_name
            ),

            "new_team_id": (
                team_b_id
            ),

            "new_team_name": (
                team_b_name
            ),
        },

        "pick_b": {
            "overall_pick": (
                pick_b
            ),

            "round_number": owner_b[
                "round_number"
            ],

            "pick_in_round": owner_b[
                "pick_in_round"
            ],

            "previous_team_id": (
                team_b_id
            ),

            "previous_team_name": (
                team_b_name
            ),

            "new_team_id": (
                team_a_id
            ),

            "new_team_name": (
                team_a_name
            ),
        },
    }


# =============================================================
# COMPLETED TRADE HISTORY
# =============================================================

def get_all_pick_trades():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_pick_trades
            ORDER BY id
            """
        ).fetchall()


def get_pick_trade_history(
    overall_pick,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_pick_trades
            WHERE
                pick_a = ?
                OR pick_b = ?
            ORDER BY id
            """,
            (
                overall_pick,
                overall_pick,
            ),
        ).fetchall()


def get_last_pick_trade(
    overall_pick,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_pick_trades
            WHERE
                pick_a = ?
                OR pick_b = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                overall_pick,
                overall_pick,
            ),
        ).fetchone()


# =============================================================
# CHECK WHETHER TRADE CAN BE UNDONE
# =============================================================

def can_undo_trade(
    trade,
):
    with get_connection() as connection:

        newer_trade = connection.execute(
            """
            SELECT *
            FROM draft_pick_trades
            WHERE
                id > ?
                AND (
                    pick_a = ?
                    OR pick_b = ?
                    OR pick_a = ?
                    OR pick_b = ?
                )
            ORDER BY id
            LIMIT 1
            """,
            (
                trade[
                    "id"
                ],

                trade[
                    "pick_a"
                ],

                trade[
                    "pick_a"
                ],

                trade[
                    "pick_b"
                ],

                trade[
                    "pick_b"
                ],
            ),
        ).fetchone()

    return (
        newer_trade is None
    )


# =============================================================
# REFRESH TRADED FLAG
# =============================================================

def refresh_pick_traded_flag(
    connection,
    overall_pick,
):
    ownership = connection.execute(
        """
        SELECT *
        FROM draft_pick_ownership
        WHERE overall_pick = ?
        """,
        (
            overall_pick,
        ),
    ).fetchone()

    if ownership is None:
        return

    traded = int(
        ownership[
            "current_espn_team_id"
        ]
        != ownership[
            "original_espn_team_id"
        ]
    )

    connection.execute(
        """
        UPDATE draft_pick_ownership
        SET traded = ?
        WHERE overall_pick = ?
        """,
        (
            traded,
            overall_pick,
        ),
    )


# =============================================================
# UNDO LAST TRADE INVOLVING A PICK
# =============================================================

def undo_last_pick_trade(
    overall_pick,
):
    trade = get_last_pick_trade(
        overall_pick
    )

    if trade is None:
        return None

    validate_trade_pick(
        trade[
            "pick_a"
        ]
    )

    validate_trade_pick(
        trade[
            "pick_b"
        ]
    )

    if not can_undo_trade(
        trade
    ):
        raise ValueError(
            (
                "This trade cannot be undone because "
                "one of its picks was traded again afterward."
            )
        )

    with get_connection() as connection:

        connection.execute(
            """
            UPDATE draft_pick_ownership
            SET
                current_espn_team_id = ?,
                current_team_name = ?
            WHERE overall_pick = ?
            """,
            (
                trade[
                    "pick_a_from_team_id"
                ],

                trade[
                    "pick_a_from_team_name"
                ],

                trade[
                    "pick_a"
                ],
            ),
        )

        connection.execute(
            """
            UPDATE draft_pick_ownership
            SET
                current_espn_team_id = ?,
                current_team_name = ?
            WHERE overall_pick = ?
            """,
            (
                trade[
                    "pick_b_from_team_id"
                ],

                trade[
                    "pick_b_from_team_name"
                ],

                trade[
                    "pick_b"
                ],
            ),
        )

        connection.execute(
            """
            DELETE FROM draft_pick_trades
            WHERE id = ?
            """,
            (
                trade[
                    "id"
                ],
            ),
        )

        refresh_pick_traded_flag(
            connection,
            trade[
                "pick_a"
            ],
        )

        refresh_pick_traded_flag(
            connection,
            trade[
                "pick_b"
            ],
        )

        connection.commit()

    return {
        "trade_id": trade[
            "id"
        ],

        "pick_a": {
            "overall_pick": trade[
                "pick_a"
            ],

            "team_id": trade[
                "pick_a_from_team_id"
            ],

            "team_name": trade[
                "pick_a_from_team_name"
            ],
        },

        "pick_b": {
            "overall_pick": trade[
                "pick_b"
            ],

            "team_id": trade[
                "pick_b_from_team_id"
            ],

            "team_name": trade[
                "pick_b_from_team_name"
            ],
        },
    }


# =============================================================
# TRADE PROPOSALS
# =============================================================

def create_trade_proposal(
    pick_a,
    pick_b,
    proposer_discord_user_id,
    recipient_discord_user_id,
    proposer_team_id,
    proposer_team_name,
    recipient_team_id,
    recipient_team_name,
):
    if pick_a == pick_b:
        raise ValueError(
            "A draft pick cannot be traded for itself."
        )

    with get_connection() as connection:

        existing = connection.execute(
            """
            SELECT *
            FROM draft_trade_proposals
            WHERE
                status = 'PENDING'
                AND (
                    pick_a = ?
                    OR pick_b = ?
                    OR pick_a = ?
                    OR pick_b = ?
                )
            LIMIT 1
            """,
            (
                pick_a,
                pick_a,
                pick_b,
                pick_b,
            ),
        ).fetchone()

        if existing is not None:
            raise ValueError(
                (
                    "One of those picks is already involved "
                    "in a pending trade proposal."
                )
            )

        cursor = connection.execute(
            """
            INSERT INTO draft_trade_proposals (
                pick_a,
                pick_b,

                proposer_discord_user_id,
                recipient_discord_user_id,

                proposer_team_id,
                proposer_team_name,

                recipient_team_id,
                recipient_team_name,

                status
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                'PENDING'
            )
            """,
            (
                pick_a,
                pick_b,

                proposer_discord_user_id,
                recipient_discord_user_id,

                proposer_team_id,
                proposer_team_name,

                recipient_team_id,
                recipient_team_name,
            ),
        )

        connection.commit()

        return cursor.lastrowid


def get_trade_proposal(
    proposal_id,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_trade_proposals
            WHERE id = ?
            """,
            (
                proposal_id,
            ),
        ).fetchone()


def get_pending_trade_proposals():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_trade_proposals
            WHERE status = 'PENDING'
            ORDER BY id
            """
        ).fetchall()


def get_pending_trade_proposals_for_user(
    discord_user_id,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_trade_proposals
            WHERE
                status = 'PENDING'
                AND (
                    proposer_discord_user_id = ?
                    OR recipient_discord_user_id = ?
                )
            ORDER BY id
            """,
            (
                discord_user_id,
                discord_user_id,
            ),
        ).fetchall()


def update_trade_proposal_status(
    proposal_id,
    status,
):
    allowed_statuses = {
        "PENDING",
        "ACCEPTED",
        "DECLINED",
        "CANCELLED",
        "INVALID",
    }

    if status not in allowed_statuses:
        raise ValueError(
            "Invalid trade proposal status."
        )

    with get_connection() as connection:

        if status == "PENDING":
            connection.execute(
                """
                UPDATE draft_trade_proposals
                SET
                    status = ?,
                    resolved_at = NULL
                WHERE id = ?
                """,
                (
                    status,
                    proposal_id,
                ),
            )

        else:
            connection.execute(
                """
                UPDATE draft_trade_proposals
                SET
                    status = ?,
                    resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    status,
                    proposal_id,
                ),
            )

        connection.commit()


# =============================================================
# VALIDATE TRADE PROPOSAL
# =============================================================

def validate_trade_proposal(
    proposal_id,
):
    proposal = get_trade_proposal(
        proposal_id
    )

    if proposal is None:
        raise ValueError(
            "That trade proposal does not exist."
        )

    if (
        proposal[
            "status"
        ]
        != "PENDING"
    ):
        raise ValueError(
            (
                "That trade proposal is no "
                "longer pending."
            )
        )

    owner_a = validate_trade_pick(
        proposal[
            "pick_a"
        ]
    )

    owner_b = validate_trade_pick(
        proposal[
            "pick_b"
        ]
    )

    if (
        owner_a[
            "current_espn_team_id"
        ]
        != proposal[
            "proposer_team_id"
        ]
    ):
        raise ValueError(
            (
                "The offered pick is no longer "
                "owned by the proposing team."
            )
        )

    if (
        owner_b[
            "current_espn_team_id"
        ]
        != proposal[
            "recipient_team_id"
        ]
    ):
        raise ValueError(
            (
                "The requested pick is no longer "
                "owned by the receiving team."
            )
        )

    return {
        "proposal": (
            proposal
        ),

        "pick_a_owner": (
            owner_a
        ),

        "pick_b_owner": (
            owner_b
        ),
    }


# =============================================================
# ACCEPT TRADE PROPOSAL
# =============================================================

def accept_trade_proposal(
    proposal_id,
    accepting_discord_user_id,
):
    validation = (
        validate_trade_proposal(
            proposal_id
        )
    )

    proposal = validation[
        "proposal"
    ]

    if (
        accepting_discord_user_id
        != proposal[
            "recipient_discord_user_id"
        ]
    ):
        raise ValueError(
            (
                "Only the recipient of this trade "
                "proposal can accept it."
            )
        )

    result = trade_draft_picks(
        pick_a=proposal[
            "pick_a"
        ],

        pick_b=proposal[
            "pick_b"
        ],

        discord_user_id=(
            accepting_discord_user_id
        ),
    )

    update_trade_proposal_status(
        proposal_id,
        "ACCEPTED",
    )

    return result


# =============================================================
# DECLINE TRADE PROPOSAL
# =============================================================

def decline_trade_proposal(
    proposal_id,
    declining_discord_user_id,
):
    proposal = get_trade_proposal(
        proposal_id
    )

    if proposal is None:
        raise ValueError(
            "That trade proposal does not exist."
        )

    if (
        proposal[
            "status"
        ]
        != "PENDING"
    ):
        raise ValueError(
            (
                "That trade proposal is no "
                "longer pending."
            )
        )

    if (
        declining_discord_user_id
        != proposal[
            "recipient_discord_user_id"
        ]
    ):
        raise ValueError(
            (
                "Only the recipient of this trade "
                "proposal can decline it."
            )
        )

    update_trade_proposal_status(
        proposal_id,
        "DECLINED",
    )

    return proposal


# =============================================================
# CANCEL TRADE PROPOSAL
# =============================================================

def cancel_trade_proposal(
    proposal_id,
    cancelling_discord_user_id,
    admin_override=False,
):
    proposal = get_trade_proposal(
        proposal_id
    )

    if proposal is None:
        raise ValueError(
            "That trade proposal does not exist."
        )

    if (
        proposal[
            "status"
        ]
        != "PENDING"
    ):
        raise ValueError(
            (
                "That trade proposal is no "
                "longer pending."
            )
        )

    if (
        not admin_override
        and cancelling_discord_user_id
        != proposal[
            "proposer_discord_user_id"
        ]
    ):
        raise ValueError(
            (
                "Only the proposer can cancel "
                "this trade proposal."
            )
        )

    update_trade_proposal_status(
        proposal_id,
        "CANCELLED",
    )

    return proposal


# =============================================================
# INVALIDATE PENDING PROPOSALS
# =============================================================

def invalidate_pending_trade_proposals_for_picks(
    pick_a,
    pick_b,
    exclude_proposal_id=None,
):
    with get_connection() as connection:

        if exclude_proposal_id is None:
            connection.execute(
                """
                UPDATE draft_trade_proposals
                SET
                    status = 'INVALID',
                    resolved_at = CURRENT_TIMESTAMP
                WHERE
                    status = 'PENDING'
                    AND (
                        pick_a = ?
                        OR pick_b = ?
                        OR pick_a = ?
                        OR pick_b = ?
                    )
                """,
                (
                    pick_a,
                    pick_a,
                    pick_b,
                    pick_b,
                ),
            )

        else:
            connection.execute(
                """
                UPDATE draft_trade_proposals
                SET
                    status = 'INVALID',
                    resolved_at = CURRENT_TIMESTAMP
                WHERE
                    status = 'PENDING'
                    AND id != ?
                    AND (
                        pick_a = ?
                        OR pick_b = ?
                        OR pick_a = ?
                        OR pick_b = ?
                    )
                """,
                (
                    exclude_proposal_id,
                    pick_a,
                    pick_a,
                    pick_b,
                    pick_b,
                ),
            )

        connection.commit()


# =============================================================
# FEATURE REQUESTS
# =============================================================

def create_feature_request(
    discord_user_id,
    discord_username,
    subject,
    description,
    priority,
):
    allowed_priorities = {
        "P1",
        "P2",
        "P3",
        "P4",
    }

    priority = (
        priority
        .upper()
        .strip()
    )

    if priority not in allowed_priorities:
        raise ValueError(
            (
                "Priority must be one of: "
                "P1, P2, P3, or P4."
            )
        )

    subject = subject.strip()
    description = description.strip()

    if not subject:
        raise ValueError(
            "Feature request subject cannot be empty."
        )

    if not description:
        raise ValueError(
            "Feature request description cannot be empty."
        )

    with get_connection() as connection:

        cursor = connection.execute(
            """
            INSERT INTO feature_requests (
                discord_user_id,
                discord_username,
                subject,
                description,
                priority,
                status
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                'OPEN'
            )
            """,
            (
                discord_user_id,
                discord_username,
                subject,
                description,
                priority,
            ),
        )

        connection.commit()

        feature_request_id = (
            cursor.lastrowid
        )

    return get_feature_request(
        feature_request_id
    )


def get_feature_request(
    feature_request_id,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM feature_requests
            WHERE id = ?
            """,
            (
                feature_request_id,
            ),
        ).fetchone()


def get_all_feature_requests():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM feature_requests
            ORDER BY id DESC
            """
        ).fetchall()


def get_feature_requests_by_status(
    status,
):
    allowed_statuses = {
        "OPEN",
        "PLANNED",
        "IN_PROGRESS",
        "COMPLETED",
        "DECLINED",
    }

    status = (
        status
        .upper()
        .strip()
    )

    if status not in allowed_statuses:
        raise ValueError(
            "Invalid feature request status."
        )

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM feature_requests
            WHERE status = ?
            ORDER BY id DESC
            """,
            (
                status,
            ),
        ).fetchall()


def update_feature_request_status(
    feature_request_id,
    status,
):
    allowed_statuses = {
        "OPEN",
        "PLANNED",
        "IN_PROGRESS",
        "COMPLETED",
        "DECLINED",
    }

    status = (
        status
        .upper()
        .strip()
    )

    if status not in allowed_statuses:
        raise ValueError(
            (
                "Feature request status must be "
                "OPEN, PLANNED, IN_PROGRESS, "
                "COMPLETED, or DECLINED."
            )
        )

    with get_connection() as connection:

        existing = connection.execute(
            """
            SELECT *
            FROM feature_requests
            WHERE id = ?
            """,
            (
                feature_request_id,
            ),
        ).fetchone()

        if existing is None:
            raise ValueError(
                (
                    f"Feature request "
                    f"#{feature_request_id} does not exist."
                )
            )

        connection.execute(
            """
            UPDATE feature_requests
            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                status,
                feature_request_id,
            ),
        )

        connection.commit()

    return get_feature_request(
        feature_request_id
    )


# =============================================================
# INITIALIZE ON IMPORT
# =============================================================

initialize_database()

initialize_draft_pick_ownership()