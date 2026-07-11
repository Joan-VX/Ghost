import discord
from discord.ext import commands
from discord import app_commands
import asyncio

# ==========================================
# CONFIGURATION
# ==========================================
TOKEN = "YOUR_BOT_TOKEN_HERE"
LOG_CHANNEL_ID = 987654321098765432  # Private channel where staff reviews apps


class ApplicationLauncher(discord.ui.View):
    """
    The permanent button in the server channel. 
    When clicked, it starts the DM application process.
    """
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Apply for Staff", style=discord.ButtonStyle.green, custom_id="persistent_dm_apply_btn")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        
        # 1. Let the user know we are DMing them
        await interaction.response.send_message(
            "📬 Check your Direct Messages! I've sent you the application questions.", 
            ephemeral=True
        )

        # 2. Try to slide into their DMs
        try:
            dm_channel = await user.create_dm()
        except discord.Forbidden:
            # Triggers if the user has "Allow direct messages from server members" turned off
            return await interaction.followup.send(
                "❌ I couldn't send you a DM. Please check your Discord Privacy Settings and ensure 'Allow direct messages from server members' is turned ON.",
                ephemeral=True
            )

        # 3. Offload the question loop so it doesn't freeze the interaction
        self.bot.loop.create_task(self.run_dm_application(user, dm_channel, interaction.guild))

    async def run_dm_application(self, user: discord.User, dm: discord.DMChannel, guild: discord.Guild):
        """
        The multi-step text question system handled purely inside the user's DMs.
        """
        def check(m):
            # Make sure the bot only listens to messages from this specific user inside their DMs
            return m.author.id == user.id and m.channel.id == dm.id

        questions = [
            ("🕒 Question 1 of 4", "What is your **Age** and **Timezone**? (e.g., 21, EST)"),
            ("🛠️ Question 2 of 4", "Do you have any **prior moderation experience**? If yes, please list it. If no, just type 'None'."),
            ("📚 Question 3 of 4 (Scenario)", "Two members are violently arguing in general chat. Neither is breaking hard rules yet, but it's tense. **What do you do?**"),
            ("📚 Question 4 of 4 (Scenario)", "You notice a fellow staff member abusing their powers (e.g. banning innocent people). **How do you handle this?**")
        ]

        answers = []

        await dm.send(f"👋 Welcome to the **{guild.name}** Staff Application! Let's get started. You have 5 minutes per question.")

        for title, question in questions:
            embed = discord.Embed(title=title, description=question, color=discord.Color.blue())
            await dm.send(embed=embed)

            try:
                # Wait up to 5 minutes (300 seconds) for a text response
                msg = await self.bot.wait_for("message", check=check, timeout=300.0)
                answers.append(msg.content)
            except asyncio.TimeoutError:
                await dm.send("⏱️ **Application Timed Out.** You took too long to respond. Please click the button in the server to try again.")
                return

        # 4. Process and Send the Results to the Server
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            await dm.send("❌ Something went wrong on our end. Please notify a Server Administrator that the log channel configuration is broken.")
            print(f"[ERROR] LOG_CHANNEL_ID {LOG_CHANNEL_ID} not found in guild '{guild.name}'.")
            return

        # Compile answers into a clean Admin review panel
        review_embed = discord.Embed(
            title="📥 New Staff Application (via DM)",
            color=discord.Color.teal()
        )
        review_embed.set_author(name=f"{user} ({user.id})", icon_url=user.display_avatar.url)
        
        review_embed.add_field(name="👤 Applicant", value=user.mention, inline=True)
        review_embed.add_field(name="🕒 Age & Timezone", value=answers[0], inline=True)
        review_embed.add_field(name="🛠️ Experience", value=answers[1], inline=False)
        review_embed.add_field(name="📚 Chat Argument Scenario", value=answers[2], inline=False)
        review_embed.add_field(name="📚 Staff Abuse Scenario", value=answers[3], inline=False)

        await log_channel.send(embed=review_embed)
        
        # Final confirmation to user
        final_embed = discord.Embed(
            title="✅ Application Submitted!",
            description="Thank you for applying! Your answers have been safely sent to the management team for review.",
            color=discord.Color.green()
        )
        await dm.send(embed=final_embed)


class ApplicationBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read text messages back from DMs
        super().__init__(command_prefix="-", intents=intents)

    async def setup_hook(self):
        # Keeps our button listener persistent when the bot restarts
        self.add_view(ApplicationLauncher(self))


bot = ApplicationBot()


@bot.event
async def on_ready():
    print(f"🎯 Bot logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.tree.command(name="setup_app", description="Spawn the persistent 'Apply for Staff' UI panel.")
@app_commands.checks.has_permissions(administrator=True)
async def setup_app(interaction: discord.Interaction):
    """
    Run this once in your public recruitment channel.
    """
    embed = discord.Embed(
        title="🛡️ Moderation Staff Applications",
        description=(
            "Want to help look after our community? We're hiring!\n\n"
            "**How it works:**\n"
            "Click the green button below, and our bot will reach out to you directly in your **DMs** to interview you safely and privately."
        ),
        color=discord.Color.purple()
    )
    
    await interaction.channel.send(embed=embed, view=ApplicationLauncher(bot))
    await interaction.response.send_message("✅ Application panel spawned!", ephemeral=True)


if __name__ == "__main__":
    bot.run(TOKEN)
