import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


# =============================================================
# DATABASE CONFIG
# =============================================================

DATABASE_PATH = Path(
    os.getenv(
        "DATABASE_PATH",
        "megabowl.db",
    )
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

                discord_channel_id INTEGER,

                discord_message_id INTEGER,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                resolved_at TIMESTAMP
            )
            """
        )

        trade_proposal_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(draft_trade_proposals)"
            ).fetchall()
        }

        if "discord_channel_id" not in trade_proposal_columns:
            connection.execute(
                "ALTER TABLE draft_trade_proposals ADD COLUMN discord_channel_id INTEGER"
            )

        if "discord_message_id" not in trade_proposal_columns:
            connection.execute(
                "ALTER TABLE draft_trade_proposals ADD COLUMN discord_message_id INTEGER"
            )

        # -----------------------------------------------------
        # DRAFT STATE MIGRATION
        # -----------------------------------------------------

        draft_state_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(draft_state)"
            ).fetchall()
        }

        if "draft_channel_id" not in draft_state_columns:
            connection.execute(
                "ALTER TABLE draft_state ADD COLUMN draft_channel_id INTEGER"
            )

        # -----------------------------------------------------
        # DRAFT PICK CLOCK
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS draft_pick_clock (
                overall_pick INTEGER PRIMARY KEY,

                status TEXT NOT NULL DEFAULT 'WAITING',

                clock_started_at TEXT,

                clock_expires_at TEXT,

                start_notification_sent INTEGER NOT NULL DEFAULT 0,

                six_hour_reminder_sent INTEGER NOT NULL DEFAULT 0,

                thirty_minute_reminder_sent INTEGER NOT NULL DEFAULT 0,

                expiration_notification_sent INTEGER NOT NULL DEFAULT 0,

                expired_at TEXT,

                completed_at TEXT,

                completed_from_status TEXT,

                FOREIGN KEY (overall_pick)
                    REFERENCES draft_pick_ownership(overall_pick)
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

                discord_channel_id INTEGER,

                discord_message_id INTEGER,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
            )
            """
        )

        feature_request_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(feature_requests)"
            ).fetchall()
        }

        if "discord_channel_id" not in feature_request_columns:
            connection.execute(
                "ALTER TABLE feature_requests ADD COLUMN discord_channel_id INTEGER"
            )

        if "discord_message_id" not in feature_request_columns:
            connection.execute(
                "ALTER TABLE feature_requests ADD COLUMN discord_message_id INTEGER"
            )

        # -----------------------------------------------------
        # BUG REPORTS
        # -----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                discord_user_id INTEGER NOT NULL,

                discord_username TEXT NOT NULL,

                subject TEXT NOT NULL,

                description TEXT NOT NULL,

                command_name TEXT,

                priority TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'OPEN',

                discord_channel_id INTEGER,

                discord_message_id INTEGER,

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
# DRAFT CLOCK HELPERS
# =============================================================

DRAFT_CLOCK_HOURS = 12

DRAFT_CLOCK_STATUSES = {
    "WAITING",
    "ON_CLOCK",
    "EXPIRED",
    "COMPLETED",
}


def _utc_now():
    return datetime.now(timezone.utc)


def _to_utc_iso(value):
    if value is None:
        value = _utc_now()

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.isoformat()


def _parse_utc_timestamp(value):
    if value is None:
        return None

    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _clock_window(started_at=None):
    start = started_at or _utc_now()

    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    else:
        start = start.astimezone(timezone.utc)

    expires = start + timedelta(hours=DRAFT_CLOCK_HOURS)

    return (
        _to_utc_iso(start),
        _to_utc_iso(expires),
    )


