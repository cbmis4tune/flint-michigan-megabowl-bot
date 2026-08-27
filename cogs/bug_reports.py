import os

import discord
from discord import app_commands
from discord.ext import commands

from database.database import (
    create_bug_report,
    get_all_bug_reports,
    get_bug_report,
    get_bug_reports_by_status,
    save_bug_report_message,
    update_bug_report_status,
)


FEEDBACK_CHANNEL_ENV_VAR = "FEEDBACK_CHANNEL_ID"

ADMIN_ROLES = {
    "Commissioner",
    "Developer",
}


BUG_SEVERITY_DEFINITIONS = {
    "P1": "Critical — bot or major functionality is unusable.",
    "P2": "High — a major feature is broken, but the bot remains usable.",
    "P3": "Normal — limited impact or a workaround exists.",
    "P4": "Low — minor issue, visual problem, typo, or small defect.",
}


BUG_REPORT_STATUSES = {
    "OPEN": "🔴 OPEN",
    "INVESTIGATING": "🔎 INVESTIGATING",
    "IN_PROGRESS": "🔵 IN PROGRESS",
    "FIXED": "✅ FIXED",
    "CLOSED": "⚪ CLOSED",
    "WONT_FIX": "❌ WON'T FIX",
}


class BugReportModal(discord.ui.Modal):
    def __init__(
        self,
        bug_report_cog,
    ):
        super().__init__(
            title="Submit Bug Report",
            timeout=300,
        )

        self.bug_report_cog = bug_report_cog

        self.subject = discord.ui.TextInput(
            label="Subject",
            placeholder="Short summary of the problem",
            required=True,
            max_length=100,
        )

        self.command = discord.ui.TextInput(
            label="Command",
            placeholder="Example: /roster (optional)",
            required=False,
            max_length=100,
        )

        self.description = discord.ui.TextInput(
            label="Description",
            style=discord.TextStyle.paragraph,
            placeholder=(
                "Describe what happened, what you expected "
                "to happen, and anything that may help "
                "reproduce the issue."
            ),
            required=True,
            max_length=1500,
        )

        self.priority = discord.ui.TextInput(
            label="Severity",
            placeholder=(
                "P1 Critical | P2 High | "
                "P3 Normal | P4 Low"
            ),
            required=True,
            max_length=2,
        )

        self.add_item(self.subject)
        self.add_item(self.command)
        self.add_item(self.description)
        self.add_item(self.priority)

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer(
            ephemeral=True
        )

        try:
            priority = (
                self.priority.value
                .upper()
                .strip()
            )

            if priority not in BUG_SEVERITY_DEFINITIONS:
                await interaction.followup.send(
                    (
                        "❌ Invalid severity.\n\n"
                        "**P1** — Critical\n"
                        "**P2** — High\n"
                        "**P3** — Normal\n"
                        "**P4** — Low\n\n"
                        "Please run `/bug-report` again "
                        "and enter one of those values."
                    ),
                    ephemeral=True,
                )
                return

            feedback_channel = (
                await self.bug_report_cog
                .get_feedback_channel()
            )

            if (
                interaction.channel_id
                != feedback_channel.id
            ):
                await interaction.followup.send(
                    (
                        "❌ Bug reports can only "
                        f"be submitted in "
                        f"{feedback_channel.mention}."
                    ),
                    ephemeral=True,
                )
                return

            command_value = (
                self.command.value.strip()
                if self.command.value
                else None
            )

            report = create_bug_report(
                discord_user_id=(
                    interaction.user.id
                ),
                discord_username=(
                    str(interaction.user)
                ),
                subject=(
                    self.subject.value
                ),
                description=(
                    self.description.value
                ),
                priority=(
                    priority
                ),
                command=(
                    command_value
                ),
            )

            embed = (
                self.bug_report_cog
                .build_bug_report_embed(
                    report,
                    reporter_mention=(
                        interaction.user.mention
                    ),
                )
            )

            message = (
                await feedback_channel.send(
                    embed=embed
                )
            )

            save_bug_report_message(
                bug_report_id=(
                    report["id"]
                ),
                discord_channel_id=(
                    message.channel.id
                ),
                discord_message_id=(
                    message.id
                ),
            )

            await interaction.followup.send(
                (
                    "✅ Bug Report "
                    f"**#{report['id']}** "
                    "was submitted successfully."
                ),
                ephemeral=True,
            )

        except Exception as error:
            print(
                (
                    "Bug Report Submit Error: "
                    f"{error}"
                )
            )

            await interaction.followup.send(
                (
                    "Something went wrong while "
                    "submitting the bug report."
                ),
                ephemeral=True,
            )


