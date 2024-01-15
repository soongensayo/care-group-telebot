from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
from datetime import datetime, timedelta, time
import os
from os import load_dotenv

#load environment variables
load_dotenv()
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
sheet_name = os.getenv('SHEET_NAME')
password = os.getenv('PASSWORD')
path_to_json_key_file = os.getenv('GOOGLE_APP_JSON_KEY_FILE')

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(name_of_json_key_file, scope)
client = gspread.authorize(creds)

prayer_sheet = client.open(sheet_name).worksheet('prayer_requests')
thanksgiving_sheet = client.open(sheet_name).worksheet('thanksgiving')
reflections_sheet = client.open(sheet_name).worksheet('reflections')
membersSheet = client.open(sheet_name).worksheet('members')

#emojis
folded_hands = '\U0001F64F'
thought_balloon = '\U0001F4AD'
pleading_face = '\U0001F97A'
smiling_face_with_smiling_eyes = '\U0001F60A'
clinking_glasses = '\U0001F942'
night_with_stars = '\U0001F303'
sunrise = '\U0001F305'
raising_hands = '\U0001F64C'
calendar_emoji = '\U0001F4C5'
check_mark_emoji = '\u2705'
writing_hand = '\u270D'
burning_heart_emoji = '\u2764\uFE0F\u200D\U0001F525'

# define state for the conversation
PRAYER_REQUEST, THANKSGIVING, PASSWORD, REFLECTION, BIRTHDAY, NAME = range(6)


async def send_reminder(context):
    print(f"finding reminders")
    subscribers = membersSheet.get_all_records()  
    for subscriber in subscribers:
        if subscriber['Subscribed'] == 'TRUE':  
            chat_id = subscriber['UserID']  
            try:
                await context.bot.send_message(chat_id=chat_id, text="HI! This is a friendly reminder that it's tuesday night. Do try to submit your stuff for the week tonight/tomorrow night so everyone can see it.")
            except Exception as e:
                print(f"Failed to send reminder to {chat_id}: {e}")

async def weekly_reminder(context):
    while True:
        now = datetime.now()
        if now.weekday() == 2 and now.hour == 14 and 51 < now.minute < 59:  
            print(f"Sending reminders at {now}")
            await send_reminder(context)
            await asyncio.sleep(60 * 60) 
        else:
            await asyncio.sleep(30) 

async def blast_thanksgivings(context):
    now = datetime.now()
    days_until_thursday = (3 - now.weekday()) % 7 # 3 represents Thursday
    last_thursday = now - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0))  # set reset time to 12am
    if now.weekday() == 3 and now.time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)

    thanksgivings_after_last_thursday = []
    # start from the second row to skip the headers and fetch rows in batches
    current_row = 2
    batch_size = 50  # adjust batch size as appropriate for your data
    while True:
        rows = thanksgiving_sheet.get(f"A{current_row}:C{current_row + batch_size - 1}")
        if not rows:
            break
        # process each row
        for row in rows:
            # check if date is after last Thursday at 12am
            request_date = datetime.strptime(row[0], '%Y-%m-%d')
            if request_date >= last_thursday_at_midnight:
                thanksgivings_after_last_thursday.append(f"{burning_heart_emoji}{row[1]}: \n{row[2]}\n")
            else:
                # if we've hit a row before last Thursday at 12am, we can stop searching
                break
        # update the current row to the next batch
        current_row += batch_size
        # if the last row in the batch was before the cut-off date, we can stop searching
        if request_date < last_thursday_at_midnight:
            break

    # format response text
    introduction = "Here are the final compiled thanksgiving items from this past week!!\n\n"
    response_text = introduction + '\n'.join(thanksgivings_after_last_thursday)
    subscribers = membersSheet.get_all_records()  
    for subscriber in subscribers:
        if subscriber['Subscribed'] == 'TRUE':  
            chat_id = subscriber['UserID']  
            try:
                await context.bot.send_message(chat_id=chat_id, text=response_text)
            except Exception as e:
                print(f"Failed to send reminder to {chat_id}: {e}")

