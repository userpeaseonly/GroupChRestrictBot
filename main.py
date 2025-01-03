from telegram import Update, Bot, ChatMember
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler,
)
from apscheduler.schedulers.background import BackgroundScheduler

# Replace with your Bot Token, Group ID, and Channel Link
BOT_TOKEN = "8039521493:AAEUqYjpWA0GXsJ5plcdKt1J8TM7tlFCa3w"
GROUP_ID = -1002492235392  # Replace with your group ID
CHANNEL_USERNAME = "testBasirat"  # Channel username without 't.me/'

# Create bot and scheduler
bot = Bot(BOT_TOKEN)
scheduler = BackgroundScheduler()

async def check_subscription(user_id: int) -> bool:
    """
    Check if a user is subscribed to the channel.
    """
    try:
        member = await bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle new members joining the group.
    """
    for member in update.message.new_chat_members:
        user_id = member.id
        user_name = member.full_name
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

async def kick_unsubscribed_users(context: ContextTypes.DEFAULT_TYPE):
    """
    Periodically check if group members are still subscribed and kick those who are not.
    """
    try:
        group_members = await bot.get_chat_administrators(chat_id=GROUP_ID)
        for member in group_members:
            user_id = member.user.id
            if not await check_subscription(user_id):
                # Temporarily kick user
                await bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                await bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                print(f"User {user_id} was unsubscribed and kicked from the group.")
    except Exception as e:
        print(f"Error in kicking unsubscribed users: {e}")

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
    application.add_handler(CommandHandler("start", handle_start))

    # Schedule the periodic job to check unsubscribed users
    scheduler.add_job(
        lambda: application.create_task(kick_unsubscribed_users(None)),
        trigger="interval",
        minutes=5,  # Adjust as needed
    )
    scheduler.start()

    # Run the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
