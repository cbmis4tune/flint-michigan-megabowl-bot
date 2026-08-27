import os

import discord
from discord import app_commands
from discord.ext import commands

from services.espn_service import (
    get_league,
    normalize_team_name
)


class LeagueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="standings",
        description="Show the current Flint Michigan Megabowl standings.",
    )
    async def standings(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            league = get_league()

            embed = discord.Embed(
                title=f"🏈 {league.settings.name} Standings",
                description=f"ESPN Fantasy Football — {os.getenv('ESPN_YEAR')}",
            )

            standings_text = ""

            for position, team in enumerate(league.standings(), start=1):
                standings_text += (
                    f"**{position}. {team.team_name}**\n"
                    f"{team.wins}-{team.losses}-{team.ties}\n\n"
                )

            embed.add_field(
                name="Standings",
                value=standings_text,
                inline=False,
            )

            await interaction.followup.send(embed=embed)

        except Exception as error:
            print(f"ESPN Error: {error}")

    async def team_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        league = get_league()

        teams = [
            team.team_name
            for team in league.teams
            if current.lower() in team.team_name.lower()
        ]

        return [
            app_commands.Choice(name=team_name, value=team_name)
            for team_name in teams[:25]
        ]
    
    @app_commands.command(
        name="roster",
        description="Show the roster for a fantasy team.",
    )
    @app_commands.describe(
        team="The fantasy team name."
    )
    @app_commands.autocomplete(team=team_autocomplete)
    async def roster(
        self,
        interaction: discord.Interaction,
        team: str,
    ):
        await interaction.response.defer()

        try:
            league = get_league()

            selected_team = None

            for fantasy_team in league.teams:
                if normalize_team_name(fantasy_team.team_name) == normalize_team_name(team):
                    selected_team = fantasy_team
                    break

            if selected_team is None:
                await interaction.followup.send(
                    f'Could not find a team named "{team}".',
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title=f"🏈 {selected_team.team_name}",
                description="Current ESPN Fantasy Football Roster",
            )

            roster_text = ""

            for player in selected_team.roster:
                roster_text += (
                    f"**{player.name}** — "
                    f"{player.position} | {player.proTeam}\n"
                )

            if not roster_text:
                roster_text = "No players are currently on this roster."

            embed.add_field(
                name="Roster",
                value=roster_text,
                inline=False,
            )

            await interaction.followup.send(embed=embed)

        except Exception as error:
            print(f"Roster Error: {error}")

            await interaction.followup.send(
                "Something went wrong while retrieving that roster.",
                ephemeral=True,
            )

            await interaction.followup.send(
                "Something went wrong while retrieving the ESPN standings.",
                ephemeral=True,
            )

    @app_commands.command(
        name="transactions",
        description="Show recent waiver, add/drop, and trade activity.",
    )
    async def transactions(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer()

        try:
            league = get_league()

            activities = league.recent_activity(size=10)

            if not activities:
                await interaction.followup.send(
                    "No recent league transactions were found."
                )
                return

            embed = discord.Embed(
                title="🔄 Recent League Transactions",
                description="Latest ESPN Fantasy Football activity",
            )

            for activity in activities:
                lines = []

                for action in activity.actions:
                    team, action_type, player = action

                    lines.append(
                        f"**{team.team_name}** — "
                        f"{action_type.title()} **{player}**"
                    )

                if lines:
                    embed.add_field(
                        name="Transaction",
                        value="\n".join(lines),
                        inline=False,
                    )

            await interaction.followup.send(embed=embed)

        except Exception as error:
            print(f"Transaction Error: {error}")

            await interaction.followup.send(
                "Something went wrong while retrieving league transactions.",
                ephemeral=True,
            )

    @app_commands.command(
        name="players-to-watch",
        description="Show starting players with injury concerns.",
    )
    async def players_to_watch(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer()

        try:
            league = get_league()

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
                    # Ignore players who aren't currently starting
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

            if not teams_with_players_to_watch:
                await interaction.followup.send(
                    "✅ No starting players currently have injury concerns."
                )
                return

            embed = discord.Embed(
                title="⚠️ Starting Players to Watch",
                description=(
                    "Starting players with injury or availability concerns."
                ),
            )

            for team, players in teams_with_players_to_watch:
                player_lines = []

                for player in players:
                    status = player.injuryStatus.replace("_", " ").title()

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

            await interaction.followup.send(embed=embed)

        except Exception as error:
            print(f"Players to Watch Error: {error}")

            await interaction.followup.send(
                "Something went wrong while retrieving players to watch.",
                ephemeral=True,
            )

#Commands go above this line
async def setup(bot):
    await bot.add_cog(LeagueCog(bot))