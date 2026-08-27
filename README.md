Flint Michigan Megabowl Bot

A custom Discord bot built for the Flint Michigan Megabowl fantasy football league.

The bot is designed to move league administration into Discord, with a particular focus on running the league's offline draft. It connects Discord members to their ESPN fantasy teams, manages draft-pick ownership and trades, records draft selections, maintains a live draft board, runs the draft clock, and provides tools for league feedback and administration.

Current release: v1.1.0

Features

Team Management

League members can claim their ESPN fantasy team from Discord. A successful claim links the member's Discord account to the team and grants the server's Owner role.

Administrative tools are available to the Commissioner and Developer roles for viewing and correcting team claims.

Draft Management

The bot supports a persistent snake draft with:

    ESPN team integration
    Configurable draft order and round count
    Player autocomplete
    Prevention of duplicate player selections
    Persistent pick history
    Draft-pick ownership tracking
    Traded-pick indicators
    Undo support for administrators
    Draft status reporting
    Exportable draft results
    Live Draft Board
    The bot maintains a persistent Discord draft board that updates as the draft progresses.
    The board displays:
        Recent draft rounds
        Selected players
        The team currently on the clock
        The active clock deadline
        Traded picks
        Expired picks
        Outstanding catch-up picks
        12-Hour Draft ClockEach scheduled pick receives a 12-hour clock.

    The bot automatically:
        Mentions the pick owner when their clock begins
        Sends a reminder with 6 hours remaining
        Sends a reminder with 30 minutes remaining
        Expires the pick when the 12-hour clock reaches zero
        Immediately starts the next scheduled pick
        Clock state is stored persistently so a bot restart does not reset the draft clock.
        Catch-Up Picks
        Timing out does not stop the draft.

    When a clock expires:
        The expired pick becomes a catch-up pick.
        The next scheduled pick immediately goes on the clock.
        The owner of the expired pick may make that selection later.
        Catch-up selections do not interrupt or reset the active draft clock.
        If a team owes multiple catch-up picks, the oldest expired pick is filled first.
        A team can therefore owe a catch-up pick while simultaneously being on the clock for a later scheduled pick.

Draft-Pick Trading
    Managers can propose trades involving draft picks. The receiving manager can accept or decline the proposal, and the proposer can cancel a pending proposal.
    The bot tracks current and original pick ownership and updates the draft accordingly when a trade is completed.
    Canceled proposals update their original Discord message and disable the proposal controls.
    Feature Requests and Bug Reports
    League members can submit feature requests and bug reports directly through Discord.


Submissions support priorities:
    P1 — Critical
    P2 — High
    P3 — Medium
    P4 — Low

Commissioner/Developer administration tools support managing the lifecycle of submitted feedback.

Roles
The bot recognizes three primary Discord roles:
    Owner
    A league member who has claimed a fantasy team. Owners can use the normal manager-facing league, draft, and trade functionality.

    Commissioner
    League administrator with access to administrative draft and league-management commands.

    Developer
    Bot administrator with the same elevated draft-management access used for development and maintenance.

Discord's command permissions and channel overrides can be used to further control where commands are visible and who can use them.


Architecture
The project is written in Python using discord.py.

At a high level:

Discord
   │
   ▼
Discord Bot
   │
   ├── League / Team Management
   ├── Draft Management
   ├── Draft Clock
   ├── Draft-Pick Trading
   ├── Feature Requests
   └── Bug Reports
   │
   ├──────────────► ESPN Fantasy Football
   │
   ▼
SQLite Databases

SQLite is used for persistent bot state, including draft state, draft picks, pick ownership, trade proposals, team claims, clock state, feature requests, and bug reports.


Project Structure
The project is organized around Discord cogs and shared services.

flint-michigan-megabowl-bot/
├── bot.py
├── cogs/
│   ├── draft.py
│   ├── league.py
│   ├── member_management.py
│   ├── feature_requests.py
│   └── bug_reports.py
├── database/
│   └── database.py
├── services/
│   └── espn_service.py
├── .env.example
└── requirements.txt

The exact repository structure may evolve as new features are added.


Configuration
The bot uses environment variables for secrets and deployment-specific configuration. Use .env.example as the source of truth for the variables required by the current version.

Create a local .env file from the example:

Copy-Item .env.example .env

Then populate the required values.

Never commit .env to GitHub. Tokens, ESPN credentials/cookies, Discord IDs that are intentionally environment-specific, and other secrets should remain outside source control.


Local Development
Clone the repository and enter the project directory:
    git clone <repository-url>
    cd flint-michigan-megabowl-bot

Create a virtual environment:
    python -m venv .venv

Activate it in PowerShell:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
    .\.venv\Scripts\Activate.ps1

Install dependencies:
    pip install -r requirements.txt

Create and configure .env, then start the bot:
    python bot.py

Development Workflow
Development is performed on the dev branch.

dev
 │
 │ development + testing
 ▼
Pull Request
 │
 ▼
main
 │
 ▼
Production

A typical development cycle is:

git switch dev
git pull

Make and test changes, then:

git add .
git commit -m "Describe the change"
git push origin dev

When a release is ready, merge dev into main through a pull request.

Deployment
The production bot is deployed through Railway from the main branch.

The intended release flow is:

dev
 ↓
Pull Request
 ↓
main
 ↓
Railway deployment
 ↓
Production smoke test
 ↓
GitHub release tag

Production environment variables are configured in Railway rather than committed to the repository.

Releases
The project follows semantic versioning:

MAJOR.MINOR.PATCH

Examples:
    1.0.1 — bug fix / patch release

    1.1.0 — backwards-compatible feature release

    2.0.0 — major redesign or breaking change

v1.1.0

v1.1 added:
    Bug reporting
    Feature-request and bug-report administration
    Persistent 12-hour draft clocks
    Start, 6-hour, and 30-minute clock notifications
    Automatic timeout advancement
    Catch-up picks
    Draftboard clock and catch-up visibility
    Improved draft status information
    Trade-proposal cancellation message cleanup

Roadmap
Potential v1.2 improvements currently include:
    /my-pick-numbers an Owner command for easier identification of what overall pick numbers you have for trading
    More accurate messaging when the final scheduled draft pick times out
    Proactively updating Discord trade-proposal messages when another transaction makes the proposal invalid
    Additional features will be driven by actual league usage and feedback.

Purpose
This is a purpose-built bot for the Flint Michigan Megabowl rather than a general-purpose public fantasy football bot.

The goal is simple: automate the repetitive administrative parts of running the league while keeping the draft and league activity inside the Discord server.