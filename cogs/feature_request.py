import os

import discord
from discord import app_commands
from discord.ext import commands

from database.database import (
    create_feature_request,
)


# =============================================================
# PRIORITY DEFINITIONS
# =============================================================

PRIORITY_DEFINITIONS = {
    "P1": "Critical — major functionality is broken or blocked.",
    "P2": "High — important improvement with significant impact.",
    "P3": "Normal — useful improvement or enhancement.",
    "P4": "Low — nice-to-have or minor quality-of-life improvement.",
}


# =============================================================
# FEATURE REQUEST MODAL
# =============================================================

class FeatureRequestModal(
    discord.ui.Modal
):
    def __init__(
        self,
        feature_request_cog,
    ):
        super().__init__(
            title="Submit Feature Request",
            timeout=300,
        )

        self.feature_request_cog = (
            feature_request_cog
        )

        self.subject = (
            discord.ui.TextInput(
                label="Subject",
                placeholder=(
                    "Short summary of the request"
                ),
                required=True,
                max_length=100,
            )
        )

        self.description = (
            discord.ui.TextInput(
                label="Description",
                style=discord.TextStyle.paragraph,
                placeholder=(
                    "Describe what you would like "
                    "the bot to do and why it would "
                    "be useful."
                ),
                required=True,
                max_length=1500,
            )
        )

        self.priority = (
            discord.ui.TextInput(
                label="Priority",
                placeholder=(
                    "P1 Critical | P2 High | "
                    "P3 Normal | P4 Nice-to-have"
                ),
                required=True,
                max_length=2,
            )
        )

        self.add_item(
            self.subject
        )

        self.add_item(
            self.description
        )

        self.add_item(
            self.priority
        )

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

            if (
                priority
                not in PRIORITY_DEFINITIONS
            ):
                await interaction.followup.send(
                    (
                        "❌ Invalid priority.\n\n"
                        "**P1** — Critical / blocking\n"
                        "**P2** — High impact\n"
                        "**P3** — Normal priority\n"
                        "**P4** — Nice-to-have\n\n"
                        "Please run `/feature-request` "
                        "again and enter one of those "
                        "priority values."
                    ),
                    ephemeral=True,
                )
                return

            # -------------------------------------------------
            # VERIFY CHANNEL AGAIN
            #
            # We check this both when the command is run
            # and when the modal is submitted.
            # -------------------------------------------------

            feature_channel = (
                await self.feature_request_cog
                .get_feature_request_channel()
            )

            if (
                interaction.channel_id
                != feature_channel.id
            ):
                await interaction.followup.send(
                    (
                        "❌ Feature requests can only "
                        f"be submitted in "
                        f"{feature_channel.mention}."
                    ),
                    ephemeral=True,
                )
                return

            # -------------------------------------------------
            # SAVE REQUEST
            # -------------------------------------------------

            request = (
                create_feature_request(
                    discord_user_id=(
                        interaction.user.id
                    ),
                    discord_username=(
                        str(
                            interaction.user
                        )
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
                )
            )

            # -------------------------------------------------
            # BUILD PUBLIC REQUEST POST
            # -------------------------------------------------

            embed = discord.Embed(
                title=(
                    f"💡 Feature Request "
                    f"#{request['id']}"
                ),
            )

            embed.add_field(
                name="Subject",
                value=(
                    request[
                        "subject"
                    ]
                ),
                inline=False,
            )

            embed.add_field(
                name="Priority",
                value=(
                    f"**{request['priority']}**\n"
                    f"{PRIORITY_DEFINITIONS[priority]}"
                ),
                inline=False,
            )

            embed.add_field(
                name="Description",
                value=(
                    request[
                        "description"
                    ]
                ),
                inline=False,
            )

            embed.add_field(
                name="Status",
                value=(
                    "🟢 OPEN"
                ),
                inline=True,
            )

            embed.add_field(
                name="Submitted By",
                value=(
                    interaction.user.mention
                ),
                inline=True,
            )

            embed.set_footer(
                text=(
                    "Flint Michigan Megabowl "
                    "Feature Request"
                )
            )

            await feature_channel.send(
                embed=embed
            )

            await interaction.followup.send(
                (
                    "✅ Feature Request "
                    f"**#{request['id']}** "
                    "was submitted successfully."
                ),
                ephemeral=True,
            )

        except Exception as error:
            print(
                (
                    "Feature Request Submit Error: "
                    f"{error}"
                )
            )

            await interaction.followup.send(
                (
                    "Something went wrong while "
                    "submitting the feature request."
                ),
                ephemeral=True,
            )


# =============================================================
# FEATURE REQUEST COG
# =============================================================

class FeatureRequestCog(
    commands.Cog
):
    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    # =========================================================
    # FEATURE REQUEST CHANNEL
    # =========================================================

    async def get_feature_request_channel(
        self,
    ):
        channel_id = os.getenv(
            "FEATURE_REQUEST_CHANNEL_ID"
        )

        if not channel_id:
            raise ValueError(
                (
                    "FEATURE_REQUEST_CHANNEL_ID "
                    "is missing from .env"
                )
            )

        try:
            channel_id = int(
                channel_id
            )

        except ValueError:
            raise ValueError(
                (
                    "FEATURE_REQUEST_CHANNEL_ID "
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

    # =========================================================
    # FEATURE REQUEST COMMAND
    # =========================================================

    @app_commands.command(
        name="feature-request",
        description=(
            "Submit a feature request "
            "for the Megabowl bot."
        ),
    )
    async def feature_request(
        self,
        interaction: discord.Interaction,
    ):
        try:
            feature_channel = (
                await self.get_feature_request_channel()
            )

            if (
                interaction.channel_id
                != feature_channel.id
            ):
                await interaction.response.send_message(
                    (
                        "❌ `/feature-request` can only "
                        f"be used in "
                        f"{feature_channel.mention}."
                    ),
                    ephemeral=True,
                )
                return

            modal = (
                FeatureRequestModal(
                    feature_request_cog=self,
                )
            )

            await interaction.response.send_modal(
                modal
            )

        except Exception as error:
            print(
                (
                    "Feature Request Command Error: "
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
                        "opening the feature request form."
                    ),
                    ephemeral=True,
                )

            else:
                await interaction.response.send_message(
                    (
                        "Something went wrong while "
                        "opening the feature request form."
                    ),
                    ephemeral=True,
                )


# =============================================================
# COG SETUP
# =============================================================

async def setup(
    bot,
):
    await bot.add_cog(
        FeatureRequestCog(
            bot
        )
    )