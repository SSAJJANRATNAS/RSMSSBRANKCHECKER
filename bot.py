import sqlite3
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Bot credentials
TOKEN = "8011614651:AAHIclU4a27-NqRQUm4RD9c1C5z07u1GZGs"
CHANNEL_USERNAME = "@l1_factory_Academy"

# 📁 List of split database files
DB_FILES = [f"students_{i}.db" for i in range(1, 11)]  # students_1.db to students_10.db

# 🎓 Get student result from multiple databases
def get_student_info(roll_number):
    for db_file in DB_FILES:
        if not os.path.exists(db_file):
            continue

        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        try:
            # Main student record
            cursor.execute("SELECT rank, category, gender, area FROM students WHERE roll_number = ?", (roll_number,))
            data = cursor.fetchone()
            if not data:
                conn.close()
                continue  # Not found, try next DB

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

            # Category-wise rank
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

        except Exception as e:
            print(f"❌ Error in {db_file}: {e}")
            conn.close()
            continue

    return None  # Not found in any DB

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to RSMSSB Result Checker Bot.\n\nPlease send your *Roll Number* to check your result.",
        parse_mode="Markdown"
    )

# Handle roll number messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Verify channel membership
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "🚫 Access Denied. Please join our official channel first:\n👉 https://t.me/l1_factory_Academy"
            )
            return
    except:
        await update.message.reply_text(
            "⚠️ Could not verify your channel membership. Please join:\n👉 https://t.me/l1_factory_Academy"
        )
        return

    roll_number = update.message.text.strip()
    if not roll_number.isdigit():
        await update.message.reply_text("❗ Please send a valid numeric Roll Number.")
        return

    info = get_student_info(roll_number)
    if not info:
        await update.message.reply_text("❌ Roll Number not found.")
        return

    response = f"""🎓 *RSMSSB Result Details*
🆔 Roll Number       : `{info['roll_number']}`
🏅 All India Rank    : *{info['rank']}*
📂 Category Applied  : *{info['applied_category']}*
🧬 Gender            : *{info['gender']}*
🌍 Area              : *{info['area']}*
🎯 Category Rank     : *{info['category_rank']}*
🎖️ Selection Status  : *{info['selection_status']}*
🏷️ Selection Category: *{info['selection_category']}*

📢 Channel: [L1 Factory Academy](https://t.me/l1_factory_Academy)
🤖 Bot: [@RSMSSBResultChecker_bot](https://t.me/RSMSSBResultChecker_bot)
"""
    await update.message.reply_text(response, parse_mode="Markdown")

# Bot setup
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == '__main__':
    print("🤖 Bot is running...")
    app.run_polling()