async def weekly_thanksgivings_blast(context):
    while True:
        now = datetime.now()
        if now.weekday() == 2 and now.hour == 22 and 50 < now.minute < 59:  #between 10:50 and 10:59pm on wednesday
            print(f"Sending reminders at {now}")
            await blast_thanksgivings(context)
            await asyncio.sleep(60 * 60)  # wait for 1 hour to avoid multiple sends
        else:
            await asyncio.sleep(30)

async def blast_requests(context):
    now = datetime.now()
    days_until_thursday = (3 - now.weekday()) % 7 
    last_thursday = now - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0))  
    if now.weekday() == 3 and now.time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)

    requests_after_last_thursday = []

    current_row = 2
    batch_size = 50  
    while True:
        rows = prayer_sheet.get(f"A{current_row}:C{current_row + batch_size - 1}")
        if not rows:
            break
        for row in rows:
            request_date = datetime.strptime(row[0], '%Y-%m-%d')
            if request_date >= last_thursday_at_midnight:
                requests_after_last_thursday.append(f"{burning_heart_emoji}{row[1]}: \n{row[2]}\n")
            else:
                break
        current_row += batch_size
        if request_date < last_thursday_at_midnight:
            break

    introduction = "Here are the final compiled prayer requests from this past week!!\n\n"
    response_text = introduction + '\n'.join(requests_after_last_thursday)
    subscribers = membersSheet.get_all_records()  
    for subscriber in subscribers:
        if subscriber['Subscribed'] == 'TRUE':  
            chat_id = subscriber['UserID'] 
            try:
                await context.bot.send_message(chat_id=chat_id, text=response_text)
            except Exception as e:
                print(f"Failed to send reminder to {chat_id}: {e}")

async def weekly_requests_blast(context):
    while True:
        now = datetime.now()
        if now.weekday() == 2 and now.hour == 22 and 50 < now.minute < 59:  
            print(f"Sending reminders at {now}")
            await blast_requests(context)
            await asyncio.sleep(60 * 60)  
        else:
            await asyncio.sleep(30)  

async def blast_reflections(context):
    now = datetime.now()
    days_until_thursday = (3 - now.weekday()) % 7  
    last_thursday = now - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0))  
    if now.weekday() == 3 and now.time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)

    requests_after_last_thursday = []

    current_row = 2
    batch_size = 50  
    while True:
        rows = reflections_sheet.get(f"A{current_row}:C{current_row + batch_size - 1}")
        if not rows:
            break
        for row in rows:
            request_date = datetime.strptime(row[0], '%Y-%m-%d')
            if request_date >= last_thursday_at_midnight:
                requests_after_last_thursday.append(f"{burning_heart_emoji}{row[1]}: \n{row[2]}\n")
            else:
                break
        current_row += batch_size
        if request_date < last_thursday_at_midnight:
            break

    introduction = "Here are the final compiled reflections from this past week!!\n\n"
    response_text = introduction + '\n'.join(requests_after_last_thursday)
    subscribers = membersSheet.get_all_records() 
    for subscriber in subscribers:
        if subscriber['Subscribed'] == 'TRUE': 
            chat_id = subscriber['UserID']  
            try:
                await context.bot.send_message(chat_id=chat_id, text=response_text)
            except Exception as e:
                print(f"Failed to send reminder to {chat_id}: {e}")

async def weekly_reflections_blast(context):
    while True:
        now = datetime.now()
        if now.weekday() == 2 and now.hour == 22 and 50 < now.minute < 59:  
            print(f"Sending reminders at {now}")
            await blast_reflections(context)
            await asyncio.sleep(60 * 60)  
        else:
            await asyncio.sleep(30) 

