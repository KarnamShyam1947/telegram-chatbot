import logging
import uuid
import os
from datetime import datetime
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from DBUtils import create_user, read_user_by_case_number

# ──────────────────────── Config ────────────────────────

TOKEN = os.getenv("BOT_TOKEN")
ASK_COMPLAINT, ASK_PHONE_NUMBER, ASK_ADDRESS, ASK_POLICE_ZONE, ASK_POLICE_STATION, ASK_CASE_NUMBER, ASK_CRIME_TYPE, ASK_CRIME_SUBTYPE, ASK_EVIDENCE = range(9)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Police stations grouped by zone
police_stations = {
    "West Zone": ["I Town Police Station", "II Town Police Station", "Suryaraopet Police Station", "Governorpet Police Station",
                  "Satyanarayanapuram Police Station", "Krishnalanka Police Station", "Machavaram Police Station",
                  "Patamata Police Station", "Nunna Police Station", "Ibrahimpatnam Police Station"],
    "East Zone": ["Thotlavalluru Police Station", "Unguturu Police Station", "Gannavaram Police Station",
                  "Pamidimukkala Police Station", "Penamaluru Police Station", "Vuyyuru Rural Police Station",
                  "Vuyyuru Town Police Station"],
    "Central Zone": ["Satyanarayanapuram Police Station", "Krishnalanka Police Station", "Machavaram Police Station",
                     "Patamata Police Station", "Penamaluru Police Station", "Vuyyuru Rural Police Station",
                     "Vuyyuru Town Police Station"],
    "Other/Don't Know": ["Women Police Station", "I Traffic Police Station", "II Traffic Police Station"]
}

# Crime types and subtypes
crimes = {
    "Crimes Against Persons (Violent Crimes)": ["Murder", "Rape", "Robbery", "Assault", "Kidnapping and Abduction",
                                                "Crimes against women", "Crimes against children", "Crimes against senior citizens"],
    "Crimes Against Property": ["Theft", "Burglary", "Arson", "Motor Vehicle Theft", "Dacoity",
                                "Offences relating to documents and properties"],
    "Other Offenses": ["Cybercrime", "Organized Crime", "Economic Offences", "White-Collar Crimes", "Drug Trafficking",
                       "Money Laundering", "Bribery", "Fraud", "Extortion", "Domestic Violence", "Inchoate Crimes", "Statutory Crimes"],
    "Other/Don't Know": ["UnKnown"]
}

# ──────────────────────── Utility: Fake Cloud Upload ────────────────────────

async def upload_to_cloud(file_path: str) -> str:
    filename = os.path.basename(file_path)
    return f"https://fake-cloud.com/uploads/{filename}"

# ──────────────────────── Telegram Bot Logic ────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Lodge a Complaint", callback_data="new_crime")],
        [InlineKeyboardButton("🚨 Report a Crime", callback_data="new_crime")],
        [InlineKeyboardButton("🔎 Check Case Status", callback_data="get_details")],
        [InlineKeyboardButton("🏢 Know Your Police Stations", callback_data="police_stations")],
        [InlineKeyboardButton("🆘 Emergency Assistance", callback_data="emergency")]
    ]
    await update.message.reply_text("Welcome to the Complaints Reporting Bot.\nChoose an option:", reply_markup=InlineKeyboardMarkup(keyboard))


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "new_crime":
        crime_buttons = [[InlineKeyboardButton(k, callback_data=k)] for k in crimes]
        await query.message.reply_text("Select the crime type:", reply_markup=InlineKeyboardMarkup(crime_buttons))
        return ASK_CRIME_TYPE
    elif query.data == "get_details":
        await query.message.reply_text("Enter the case number:")
        return ASK_CASE_NUMBER