def initialize_draft_pick_clock(
    reset=False,
    started_at=None,
):
    state = get_draft_state()

    total_teams = state["total_teams"]
    total_rounds = state["total_rounds"]

    if total_teams is None or total_rounds is None:
        return

    total_picks = total_teams * total_rounds

    if total_picks <= 0:
        return

    existing_picks = {
        row["overall_pick"]
        for row in get_all_draft_picks()
    }

    current_pick = state["current_pick"] or 1

    with get_connection() as connection:
        if reset:
            connection.execute(
                "DELETE FROM draft_pick_clock"
            )

        existing_count = connection.execute(
            "SELECT COUNT(*) AS count FROM draft_pick_clock"
        ).fetchone()["count"]

        if existing_count > 0 and not reset:
            return

        for overall_pick in range(1, total_picks + 1):
            if overall_pick in existing_picks:
                status = "COMPLETED"
            elif overall_pick < current_pick:
                status = "EXPIRED"
            elif (
                state["active"]
                and overall_pick == current_pick
            ):
                status = "ON_CLOCK"
            else:
                status = "WAITING"

            clock_started_at = None
            clock_expires_at = None

            if status == "ON_CLOCK":
                (
                    clock_started_at,
                    clock_expires_at,
                ) = _clock_window(started_at)

            connection.execute(
                """
                INSERT INTO draft_pick_clock (
                    overall_pick,
                    status,
                    clock_started_at,
                    clock_expires_at,
                    expired_at,
                    completed_at,
                    completed_from_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    overall_pick,
                    status,
                    clock_started_at,
                    clock_expires_at,
                    (
                        _to_utc_iso(started_at)
                        if status == "EXPIRED"
                        else None
                    ),
                    (
                        _to_utc_iso(started_at)
                        if status == "COMPLETED"
                        else None
                    ),
                    None,
                ),
            )

        connection.commit()


def get_pick_clock(overall_pick):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_pick_clock
            WHERE overall_pick = ?
            """,
            (overall_pick,),
        ).fetchone()


def get_all_pick_clocks():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM draft_pick_clock
            ORDER BY overall_pick
            """
        ).fetchall()


def get_current_pick_clock():
    state = get_draft_state()
    current_pick = state["current_pick"]

    if current_pick is None:
        return None

    return get_pick_clock(current_pick)


def get_expired_picks_for_team(
    espn_team_id,
):
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                c.*,
                o.round_number,
                o.pick_in_round,
                o.current_espn_team_id,
                o.current_team_name,
                o.original_espn_team_id,
                o.original_team_name,
                o.traded
            FROM draft_pick_clock c
            JOIN draft_pick_ownership o
                ON o.overall_pick = c.overall_pick
            WHERE
                c.status = 'EXPIRED'
                AND o.current_espn_team_id = ?
            ORDER BY c.overall_pick
            """,
            (espn_team_id,),
        ).fetchall()


def get_oldest_expired_pick_for_team(
    espn_team_id,
):
    picks = get_expired_picks_for_team(
        espn_team_id
    )

    if not picks:
        return None

    return picks[0]


def get_all_expired_picks():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                c.*,
                o.round_number,
                o.pick_in_round,
                o.current_espn_team_id,
                o.current_team_name,
                o.original_espn_team_id,
                o.original_team_name,
                o.traded
            FROM draft_pick_clock c
            JOIN draft_pick_ownership o
                ON o.overall_pick = c.overall_pick
            WHERE c.status = 'EXPIRED'
            ORDER BY c.overall_pick
            """
        ).fetchall()


def get_outstanding_expired_pick_count():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM draft_pick_clock
            WHERE status = 'EXPIRED'
            """
        ).fetchone()["count"]


