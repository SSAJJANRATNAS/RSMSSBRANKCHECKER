
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Bot credentials
TOKEN = "8011614651:AAHIclU4a27-NqRQUm4RD9c1C5z07u1GZGs"
CHANNEL_USERNAME = "@l1_factory_Academy"

# Database path (local)
DB_PATH = "students.db"

# Get student result from SQLite database
def get_student_info(roll_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT rank, category, gender, area FROM students WHERE roll_number = ?", (roll_number,))
    data = cursor.fetchone()
    if not data:
        return None

    rank, applied_category, gender, area = data
    selection_status = "Not Selected"
    selection_category = "-"
    category_rank = "-"

    selection_tables = [
        "tsp_selected_for_gen_category", "tsp_female_general_selection", "tsp_sc_general_selection",
        "tsp_female_sc_general_selection", "tsp_st_general_selection", "tsp_female_st_general_selection",
        "non_tsp_selected_for_gen_category", "non_tsp_female_general_selection", "non_tsp_sc_general_selection",
        "non_tsp_female_sc_general_selection", "non_tsp_st_general_selection", "non_tsp_female_st_general_selection",
        "non_tsp_obc_general_selection", "non_tsp_female_obc_general_selection", "non_tsp_mbc_general_selection",
        "non_tsp_female_mbc_general_selection", "non_tsp_ews_general_selection", "non_tsp_female_ews_general_selection"
    ]

    for table in selection_tables:
        cursor.execute(f"SELECT 1 FROM {table} WHERE roll_number = ? LIMIT 1", (roll_number,))
        if cursor.fetchone():
            selection_status = "Selected"
            selection_category = table.replace("non_tsp_", "").replace("tsp_", "").replace("_general_selection", "").replace("_selected_for_gen_category", "GEN").upper()
            break

    cursor.execute(
        "SELECT COUNT(*) FROM students WHERE category = ? AND rank <= ? AND area = ?",
        (applied_category, rank, area)
    )
    category_rank = cursor.fetchone()[0]
    conn.close()

    return {
        "roll_number": roll_number,
        "rank": rank,
        "applied_category": applied_category,
        "gender": gender,
        "area": area,
        "selection_status": selection_status,
        "selection_category": selection_category,
        "category_rank": category_rank
    }

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to RSMSSB Result Checker Bot.\n\nPlease send your Roll Number to check your result."
    )

# Handle incoming messages (roll numbers)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check if user has joined the channel
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "Access Denied. Please join our official channel first: https://t.me/l1_factory_Academy"
            )
            return
    except:
        await update.message.reply_text(
            "Could not verify your channel membership. Please join: https://t.me/l1_factory_Academy"
        )
        return

    roll_number = update.message.text.strip()
    if not roll_number.isdigit():
        await update.message.reply_text("Please send a valid numeric Roll Number.")
        return

    info = get_student_info(roll_number)
    if not info:
        await update.message.reply_text("Roll Number not found.")
        return

    response = f"""RSMSSB Result Details
----------------------------
Roll Number       : {info['roll_number']}
All India Rank    : {info['rank']}
Category Applied  : {info['applied_category']}
Gender            : {info['gender']}
Area              : {info['area']}
Category Rank     : {info['category_rank']}
Selection Status  : {info['selection_status']}
Selection Category: {info['selection_category']}

Channel: https://t.me/l1_factory_Academy
Bot: https://t.me/RSMSSBResultChecker_bot
"""
    await update.message.reply_text(response)

# Build the application
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == '__main__':
    print("Bot is running...")
    app.run_polling()