class BugReportCog(commands.Cog):
    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    def has_feedback_admin_role(
        self,
        interaction: discord.Interaction,
    ):
        if not isinstance(
            interaction.user,
            discord.Member,
        ):
            return False

        user_roles = {
            role.name
            for role in interaction.user.roles
        }

        return bool(
            ADMIN_ROLES
            & user_roles
        )

    async def get_feedback_channel(
        self,
    ):
        channel_id = os.getenv(
            FEEDBACK_CHANNEL_ENV_VAR
        )

        if not channel_id:
            raise ValueError(
                (
                    f"{FEEDBACK_CHANNEL_ENV_VAR} "
                    "is missing from .env"
                )
            )

        try:
            channel_id = int(channel_id)

        except ValueError:
            raise ValueError(
                (
                    f"{FEEDBACK_CHANNEL_ENV_VAR} "
                    "must be a valid Discord "
                    "channel ID."
                )
            )

        channel = self.bot.get_channel(
            channel_id
        )

        if channel is None:
            channel = (
                await self.bot.fetch_channel(
                    channel_id
                )
            )

        return channel

    def build_bug_report_embed(
        self,
        report,
        reporter_mention=None,
    ):
        priority = report[
            "priority"
        ]

        status = report[
            "status"
        ]

        embed = discord.Embed(
            title=(
                f"🐛 Bug Report "
                f"#{report['id']}"
            ),
        )

        embed.add_field(
            name="Subject",
            value=(
                report[
                    "subject"
                ]
            ),
            inline=False,
        )

        embed.add_field(
            name="Severity",
            value=(
                f"**{priority}**\n"
                f"{BUG_SEVERITY_DEFINITIONS.get(priority, '')}"
            ),
            inline=False,
        )

        command_value = (
            report["command"]
            if report["command"]
            else "Not specified"
        )

        embed.add_field(
            name="Command",
            value=(
                command_value
            ),
            inline=False,
        )

        embed.add_field(
            name="Description",
            value=(
                report[
                    "description"
                ]
            ),
            inline=False,
        )

        embed.add_field(
            name="Status",
            value=(
                BUG_REPORT_STATUSES.get(
                    status,
                    status,
                )
            ),
            inline=True,
        )

        if reporter_mention is None:
            reporter_mention = (
                f"<@{report['discord_user_id']}>"
            )

        embed.add_field(
            name="Reported By",
            value=(
                reporter_mention
            ),
            inline=True,
        )

        if report[
            "updated_at"
        ]:
            embed.add_field(
                name="Last Updated",
                value=(
                    str(
                        report[
                            "updated_at"
                        ]
                    )
                ),
                inline=False,
            )

        embed.set_footer(
            text=(
                "Flint Michigan Megabowl "
                "Bug Report"
            )
        )

        return embed

    async def refresh_bug_report_message(
        self,
        report,
    ):
        channel_id = report[
            "discord_channel_id"
        ]

        message_id = report[
            "discord_message_id"
        ]

        if (
            not channel_id
            or not message_id
        ):
            return False

        try:
            channel = self.bot.get_channel(
                channel_id
            )

            if channel is None:
                channel = (
                    await self.bot.fetch_channel(
                        channel_id
                    )
                )

            message = (
                await channel.fetch_message(
                    message_id
                )
            )

            embed = (
                self.build_bug_report_embed(
                    report
                )
            )

            await message.edit(
                embed=embed
            )

            return True

        except discord.NotFound:
            print(
                (
                    "Bug report public message "
                    f"#{report['id']} no longer exists."
                )
            )

            return False

        except Exception as error:
            print(
                (
                    "Bug Report Message Refresh Error: "
                    f"{error}"
                )
            )

            return False

    @app_commands.command(
        name="bug-report",
        description=(
            "Submit a bug report "
            "for the Megabowl bot."
        ),
    )
    async def bug_report(
        self,
        interaction: discord.Interaction,
    ):
        try:
            feedback_channel = (
                await self.get_feedback_channel()
            )

            if (
                interaction.channel_id
                != feedback_channel.id
            ):
                await interaction.response.send_message(
                    (
                        "❌ `/bug-report` can only "
                        f"be used in "
                        f"{feedback_channel.mention}."
                    ),
                    ephemeral=True,
                )
                return

            modal = BugReportModal(
                bug_report_cog=self,
            )

            await interaction.response.send_modal(
                modal
            )

        except Exception as error:
            print(
                (
                    "Bug Report Command Error: "
                    f"{error}"
                )
            )

            if (
                interaction.response
                .is_done()
            ):
                await interaction.followup.send(
                    (
                        "Something went wrong while "
                        "opening the bug report form."
                    ),
                    ephemeral=True,
                )

            else:
                await interaction.response.send_message(
                    (
                        "Something went wrong while "
                        "opening the bug report form."
                    ),
                    ephemeral=True,
                )

    @app_commands.command(
        name="bug-reports",
        description=(
            "Admin: list bug reports."
        ),
    )
    @app_commands.describe(
        status=(
            "Optional status filter."
        )
    )
    @app_commands.choices(
        status=[
            app_commands.Choice(
                name="Open",
                value="OPEN",
            ),
            app_commands.Choice(
                name="Investigating",
                value="INVESTIGATING",
            ),
            app_commands.Choice(
                name="In Progress",
                value="IN_PROGRESS",
            ),
            app_commands.Choice(
                name="Fixed",
                value="FIXED",
            ),
            app_commands.Choice(
                name="Closed",
                value="CLOSED",
            ),
            app_commands.Choice(
                name="Won't Fix",
                value="WONT_FIX",
            ),
        ]
    )
    async def bug_reports(
        self,
        interaction: discord.Interaction,
        status: (
            app_commands.Choice[str]
            | None
        ) = None,
    ):
        await interaction.response.defer(
            ephemeral=True
        )

        try:
            if not self.has_feedback_admin_role(
                interaction
            ):
                await interaction.followup.send(
                    (
                        "❌ Only members with the "
                        "**Commissioner** or "
                        "**Developer** role can "
                        "view bug reports."
                    ),
                    ephemeral=True,
                )
                return

            if status is None:
                reports = (
                    get_all_bug_reports()
                )

                title = "🐛 Bug Reports"

            else:
                reports = (
                    get_bug_reports_by_status(
                        status.value
                    )
                )

                title = (
                    "🐛 Bug Reports — "
                    f"{status.name}"
                )

            if not reports:
                await interaction.followup.send(
                    (
                        "No matching bug reports "
                        "were found."
                    ),
                    ephemeral=True,
                )
                return

            embed = discord.Embed(
                title=title,
            )

            lines = []

            for report in reports[:25]:
                command_text = (
                    f" • {report['command']}"
                    if report["command"]
                    else ""
                )

                lines.append(
                    (
                        f"**#{report['id']}** "
                        f"[{report['priority']}] "
                        f"{report['subject']}"
                        f"{command_text}\n"
                        f"↳ "
                        f"{BUG_REPORT_STATUSES.get(report['status'], report['status'])}"
                    )
                )

            embed.description = (
                "\n\n".join(
                    lines
                )
            )

            if len(reports) > 25:
                embed.set_footer(
                    text=(
                        f"Showing 25 of "
                        f"{len(reports)} reports."
                    )
                )

            await interaction.followup.send(
                embed=embed,
                ephemeral=True,
            )

        except Exception as error:
            print(
                (
                    "Bug Reports List Error: "
                    f"{error}"
                )
            )

            await interaction.followup.send(
                (
                    "Something went wrong while "
                    "retrieving bug reports."
                ),
                ephemeral=True,
            )

    @app_commands.command(
        name="bug-report-view",
        description=(
            "Admin: view a bug report."
        ),
    )
    @app_commands.describe(
        report_id=(
            "Bug report number."
        )
    )
    async def bug_report_view(
        self,
        interaction: discord.Interaction,
        report_id: app_commands.Range[
            int,
            1,
            1000000,
        ],
    ):
        await interaction.response.defer(
            ephemeral=True
        )

        try:
            if not self.has_feedback_admin_role(
                interaction
            ):
                await interaction.followup.send(
                    (
                        "❌ Only members with the "
                        "**Commissioner** or "
                        "**Developer** role can "
                        "view bug report details."
                    ),
                    ephemeral=True,
                )
                return

            report = (
                get_bug_report(
                    report_id
                )
            )

            if report is None:
                await interaction.followup.send(
                    (
                        f"❌ Bug Report "
                        f"**#{report_id}** "
                        "does not exist."
                    ),
                    ephemeral=True,
                )
                return

            embed = (
                self.build_bug_report_embed(
                    report
                )
            )

            embed.add_field(
                name="Discord User ID",
                value=str(
                    report[
                        "discord_user_id"
                    ]
                ),
                inline=False,
            )

            embed.add_field(
                name="Created At",
                value=str(
                    report[
                        "created_at"
                    ]
                ),
                inline=False,
            )

            await interaction.followup.send(
                embed=embed,
                ephemeral=True,
            )

        except Exception as error:
            print(
                (
                    "Bug Report View Error: "
                    f"{error}"
                )
            )

            await interaction.followup.send(
                (
                    "Something went wrong while "
                    "retrieving that bug report."
                ),
                ephemeral=True,
            )

    @app_commands.command(
        name="bug-report-status",
        description=(
            "Admin: change a bug report status."
        ),
    )
    @app_commands.describe(
        report_id=(
            "Bug report number."
        ),
        status=(
            "New bug report status."
        ),
    )
    @app_commands.choices(
        status=[
            app_commands.Choice(
                name="Open",
                value="OPEN",
            ),
            app_commands.Choice(
                name="Investigating",
                value="INVESTIGATING",
            ),
            app_commands.Choice(
                name="In Progress",
                value="IN_PROGRESS",
            ),
            app_commands.Choice(
                name="Fixed",
                value="FIXED",
            ),
            app_commands.Choice(
                name="Closed",
                value="CLOSED",
            ),
            app_commands.Choice(
                name="Won't Fix",
                value="WONT_FIX",
            ),
        ]
    )
    async def bug_report_status(
        self,
        interaction: discord.Interaction,
        report_id: app_commands.Range[
            int,
            1,
            1000000,
        ],
        status: app_commands.Choice[str],
    ):
        await interaction.response.defer(
            ephemeral=True
        )

        try:
            if not self.has_feedback_admin_role(
                interaction
            ):
                await interaction.followup.send(
                    (
                        "❌ Only members with the "
                        "**Commissioner** or "
                        "**Developer** role can "
                        "change bug report statuses."
                    ),
                    ephemeral=True,
                )
                return

            report = (
                update_bug_report_status(
                    bug_report_id=(
                        report_id
                    ),
                    status=(
                        status.value
                    ),
                )
            )

            public_message_updated = (
                await self.refresh_bug_report_message(
                    report
                )
            )

            message_status = (
                "The public bug report post was updated."
                if public_message_updated
                else (
                    "The database was updated, but "
                    "the original public post could "
                    "not be updated."
                )
            )

            await interaction.followup.send(
                (
                    f"✅ Bug Report "
                    f"**#{report_id}** is now "
                    f"**{status.name}**.\n\n"
                    f"{message_status}"
                ),
                ephemeral=True,
            )

        except ValueError as error:
            await interaction.followup.send(
                f"❌ {error}",
                ephemeral=True,
            )

        except Exception as error:
            print(
                (
                    "Bug Report Status Error: "
                    f"{error}"
                )
            )

            await interaction.followup.send(
                (
                    "Something went wrong while "
                    "updating that bug report."
                ),
                ephemeral=True,
            )


async def setup(
    bot,
):
    await bot.add_cog(
        BugReportCog(
            bot
        )
    )