def start_pick_clock(
    overall_pick,
    started_at=None,
):
    clock = get_pick_clock(overall_pick)

    if clock is None:
        raise ValueError(
            f"Clock state for overall pick {overall_pick} does not exist."
        )

    if clock["status"] == "COMPLETED":
        raise ValueError(
            f"Overall pick {overall_pick} has already been completed."
        )

    (
        clock_started_at,
        clock_expires_at,
    ) = _clock_window(started_at)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE draft_pick_clock
            SET
                status = 'ON_CLOCK',
                clock_started_at = ?,
                clock_expires_at = ?,
                start_notification_sent = 0,
                six_hour_reminder_sent = 0,
                thirty_minute_reminder_sent = 0,
                expiration_notification_sent = 0,
                expired_at = NULL,
                completed_at = NULL,
                completed_from_status = NULL
            WHERE overall_pick = ?
            """,
            (
                clock_started_at,
                clock_expires_at,
                overall_pick,
            ),
        )
        connection.commit()

    return get_pick_clock(overall_pick)


def mark_clock_notification_sent(
    overall_pick,
    notification_type,
):
    column_map = {
        "START": "start_notification_sent",
        "SIX_HOUR": "six_hour_reminder_sent",
        "THIRTY_MINUTE": "thirty_minute_reminder_sent",
        "EXPIRED": "expiration_notification_sent",
    }

    normalized = notification_type.upper().strip()
    column = column_map.get(normalized)

    if column is None:
        raise ValueError(
            "Invalid draft clock notification type."
        )

    with get_connection() as connection:
        connection.execute(
            f"""
            UPDATE draft_pick_clock
            SET {column} = 1
            WHERE overall_pick = ?
            """,
            (overall_pick,),
        )
        connection.commit()

    return get_pick_clock(overall_pick)


def get_due_clock_notifications(
    now=None,
):
    state = get_draft_state()

    if not state["active"]:
        return []

    current_pick = state["current_pick"]

    if current_pick is None:
        return []

    clock = get_pick_clock(current_pick)

    if clock is None or clock["status"] != "ON_CLOCK":
        return []

    now_utc = now or _utc_now()

    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)

    started_at = _parse_utc_timestamp(
        clock["clock_started_at"]
    )
    expires_at = _parse_utc_timestamp(
        clock["clock_expires_at"]
    )

    if started_at is None or expires_at is None:
        return []

    remaining = expires_at - now_utc

    # Only return the most relevant event. This prevents a bot that
    # was offline for several hours from sending multiple stale
    # reminders at once when it reconnects.
    if remaining <= timedelta(0):
        return ["EXPIRED"]

    if remaining <= timedelta(minutes=30):
        if not clock["thirty_minute_reminder_sent"]:
            return ["THIRTY_MINUTE"]
        return []

    if remaining <= timedelta(hours=6):
        if not clock["six_hour_reminder_sent"]:
            return ["SIX_HOUR"]
        return []

    if not clock["start_notification_sent"]:
        return ["START"]

    return []


def get_unnotified_expired_picks():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                c.*,
                o.round_number,
                o.pick_in_round,
                o.current_espn_team_id,
                o.current_team_name,
                o.original_espn_team_id,
                o.original_team_name,
                o.traded
            FROM draft_pick_clock c
            JOIN draft_pick_ownership o
                ON o.overall_pick = c.overall_pick
            WHERE
                c.status = 'EXPIRED'
                AND c.expiration_notification_sent = 0
            ORDER BY c.overall_pick
            """
        ).fetchall()


