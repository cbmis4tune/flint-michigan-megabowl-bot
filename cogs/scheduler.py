import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from services.espn_service import get_league


MOUNTAIN_TIME = ZoneInfo("America/Denver")

POST_TIME = time(
    hour=9,
    minute=0,
    tzinfo=MOUNTAIN_TIME,
)


def is_fantasy_season_active(league):
    """
    ESPN reports current_week as 0 before the fantasy season begins.

    For now, consider the fantasy season active once ESPN has advanced
    the league to Week 1 or later.
    """
    current_week = getattr(league, "current_week", None)

    return current_week is not None and current_week >= 1


class SchedulerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weekly_posts.start()

    def cog_unload(self):
        self.weekly_posts.cancel()

    async def get_standings_channel(self):
        channel_id = int(os.getenv("STANDINGS_CHANNEL_ID"))

        channel = self.bot.get_channel(channel_id)

        if channel is None:
            channel = await self.bot.fetch_channel(channel_id)

        return channel

    async def get_players_to_watch_channel(self):
        channel_id = int(os.getenv("PLAYERS_TO_WATCH_CHANNEL_ID"))

        channel = self.bot.get_channel(channel_id)

        if channel is None:
            channel = await self.bot.fetch_channel(channel_id)

        return channel

    @tasks.loop(time=POST_TIME)
    async def weekly_posts(self):
        now = datetime.now(MOUNTAIN_TIME)

        # Monday = 0
        # Tuesday = 1
        # Wednesday = 2

        if now.weekday() == 1:
            await self.post_standings()

        elif now.weekday() == 2:
            await self.post_players_to_watch()

    @weekly_posts.before_loop
    async def before_weekly_posts(self):
        await self.bot.wait_until_ready()

    async def post_standings(self):
        try:
            league = get_league()

            # Do not post outside the fantasy season
            if not is_fantasy_season_active(league):
                print(
                    "Fantasy season is not active. "
                    "Skipping weekly standings."
                )
                return

            channel = await self.get_standings_channel()

            standings_text = ""

            for position, team in enumerate(
                league.standings(),
                start=1,
            ):
                standings_text += (
                    f"**{position}. {team.team_name}**\n"
                    f"{team.wins}-{team.losses}-{team.ties}\n\n"
                )

            embed = discord.Embed(
                title=f"🏈 {league.settings.name} Standings",
                description=(
                    f"ESPN Fantasy Football — "
                    f"{os.getenv('ESPN_YEAR')}"
                ),
            )

            embed.add_field(
                name="Standings",
                value=standings_text,
                inline=False,
            )

            await channel.send(embed=embed)

            print("Weekly standings posted.")

        except Exception as error:
            print(f"Scheduled Standings Error: {error}")

    async def post_players_to_watch(self):
        try:
            league = get_league()

            # Do not post outside the fantasy season
            if not is_fantasy_season_active(league):
                print(
                    "Fantasy season is not active. "
                    "Skipping players-to-watch report."
                )
                return

            channel = await self.get_players_to_watch_channel()

            watch_statuses = {
                "QUESTIONABLE",
                "DOUBTFUL",
                "OUT",
                "INJURY_RESERVE",
                "SUSPENSION",
            }

            non_starting_slots = {
                "BE",
                "IR",
            }

            teams_with_players_to_watch = []

            for team in league.teams:
                players_to_watch = []

                for player in team.roster:
                    # Ignore bench and IR players
                    if player.lineupSlot in non_starting_slots:
                        continue

                    # Ignore healthy starters
                    if player.injuryStatus not in watch_statuses:
                        continue

                    players_to_watch.append(player)

                if players_to_watch:
                    teams_with_players_to_watch.append(
                        (team, players_to_watch)
                    )

            embed = discord.Embed(
                title="⚠️ Starting Players to Watch",
                description=(
                    "Starting players with injury or "
                    "availability concerns."
                ),
            )

            if not teams_with_players_to_watch:
                embed.description = (
                    "✅ No starting players currently "
                    "have injury concerns."
                )

            else:
                for team, players in teams_with_players_to_watch:
                    player_lines = []

                    for player in players:
                        status = (
                            player.injuryStatus
                            .replace("_", " ")
                            .title()
                        )

                        player_lines.append(
                            f"**{player.name}** "
                            f"({player.position} - {player.proTeam})\n"
                            f"↳ {status}"
                        )

                    embed.add_field(
                        name=team.team_name,
                        value="\n".join(player_lines),
                        inline=False,
                    )

            await channel.send(embed=embed)

            print("Weekly players-to-watch report posted.")

        except Exception as error:
            print(
                f"Scheduled Players to Watch Error: {error}"
            )


async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))