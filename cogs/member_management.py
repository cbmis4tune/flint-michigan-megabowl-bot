import discord
from discord.ext import commands


class MemberManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================================================
    # MEMBER JOIN
    # =========================================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member,
    ):
        """
        New members intentionally receive no Owner role here.

        Access to the rest of the server is granted only after
        the member successfully claims their fantasy team with
        /claim-team.
        """

        print(
            (
                f"{member} joined "
                f"{member.guild.name}."
            )
        )


async def setup(bot):
    await bot.add_cog(
        MemberManagementCog(bot)
    )