def expire_current_pick_and_advance(
    now=None,
):
    now_utc = now or _utc_now()

    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)

    state = get_draft_state()

    if not state["active"]:
        return None

    current_pick = state["current_pick"]
    total_teams = state["total_teams"]
    total_rounds = state["total_rounds"]

    if (
        current_pick is None
        or total_teams is None
        or total_rounds is None
    ):
        return None

    total_picks = total_teams * total_rounds

    if current_pick > total_picks:
        return None

    clock = get_pick_clock(current_pick)

    if clock is None or clock["status"] != "ON_CLOCK":
        return None

    expires_at = _parse_utc_timestamp(
        clock["clock_expires_at"]
    )

    if expires_at is None or now_utc < expires_at:
        return None

    next_pick = current_pick + 1
    next_clock = None

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE draft_pick_clock
            SET
                status = 'EXPIRED',
                expired_at = ?,
                completed_at = NULL,
                completed_from_status = NULL
            WHERE
                overall_pick = ?
                AND status = 'ON_CLOCK'
            """,
            (
                _to_utc_iso(now_utc),
                current_pick,
            ),
        )

        if next_pick <= total_picks:
            (
                next_started_at,
                next_expires_at,
            ) = _clock_window(now_utc)

            connection.execute(
                """
                UPDATE draft_pick_clock
                SET
                    status = 'ON_CLOCK',
                    clock_started_at = ?,
                    clock_expires_at = ?,
                    start_notification_sent = 0,
                    six_hour_reminder_sent = 0,
                    thirty_minute_reminder_sent = 0,
                    expiration_notification_sent = 0,
                    expired_at = NULL,
                    completed_at = NULL,
                    completed_from_status = NULL
                WHERE overall_pick = ?
                """,
                (
                    next_started_at,
                    next_expires_at,
                    next_pick,
                ),
            )

            connection.execute(
                """
                UPDATE draft_state
                SET current_pick = ?
                WHERE id = 1
                """,
                (next_pick,),
            )

        else:
            connection.execute(
                """
                UPDATE draft_state
                SET current_pick = ?
                WHERE id = 1
                """,
                (next_pick,),
            )

        connection.commit()

    if next_pick <= total_picks:
        next_clock = get_pick_clock(next_pick)

    return {
        "expired_pick": current_pick,
        "expired_owner": get_pick_owner(current_pick),
        "next_pick": (
            next_pick
            if next_pick <= total_picks
            else None
        ),
        "next_clock": next_clock,
    }


def _complete_clock_pick(
    connection,
    overall_pick,
    previous_status,
    completed_at=None,
):
    connection.execute(
        """
        UPDATE draft_pick_clock
        SET
            status = 'COMPLETED',
            completed_at = ?,
            completed_from_status = ?
        WHERE overall_pick = ?
        """,
        (
            _to_utc_iso(completed_at),
            previous_status,
            overall_pick,
        ),
    )


def _start_next_scheduled_pick(
    connection,
    next_pick,
    total_picks,
    started_at=None,
):
    if next_pick > total_picks:
        return False

    (
        clock_started_at,
        clock_expires_at,
    ) = _clock_window(started_at)

    connection.execute(
        """
        UPDATE draft_pick_clock
        SET
            status = 'ON_CLOCK',
            clock_started_at = ?,
            clock_expires_at = ?,
            start_notification_sent = 0,
            six_hour_reminder_sent = 0,
            thirty_minute_reminder_sent = 0,
            expiration_notification_sent = 0,
            expired_at = NULL,
            completed_at = NULL,
            completed_from_status = NULL
        WHERE overall_pick = ?
        """,
        (
            clock_started_at,
            clock_expires_at,
            next_pick,
        ),
    )

    return True


# =============================================================
# START NEW DRAFT
# =============================================================

def start_new_draft(
    draft_order,
    total_rounds,
    draft_channel_id=None,
):
    total_teams = len(
        draft_order
    )

    with get_connection() as connection:

        connection.execute(
            "DELETE FROM draft_picks"
        )

        connection.execute(
            "DELETE FROM draft_order"
        )

        connection.execute(
            "DELETE FROM draft_pick_ownership"
        )

        connection.execute(
            "DELETE FROM draft_pick_clock"
        )

        connection.execute(
            "DELETE FROM draft_pick_trades"
        )

        connection.execute(
            "DELETE FROM draft_trade_proposals"
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
                    team["espn_team_id"],
                    team["team_name"],
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
                draft_channel_id = ?,
                draftboard_channel_id = NULL,
                draftboard_message_id = NULL
            WHERE id = 1
            """,
            (
                total_teams,
                total_rounds,
                draft_channel_id,
            ),
        )

        connection.commit()

    initialize_draft_pick_ownership()
    initialize_draft_pick_clock(
        reset=True
    )


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
    target_overall_pick=None,
):
    state = get_draft_state()

    if not state["active"]:
        raise ValueError(
            "There is no active draft."
        )

    current_pick = state["current_pick"]
    total_teams = state["total_teams"]
    total_rounds = state["total_rounds"]

    if total_teams is None or total_rounds is None:
        raise ValueError(
            "Draft configuration is incomplete."
        )

    total_picks = total_teams * total_rounds

    if target_overall_pick is None:
        target_overall_pick = current_pick

    if (
        target_overall_pick is None
        or target_overall_pick < 1
        or target_overall_pick > total_picks
    ):
        raise ValueError(
            "There is no valid draft pick to complete."
        )

    ownership = get_pick_owner(
        target_overall_pick
    )

    if ownership is None:
        raise ValueError(
            "Draft pick ownership could not be found."
        )

    clock = get_pick_clock(
        target_overall_pick
    )

    if clock is None:
        raise ValueError(
            "Draft clock state could not be found."
        )

    previous_clock_status = clock["status"]

    if previous_clock_status not in {
        "ON_CLOCK",
        "EXPIRED",
    }:
        if previous_clock_status == "COMPLETED":
            raise ValueError(
                "That draft pick has already been completed."
            )

        raise ValueError(
            "That draft pick is not currently eligible to be made."
        )

    if (
        previous_clock_status == "ON_CLOCK"
        and target_overall_pick != current_pick
    ):
        raise ValueError(
            "That pick is not the current scheduled pick."
        )

    overall_pick = target_overall_pick
    round_number = ownership["round_number"]
    pick_in_round = ownership["pick_in_round"]

    team = {
        "espn_team_id": ownership[
            "current_espn_team_id"
        ],
        "team_name": ownership[
            "current_team_name"
        ],
    }

    now_utc = _utc_now()

    with get_connection() as connection:
        existing_player = connection.execute(
            """
            SELECT *
            FROM draft_picks
            WHERE espn_player_id = ?
            """,
            (espn_player_id,),
        ).fetchone()

        if existing_player is not None:
            raise ValueError(
                "That player has already been drafted."
            )

        existing_pick = connection.execute(
            """
            SELECT *
            FROM draft_picks
            WHERE overall_pick = ?
            """,
            (overall_pick,),
        ).fetchone()

        if existing_pick is not None:
            raise ValueError(
                "That draft pick has already been completed."
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                overall_pick,
                round_number,
                pick_in_round,
                team["espn_team_id"],
                team["team_name"],
                espn_player_id,
                player_name,
                position,
                nfl_team,
                discord_user_id,
            ),
        )

        _complete_clock_pick(
            connection,
            overall_pick,
            previous_clock_status,
            now_utc,
        )

        if previous_clock_status == "ON_CLOCK":
            next_pick = overall_pick + 1

            if next_pick <= total_picks:
                _start_next_scheduled_pick(
                    connection,
                    next_pick,
                    total_picks,
                    now_utc,
                )

                connection.execute(
                    """
                    UPDATE draft_state
                    SET current_pick = ?
                    WHERE id = 1
                    """,
                    (next_pick,),
                )
            else:
                connection.execute(
                    """
                    UPDATE draft_state
                    SET current_pick = ?
                    WHERE id = 1
                    """,
                    (next_pick,),
                )

        remaining_incomplete = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM draft_pick_clock
            WHERE status != 'COMPLETED'
            """
        ).fetchone()["count"]

        if remaining_incomplete == 0:
            connection.execute(
                """
                UPDATE draft_state
                SET active = 0
                WHERE id = 1
                """
            )

        connection.commit()

    return {
        "overall_pick": overall_pick,
        "round_number": round_number,
        "pick_in_round": pick_in_round,
        "team": team,
        "traded": bool(ownership["traded"]),
        "catch_up": (
            previous_clock_status == "EXPIRED"
        ),
        "previous_clock_status": previous_clock_status,
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
            ORDER BY
                datetime(picked_at) DESC,
                rowid DESC
            LIMIT 1
            """
        ).fetchone()