async def process_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    password_try = update.message.text
    if password_try == password: 
        await update.message.reply_text(
            'Password accepted. What is your name (do not include surname, unless there are >1 of you in this group with same name)?',
            reply_markup=ForceReply(selective=True),
        )
        return NAME 
    else:
        await update.message.reply_text('Incorrect password. Please try again.')
        return ConversationHandler.END

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['actual_name'] = update.message.text
    await update.message.reply_text(
        'What is your birthday? Please enter in the format DD/MM/YYYY.',
        reply_markup=ForceReply(selective=True),
    )
    return BIRTHDAY

async def receive_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    birthday_text = update.message.text
    user_id = update.effective_chat.id
    user_name = update.effective_user.full_name
    # Retrieve the actual name from the context
    actual_name = context.user_data.get('actual_name', 'Unknown')  # Default to 'Unknown' if not found
    try:
        # Parse the birthday to ensure it is valid and in the correct format
        birthday = datetime.strptime(birthday_text, '%d/%m/%Y').strftime('%d/%m/%Y')
        # Add the user, actual name, and the birthday to the subscribers worksheet
        membersSheet.append_row([user_id, True, user_name, birthday, actual_name])
        await update.message.reply_text('Your details have been recorded and you have subscribed to bot reminders. Thank you!')
        return ConversationHandler.END
    except ValueError:
        # If the date is not in the correct format, ask for the input again
        await update.message.reply_text(
            'The date format is incorrect. Please enter your birthday in the format MM/DD/YYYY.',
            reply_markup=ForceReply(selective=True),
        )
        return BIRTHDAY

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_chat.id
    # search for the user in the subscribers worksheet and update their status
    cell = membersSheet.find(str(user_id))
    if cell:
        membersSheet.update_cell(cell.row, 2, False)  # assuming the 'Subscribed' column is column 2
    await update.message.reply_text('You have unsubscribed from bot reminders.')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Welcome to the Cell Group Bot! Please enter the password to start. If you cancelled the reply pop-up on accident, just send the command /cancel and start again',
        reply_markup=ForceReply(selective=True),
        )
    return PASSWORD

async def ask_for_prayer_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'What are your prayer requests for this week? If you cancelled the reply pop-up on accident, just send the command /cancel and start again',
        reply_markup=ForceReply(selective=True),
    )
    return PRAYER_REQUEST

async def ask_for_thanksgiving(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'What are your thanksgiving items for this week? If you cancelled the reply pop-up on accident, just send the command /cancel and start again',
        reply_markup=ForceReply(selective=True),
    )
    return THANKSGIVING

async def ask_for_reflection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'How did God speak to you this week? If you cancelled the reply pop-up on accident, just send the command /cancel and start again',
        reply_markup=ForceReply(selective=True),
    )
    return REFLECTION

async def receive_reflection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    reflection_text = update.message.text
    user_name = update.effective_user.full_name
    current_date = datetime.now().strftime('%Y-%m-%d')

    days_until_thursday = (3 - datetime.now().weekday()) % 7 # change if you want it to be a different day!
    last_thursday = datetime.now() - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0))
    if datetime.now().weekday() == 3 and datetime.now().time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)

    cell_list = reflections_sheet.range('A2:C50')  

    existing_entry_row = None
    for i in range(0, len(cell_list), 3): 
        row_date = cell_list[i].value
        row_name = cell_list[i+1].value
        if row_date and row_name: 
            row_date = datetime.strptime(row_date, '%Y-%m-%d')
            if row_name == user_name and last_thursday_at_midnight <= row_date < last_thursday_at_midnight + timedelta(days=7):
                existing_entry_row = i // 3 + 2  
                break

    if existing_entry_row:
        existing_reflection = reflections_sheet.cell(existing_entry_row, 3).value
        updated_reflection = existing_reflection + "\n" + "//" + reflection_text
        reflections_sheet.update_cell(existing_entry_row, 3, updated_reflection)
        response_message = 'Your reflection has been updated. Thank you!'
    else:
        reflections_sheet.insert_row([current_date, user_name, reflection_text], index=2)
        response_message = 'Your reflection has been recorded. Thank you!'

    await update.message.reply_text(response_message)
    return ConversationHandler.END

