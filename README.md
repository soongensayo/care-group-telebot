# CARE GROUP TELEBOT (V1)

## Introduction

Why a Care Group Telebot? 
- Tool to keep people within a care group involved in the lives of one another
- For care group members to be comfortable sharing personal matters in a bite-sized manner
- For care group members know how to pray for & encourage one another

Main features:
- Linked to a Google Spreadsheet (where all the data will be stored, and for easy access separately)
- Members can submit items under 3 categories:
    1. Thanksgiving items
    2. Prayer requests
    3. Reflections
- Members can also view all submitted items by everyone in the group (that has been submitted within the past week)
- Weekly reminders: reminds users (by default, on Wednesday) to submit in their items for the week
- Weekly blasts: blasts out all thanksgiving items (by default, on Thursday), prayer requests and reflections that members have sent over the week

## To start

### Environment Variables

Before running the bot, you need to set up your environment variables:
1. Copy `.env.sample` to a new file named `.env`
2. Replace the placeholder values as you go along the other steps below

### Setting up the Telegram Bot

1. Search @botfather on telegram and message it
2. Send /start and follow the steps to create a new telegram bot
3. Copy the API token (paste it under "TELEGRAM_BOT_TOKEN") and use it in your project

### Setting up Google Service Account (for access to your bot's Google Spreadsheet)
1. Go to Google Cloud and create a new project
2. Go to "IAM and admin" -> "Service accounts" 
3. Create a new service account
4. Generate Keys: 
    - Click on "Create Key"
    - Choose "JSON" as the key type
    - Click "Create". **This will download a JSON file containing your service account's credentials to your computer, which you will then add into the root of the project folder! (IMPORTANT)**

### Setting up the Google Spreadsheet
1. Create a Google Spreadsheet (this will be the database for everything regarding this bot!)
2. Rename your spreadsheet and copy the sheet name (paste it under "SHEET_NAME") 
3. Share the sheet with the email of your service account (created in step 2), and grant it permission to edit 

### Congrats!
Start messaging your telebot, and share it with your care group members

## Notes
Currently, the code is not refined at all and there are lots of improvements to be made...in due time!