# =============================================================
# UNDO LAST PICK
# =============================================================

def undo_last_draft_pick():
    last_pick = get_last_draft_pick()

    if last_pick is None:
        return None

    overall_pick = last_pick["overall_pick"]
    clock = get_pick_clock(overall_pick)

    completed_from_status = (
        clock["completed_from_status"]
        if clock is not None
        else None
    )

    state = get_draft_state()
    current_pick = state["current_pick"]
    total_teams = state["total_teams"]
    total_rounds = state["total_rounds"]

    total_picks = (
        total_teams * total_rounds
        if total_teams is not None
        and total_rounds is not None
        else 0
    )

    now_utc = _utc_now()

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM draft_picks
            WHERE overall_pick = ?
            """,
            (overall_pick,),
        )

        should_rewind_clock = (
            completed_from_status == "ON_CLOCK"
            and current_pick == overall_pick + 1
            and current_pick <= total_picks
        )

        if should_rewind_clock:
            connection.execute(
                """
                UPDATE draft_pick_clock
                SET
                    status = 'WAITING',
                    clock_started_at = NULL,
                    clock_expires_at = NULL,
                    start_notification_sent = 0,
                    six_hour_reminder_sent = 0,
                    thirty_minute_reminder_sent = 0,
                    expiration_notification_sent = 0,
                    expired_at = NULL,
                    completed_at = NULL,
                    completed_from_status = NULL
                WHERE overall_pick = ?
                """,
                (current_pick,),
            )

            (
                started_at,
                expires_at,
            ) = _clock_window(now_utc)

            connection.execute(
                """
                UPDATE draft_pick_clock
                SET
                    status = 'ON_CLOCK',
                    clock_started_at = ?,
                    clock_expires_at = ?,
                    start_notification_sent = 0,
                    six_hour_reminder_sent = 0,
                    thirty_minute_reminder_sent = 0,
                    expiration_notification_sent = 0,
                    expired_at = NULL,
                    completed_at = NULL,
                    completed_from_status = NULL
                WHERE overall_pick = ?
                """,
                (
                    started_at,
                    expires_at,
                    overall_pick,
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
                (overall_pick,),
            )

        else:
            connection.execute(
                """
                UPDATE draft_pick_clock
                SET
                    status = 'EXPIRED',
                    expired_at = ?,
                    completed_at = NULL,
                    completed_from_status = NULL
                WHERE overall_pick = ?
                """,
                (
                    _to_utc_iso(now_utc),
                    overall_pick,
                ),
            )

            connection.execute(
                """
                UPDATE draft_state
                SET active = 1
                WHERE id = 1
                """
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


def save_draft_channel(
    channel_id,
):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE draft_state
            SET draft_channel_id = ?
            WHERE id = 1
            """,
            (channel_id,),
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