async def receive_prayer_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prayer_request_text = update.message.text
    user_name = update.effective_user.full_name
    current_date = datetime.now().strftime('%Y-%m-%d')

    days_until_thursday = (3 - datetime.now().weekday()) % 7
    last_thursday = datetime.now() - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0))
    if datetime.now().weekday() == 3 and datetime.now().time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)

    cell_list = prayer_sheet.range('A2:C50')  

    existing_entry_row = None
    for i in range(0, len(cell_list), 3): 
        row_date = cell_list[i].value
        row_name = cell_list[i+1].value
        if row_date and row_name:  
            row_date = datetime.strptime(row_date, '%Y-%m-%d')
            if row_name == user_name and last_thursday_at_midnight <= row_date < last_thursday_at_midnight + timedelta(days=7):
                existing_entry_row = i // 3 + 2  
                break

    if existing_entry_row:
        existing_request = prayer_sheet.cell(existing_entry_row, 3).value
        updated_request = existing_request + "\n" + "//" + prayer_request_text
        prayer_sheet.update_cell(existing_entry_row, 3, updated_request)
        response_message = 'Your prayer requests have been updated. Thank you!'
    else:
        prayer_sheet.insert_row([current_date, user_name, prayer_request_text], index=2)
        response_message = 'Your prayer requests have been recorded. Thank you!'

    await update.message.reply_text(response_message)
    return ConversationHandler.END

async def receive_thanksgiving(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    thanksgiving_text = update.message.text
    user_name = update.effective_user.full_name
    current_date = datetime.now().strftime('%Y-%m-%d')

    days_until_thursday = (3 - datetime.now().weekday()) % 7
    last_thursday = datetime.now() - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0))
    if datetime.now().weekday() == 3 and datetime.now().time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)

    cell_list = thanksgiving_sheet.range('A2:C50')  

    existing_entry_row = None
    for i in range(0, len(cell_list), 3):
        row_date = cell_list[i].value
        row_name = cell_list[i+1].value
        if row_date and row_name: 
            row_date = datetime.strptime(row_date, '%Y-%m-%d')
            if row_name == user_name and last_thursday_at_midnight <= row_date < last_thursday_at_midnight + timedelta(days=7):
                existing_entry_row = i // 3 + 2 
                break

    if existing_entry_row:
        existing_thanksgiving = thanksgiving_sheet.cell(existing_entry_row, 3).value
        updated_thanksgiving = existing_thanksgiving + "\n" + "//" + thanksgiving_text
        thanksgiving_sheet.update_cell(existing_entry_row, 3, updated_thanksgiving)
        response_message = 'Your thanksgiving items have been updated. Thank you!'
    else:
        thanksgiving_sheet.insert_row([current_date, user_name, thanksgiving_text], index=2)
        response_message = 'Your thanksgiving items have been recorded. Thank you!'

    await update.message.reply_text(response_message)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('The operation has been cancelled.')
    return ConversationHandler.END

async def send_reflection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Please share your reflections. If you cancelled the reply pop-up on accident, just send the command /cancel and start again')

async def view_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    days_until_thursday = (3 - now.weekday()) % 7  
    last_thursday = now - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0))
    if now.weekday() == 3 and now.time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)
        
    prayer_requests_after_last_thursday = []

    current_row = 2
    batch_size = 50  
    while True:
        rows = prayer_sheet.get(f"A{current_row}:C{current_row + batch_size - 1}")
        if not rows:
            break
        for row in rows:
            request_date = datetime.strptime(row[0], '%Y-%m-%d')
            if request_date >= last_thursday_at_midnight:
                prayer_requests_after_last_thursday.append(f"{burning_heart_emoji} {row[1]}: \n{row[2]}\n")
            else:
                break
        current_row += batch_size
        if request_date < last_thursday_at_midnight:
            break

    response_text = '\n'.join(prayer_requests_after_last_thursday)

    if response_text:
        await update.message.reply_text(f'Here are the prayer requests for this week{folded_hands}{pleading_face}:\n\n{response_text}')
    else:
        await update.message.reply_text('There are no new prayer requests for this week.')