async def service_under_development(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🚧 This service is under development. Please check back later.")
    return ConversationHandler.END

async def crime_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    crime_type = update.callback_query.data
    context.user_data['crime_type'] = crime_type
    subtype_buttons = [[InlineKeyboardButton(st, callback_data=st)] for st in crimes[crime_type]]
    await update.callback_query.message.edit_text(f"You selected: *{crime_type}*", parse_mode='Markdown')
    await update.callback_query.message.reply_text("Select the crime subtype:", reply_markup=InlineKeyboardMarkup(subtype_buttons))
    return ASK_CRIME_SUBTYPE

async def crime_subtype_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    crime_subtype = update.callback_query.data
    context.user_data['crime_subtype'] = crime_subtype
    await update.callback_query.message.edit_text(f"Subtype: *{crime_subtype}*", parse_mode='Markdown')
    await update.callback_query.message.reply_text("Please describe the crime:")
    return ASK_COMPLAINT

async def receive_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['complaint'] = update.message.text
    await update.message.reply_text("Provide your phone number:")
    return ASK_PHONE_NUMBER

async def receive_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone_number'] = update.message.text
    await update.message.reply_text("Enter the incident address:")
    return ASK_ADDRESS

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    zone_buttons = [[InlineKeyboardButton(z, callback_data=z)] for z in police_stations]
    await update.message.reply_text("Select your zone:", reply_markup=InlineKeyboardMarkup(zone_buttons))
    return ASK_POLICE_ZONE

async def police_zone_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    zone = update.callback_query.data
    context.user_data['zone'] = zone
    stations = police_stations[zone]
    station_buttons = [[InlineKeyboardButton(st, callback_data=st)] for st in stations]
    await update.callback_query.message.edit_text(f"Zone: *{zone}*", parse_mode='Markdown')
    await update.callback_query.message.reply_text("Select police station:", reply_markup=InlineKeyboardMarkup(station_buttons))
    return ASK_POLICE_STATION

async def receive_police_station(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['police_station'] = update.callback_query.data
    context.user_data['case_number'] = str(uuid.uuid4())[:8]
    context.user_data['user'] = update.callback_query.from_user
    await update.callback_query.message.edit_text(f"Police Station: *{context.user_data['police_station']}*", parse_mode='Markdown')
    await update.callback_query.message.reply_text("📎 Upload evidence (photo/video), or type `skip`.")
    return ASK_EVIDENCE

async def receive_evidence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_url = "No Evidence Provided"

    if update.message.text and update.message.text.lower() == 'skip':
        pass
    else:
        file = update.message.photo[-1] if update.message.photo else update.message.video
        if file:
            tg_file = await file.get_file()
            ext = ".png" if update.message.photo else ".mp4"
            file_path = f"evidence_{tg_file.file_unique_id}{ext}"
            await tg_file.download_to_drive(custom_path=file_path)
            file_url = await upload_to_cloud(file_path)
            if os.path.exists(file_path):
                os.remove(file_path)

    user = context.user_data['user']
    create_user(
        case_number=context.user_data['case_number'],
        name=user.full_name,
        phone_number=context.user_data['phone_number'],
        complaint=context.user_data['complaint'],
        address=context.user_data['address'],
        crime_type=context.user_data['crime_type'],
        crime_subtype=context.user_data['crime_subtype'],
        zone=context.user_data['zone'],
        police_station=context.user_data['police_station'],
        evidence_url=file_url,
        chat_id=update.message.chat_id
    )

    await update.message.reply_text(
        f"✅ Case registered!\nYour Case Number is: *{context.user_data['case_number']}*",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def receive_case_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    case_number = update.message.text.strip()
    case = read_user_by_case_number(case_number)

    if not case:
        await update.message.reply_text("❌ *No case found with that number.*", parse_mode='Markdown')
        return ConversationHandler.END

    # Format evidence display
    evidence_text = "📎 No evidence was provided." if case.evidence_url == "No Evidence Provided" else f"📎 [View Evidence]({case.evidence_url})"

    await update.message.reply_text(
        f"📂 *Case Details:*\n\n"
        f"🔐 *Case Number:* `{case_number}`\n"
        f"👤 *Name:* {case.name}\n"
        f"📞 *Phone:* {case.phone_number}\n"
        f"📍 *Address:* {case.address}\n"
        f"🌐 *Zone:* {case.zone}\n"
        f"🏢 *Police Station:* {case.police_station}\n"
        f"⚖️ *Crime Type:* {case.crime_type.replace('_', '\\_')}\n"
        f"🔎 *Subtype:* {case.crime_subtype.replace('_', '\\_')}\n"
        f"📝 *Complaint:* {case.complaint.replace('_', '\\_')}\n"
        f"{evidence_text}\n"
        f"🕒 *Reported on:* {case.datetime.strftime('%d-%m-%Y %H:%M:%S')}\n"
        f"📊 *Status:* {case.status}",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

    return ConversationHandler.END

# ──────────────────────── Error Handler ────────────────────────

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("⚠️ An error occurred. Please try again.")

# ──────────────────────── Bot Launcher ────────────────────────

def start_bot():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^(new_crime|get_details)$"),
            CommandHandler("newcase", button_handler),
            CommandHandler("getdetails", button_handler),
        ],
        states={
            ASK_CRIME_TYPE: [CallbackQueryHandler(crime_type_selected)],
            ASK_CRIME_SUBTYPE: [CallbackQueryHandler(crime_subtype_selected)],
            ASK_COMPLAINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_complaint)],
            ASK_PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone_number)],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
            ASK_POLICE_ZONE: [CallbackQueryHandler(police_zone_selected)],
            ASK_POLICE_STATION: [CallbackQueryHandler(receive_police_station)],
            ASK_EVIDENCE: [MessageHandler(filters.PHOTO | filters.VIDEO | (filters.TEXT & ~filters.COMMAND), receive_evidence)],
            ASK_CASE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_case_number)],
        },
        fallbacks=[],
    )

    # Start and callback handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(service_under_development, pattern="^(police_stations|emergency)$"))
    app.add_error_handler(handle_error)

    logger.info("🚨 Bot started...")
    app.run_polling()


if __name__ == "__main__":
    start_bot()