def save_trade_proposal_message(
    proposal_id,
    discord_channel_id,
    discord_message_id,
):
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id
            FROM draft_trade_proposals
            WHERE id = ?
            """,
            (
                proposal_id,
            ),
        ).fetchone()

        if existing is None:
            raise ValueError(
                f"Trade proposal #{proposal_id} does not exist."
            )

        connection.execute(
            """
            UPDATE draft_trade_proposals
            SET
                discord_channel_id = ?,
                discord_message_id = ?
            WHERE id = ?
            """,
            (
                discord_channel_id,
                discord_message_id,
                proposal_id,
            ),
        )

        connection.commit()

    return get_trade_proposal(
        proposal_id
    )


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

FEATURE_REQUEST_STATUSES = {
    "OPEN",
    "PLANNED",
    "IN_PROGRESS",
    "COMPLETED",
    "DECLINED",
}

FEEDBACK_PRIORITIES = {
    "P1",
    "P2",
    "P3",
    "P4",
}


def create_feature_request(
    discord_user_id,
    discord_username,
    subject,
    description,
    priority,
):
    priority = priority.upper().strip()

    if priority not in FEEDBACK_PRIORITIES:
        raise ValueError(
            "Priority must be one of: P1, P2, P3, or P4."
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
            VALUES (?, ?, ?, ?, ?, 'OPEN')
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
        feature_request_id = cursor.lastrowid

    return get_feature_request(feature_request_id)


def save_feature_request_message(
    feature_request_id,
    discord_channel_id,
    discord_message_id,
):
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM feature_requests WHERE id = ?",
            (feature_request_id,),
        ).fetchone()

        if existing is None:
            raise ValueError(
                f"Feature request #{feature_request_id} does not exist."
            )

        connection.execute(
            """
            UPDATE feature_requests
            SET
                discord_channel_id = ?,
                discord_message_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                discord_channel_id,
                discord_message_id,
                feature_request_id,
            ),
        )
        connection.commit()

    return get_feature_request(feature_request_id)


def get_feature_request(feature_request_id):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM feature_requests WHERE id = ?",
            (feature_request_id,),
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