async def view_thanksgivings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    days_until_thursday = (3 - now.weekday()) % 7  
    last_thursday = now - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0))  
    if now.weekday() == 3 and now.time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)

    thanksgivings_after_last_thursday = []

    current_row = 2
    batch_size = 50  
    while True:
        rows = thanksgiving_sheet.get(f"A{current_row}:C{current_row + batch_size - 1}")
        if not rows:
            break
        for row in rows:
            request_date = datetime.strptime(row[0], '%Y-%m-%d')
            if request_date >= last_thursday_at_midnight:
                thanksgivings_after_last_thursday.append(f"{burning_heart_emoji}{row[1]}: \n{row[2]}\n")
            else:
                break
        current_row += batch_size
        if request_date < last_thursday_at_midnight:
            break

    response_text = '\n'.join(thanksgivings_after_last_thursday)

    if response_text:
        await update.message.reply_text(f'Here are the thanksgiving items for this week{raising_hands}{clinking_glasses}:\n\n{response_text}')
    else:
        await update.message.reply_text('There are no new thanksgiving items for this week.')

async def view_reflections(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    days_until_thursday = (3 - now.weekday()) % 7  
    last_thursday = now - timedelta(days=days_until_thursday)
    last_thursday_at_midnight = datetime.combine(last_thursday.date(), time(0, 0)) 
    if now.weekday() == 3 and now.time() < time(0, 0):
        last_thursday_at_midnight -= timedelta(days=7)

    reflections_after_last_thursday = []

    current_row = 2
    batch_size = 50  
    while True:
        rows = reflections_sheet.get(f"A{current_row}:C{current_row + batch_size - 1}")
        if not rows:
            break
        for row in rows:
            request_date = datetime.strptime(row[0], '%Y-%m-%d')
            if request_date >= last_thursday_at_midnight:
                reflections_after_last_thursday.append(f"{burning_heart_emoji}{row[1]}: \n{row[2]}\n")
            else:
                break
        current_row += batch_size
        if request_date < last_thursday_at_midnight:
            break

    response_text = '\n'.join(reflections_after_last_thursday)

    if response_text:
        await update.message.reply_text(f'Here are the reflections for this week{thought_balloon}{writing_hand}:\n\n{response_text}')
    else:
        await update.message.reply_text('There are no new reflections for this week.')


def main():
    application = ApplicationBuilder().token(telegram_bot_token).build()

    prayer_request_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('submit_prayer_requests', ask_for_prayer_request)],
        states={
            PRAYER_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_prayer_request)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    thanksgiving_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('submit_thanksgivings', ask_for_thanksgiving)],
        states={
            THANKSGIVING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_thanksgiving)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    start_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_start)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_birthday)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    reflection_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('submit_reflection', ask_for_reflection)],
        states={
            REFLECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reflection)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(start_conversation_handler) #register
    application.add_handler(CommandHandler('view_requests', view_requests)) #view_requests
    application.add_handler(CommandHandler('view_thanksgivings', view_thanksgivings)) #view_thanksgivings
    application.add_handler(CommandHandler('view_reflections', view_reflections)) #view_reflections
    application.add_handler(CommandHandler('unsubscribe', unsubscribe))
    application.add_handler(prayer_request_conversation_handler) #submit_prayer_request
    application.add_handler(thanksgiving_conversation_handler) #submit_thanksgiving
    application.add_handler(reflection_conversation_handler) #submit_reflection

    # create the asyncio event loop
    loop = asyncio.get_event_loop()

    # start the scheduled reminders
    loop.create_task(weekly_reminder(application))
    loop.create_task(weekly_thanksgivings_blast(application))
    loop.create_task(weekly_requests_blast(application))
    loop.create_task(weekly_reflections_blast(application))

    loop.run_until_complete(application.run_polling())


if __name__ == '__main__':
    asyncio.run(main())