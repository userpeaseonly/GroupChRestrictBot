from telegram import Update, Bot, ChatMember
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
import dotenv
import os

# Load environment variables
dotenv.load_dotenv()

# Replace with your Bot Token, Group ID, and Channel Link
BOT_TOKEN = os.getenv("BOT_TOKEN") # Bot Token
GROUP_ID = os.getenv("GROUP_ID") # Group ID where the bot is added
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # Channel username without 't.me/'

print(f"Bot Token = {BOT_TOKEN}")
print(f"Group ID = {GROUP_ID}")
print(f"Channel Username = {CHANNEL_USERNAME}")

bot = Bot(BOT_TOKEN)

# Dictionary to track active users
active_users = {}

async def check_subscription(user_id: int) -> bool:
    """
    Check if a user is subscribed to the channel.
    """
    try:
        member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        # Handle error or assume the user is not subscribed
        print(f"Error checking subscription for user {user_id}: {e}")
        return False

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle new members joining the group.
    """
    for member in update.message.new_chat_members:
        user_id = member.id
        user_name = member.full_name
        active_users[user_id] = member  # Track the user
        print(f"New user joined: {user_name} ({user_id})")

        # Check subscription status
        is_subscribed = await check_subscription(user_id)
        if not is_subscribed:
            # Temporarily kick user
            await context.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            await context.bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
            await update.message.reply_text(
                f"Sorry {user_name}, you must subscribe to @{CHANNEL_USERNAME} before joining the group."
            )
        else:
            await update.message.reply_text(f"Welcome to the group, {user_name}!")

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Track users who send messages to the group.
    """
    user_id = update.effective_user.id
    active_users[user_id] = update.effective_user  # Track the user

async def kick_unsubscribed_users(context: ContextTypes.DEFAULT_TYPE):
    """
    Periodically check if active users are still subscribed and kick those who are not.
    """
    print("Checking subscription status of active users...[start]")
    for user_id, user in list(active_users.items()):
        is_subscribed = await check_subscription(user_id)
        if not is_subscribed:
            try:
                # Temporarily kick user
                await bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                await bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                print(f"Kicked {user.full_name} ({user_id}) for unsubscribing from @{CHANNEL_USERNAME}.")
                del active_users[user_id]  # Remove user from tracking
            except Exception as e:
                print(f"Error kicking user {user_id}: {e}")
    print("Checking subscription status of active users...[stop]")

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start command to verify the bot is running.
    """
    await update.message.reply_text("Bot is up and running!")

def main():
    # Set up the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_member))
    application.add_handler(MessageHandler(filters.TEXT, handle_user_message))
    application.add_handler(CommandHandler("start", handle_start))

    # Schedule the periodic job to check unsubscribed users
    async def job_callback(context):
        await kick_unsubscribed_users(context)

    application.job_queue.run_repeating(job_callback, interval=3600, first=10)  # Check every 60 seconds

    # Run the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