def get_feature_requests_by_status(status):
    status = status.upper().strip()

    if status not in FEATURE_REQUEST_STATUSES:
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
            (status,),
        ).fetchall()


def update_feature_request_status(
    feature_request_id,
    status,
):
    status = status.upper().strip()

    if status not in FEATURE_REQUEST_STATUSES:
        raise ValueError(
            (
                "Feature request status must be OPEN, PLANNED, "
                "IN_PROGRESS, COMPLETED, or DECLINED."
            )
        )

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM feature_requests WHERE id = ?",
            (feature_request_id,),
        ).fetchone()

        if existing is None:
            raise ValueError(
                f"Feature request #{feature_request_id} does not exist."
            )

        connection.execute(
            """
            UPDATE feature_requests
            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, feature_request_id),
        )
        connection.commit()

    return get_feature_request(feature_request_id)


# =============================================================
# BUG REPORTS
# =============================================================

BUG_REPORT_STATUSES = {
    "OPEN",
    "INVESTIGATING",
    "IN_PROGRESS",
    "FIXED",
    "CLOSED",
    "WONT_FIX",
}


def create_bug_report(
    discord_user_id,
    discord_username,
    subject,
    description,
    priority,
    command=None,
):
    priority = priority.upper().strip()

    if priority not in FEEDBACK_PRIORITIES:
        raise ValueError(
            "Priority must be one of: P1, P2, P3, or P4."
        )

    subject = subject.strip()
    description = description.strip()

    if command is not None:
        command = command.strip() or None

    if not subject:
        raise ValueError(
            "Bug report subject cannot be empty."
        )

    if not description:
        raise ValueError(
            "Bug report description cannot be empty."
        )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO bug_reports (
                discord_user_id,
                discord_username,
                subject,
                description,
                command_name,
                priority,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
            """,
            (
                discord_user_id,
                discord_username,
                subject,
                description,
                command,
                priority,
            ),
        )
        connection.commit()
        bug_report_id = cursor.lastrowid

    return get_bug_report(bug_report_id)


def save_bug_report_message(
    bug_report_id,
    discord_channel_id,
    discord_message_id,
):
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM bug_reports WHERE id = ?",
            (bug_report_id,),
        ).fetchone()

        if existing is None:
            raise ValueError(
                f"Bug report #{bug_report_id} does not exist."
            )

        connection.execute(
            """
            UPDATE bug_reports
            SET
                discord_channel_id = ?,
                discord_message_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                discord_channel_id,
                discord_message_id,
                bug_report_id,
            ),
        )
        connection.commit()

    return get_bug_report(bug_report_id)


def get_bug_report(bug_report_id):
    with get_connection() as connection:
        return connection.execute(
            "SELECT *, command_name AS command FROM bug_reports WHERE id = ?",
            (bug_report_id,),
        ).fetchone()


def get_all_bug_reports():
    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *, command_name AS command
            FROM bug_reports
            ORDER BY id DESC
            """
        ).fetchall()


def get_bug_reports_by_status(status):
    status = status.upper().strip()

    if status not in BUG_REPORT_STATUSES:
        raise ValueError(
            "Invalid bug report status."
        )

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *, command_name AS command
            FROM bug_reports
            WHERE status = ?
            ORDER BY id DESC
            """,
            (status,),
        ).fetchall()


def update_bug_report_status(
    bug_report_id,
    status,
):
    status = status.upper().strip()

    if status not in BUG_REPORT_STATUSES:
        raise ValueError(
            (
                "Bug report status must be OPEN, INVESTIGATING, "
                "IN_PROGRESS, FIXED, CLOSED, or WONT_FIX."
            )
        )

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM bug_reports WHERE id = ?",
            (bug_report_id,),
        ).fetchone()

        if existing is None:
            raise ValueError(
                f"Bug report #{bug_report_id} does not exist."
            )

        connection.execute(
            """
            UPDATE bug_reports
            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, bug_report_id),
        )
        connection.commit()

    return get_bug_report(bug_report_id)


# =============================================================
# INITIALIZE ON IMPORT
# =============================================================

initialize_database()

initialize_draft_pick_ownership()