

import time
import json
import telegram.ext
import telegram
import sys
import datetime
import os
import logging
import threading


Version_Code = 'v1.1.0' 

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )

PATH = os.path.dirname(os.path.realpath(__file__)) + '/'

CONFIG = json.loads(open(PATH + 'config.json', 'r').read())  

MESSAGE_LOCK = False

message_list = json.loads(open(PATH + 'data.json', 'r').read())  

PREFERENCE_LOCK = False

preference_list = json.loads(open(PATH + 'preference.json', 'r').read()) 

def save_data():  
    global MESSAGE_LOCK
    while MESSAGE_LOCK:
        time.sleep(0.05)
    MESSAGE_LOCK = True
    f = open(PATH + 'data.json', 'w')
    f.write(json.dumps(message_list))
    f.close()
    MESSAGE_LOCK = False

def save_preference():  
    global PREFERENCE_LOCK
    while PREFERENCE_LOCK:
        time.sleep(0.05)
    PREFERENCE_LOCK = True
    f = open(PATH + 'preference.json', 'w')
    f.write(json.dumps(preference_list))
    f.close()
    PREFERENCE_LOCK = False

def save_config(): 
    f = open(PATH + 'config.json', 'w')
    f.write(json.dumps(CONFIG, indent=4))
    f.close()

def init_user(user): 
    global preference_list
    if not str(user.id) in preference_list: 
        preference_list[str(user.id)] = {}
        preference_list[str(user.id)]['notification'] = False 
        preference_list[str(user.id)]['blocked'] = False 
        preference_list[str(user.id)]['name'] = user.full_name 
        threading.Thread(target=save_preference).start()
        return
    if not 'blocked' in preference_list[str(user.id)]: 
        preference_list[str(user.id)]['blocked'] = False
    if preference_list[str(user.id)]['name'] != user.full_name:  
        preference_list[str(user.id)]['name'] = user.full_name
        threading.Thread(target=save_preference).start()

updater = telegram.ext.Updater(token=CONFIG['Token'])
dispatcher = updater.dispatcher

me = updater.bot.get_me()
CONFIG['ID'] = me.id
CONFIG['Username'] = '@' + me.username

print('Starting... (ID: ' + str(CONFIG['ID']) + ', Username: ' \
    + CONFIG['Username'] + ')')

def process_msg(bot, update): 
    global message_list
    init_user(update.message.from_user)
    if CONFIG['Admin'] == 0: 
        bot.send_message(chat_id=update.message.from_user.id,
                         text="Please complete the configuration first.")
        return
    if update.message.from_user.id == CONFIG['Admin']: 
        if update.message.reply_to_message: 
            if str(update.message.reply_to_message.message_id) in message_list: 
                msg = update.message
                sender_id = message_list[str(update.message.reply_to_message.message_id)]['sender_id']
               
                try:
                    if msg.audio:
                        bot.send_audio(chat_id=sender_id,
                                audio=msg.audio, caption=msg.caption)
                    elif msg.document:
                        bot.send_document(chat_id=sender_id,
                                document=msg.document,
                                caption=msg.caption)
                    elif msg.voice:
                        bot.send_voice(chat_id=sender_id,
                                voice=msg.voice, caption=msg.caption)
                    elif msg.video:
                        bot.send_video(chat_id=sender_id,
                                video=msg.video, caption=msg.caption)
                    elif msg.sticker:
                        bot.send_sticker(chat_id=sender_id,
                                sticker=update.message.sticker)
                    elif msg.photo:
                        bot.send_photo(chat_id=sender_id,
                                photo=msg.photo[0], caption=msg.caption)
                    elif msg.text_markdown:
                        bot.send_message(chat_id=sender_id,
                                text=msg.text_markdown,
                                parse_mode=telegram.ParseMode.MARKDOWN)
                    else:
                        bot.send_message(chat_id=CONFIG['Admin'],
                                text="Do not support to reply the user this type of message.")
                        return
                except Exception as e:
                    if e.message \
                        == 'Forbidden: bot was blocked by the user':
                        bot.send_message(chat_id=CONFIG['Admin'],
                                text="This user stopped the bot so you cannot reply.") 
                    else:
                        bot.send_message(chat_id=CONFIG['Admin'],
                                text="Failed to reply, please retry.")
                    return
                if preference_list[str(update.message.from_user.id)]['notification']: 
                    bot.send_message(chat_id=update.message.chat_id,
                            text="Replied.\nReceiver：%s [Link](tg://user?id=%s)"
                            % (preference_list[str(sender_id)]['name'],
                            str(sender_id)),
                            parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                bot.send_message(chat_id=CONFIG['Admin'],
                                 text="No data of this message. Cannot inquire or reply.")
        else:
            bot.send_message(chat_id=CONFIG['Admin'],
                             text="Please reply to a message.")
    else: 
        if preference_list[str(update.message.from_user.id)]['blocked']:
            bot.send_message(chat_id=update.message.from_user.id,text="You won't be able to send messages to the admin because you have been banned.")
            return
        fwd_msg = bot.forward_message(chat_id=CONFIG['Admin'],
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id)  
        if fwd_msg.sticker:  
            bot.send_message(chat_id=CONFIG['Admin'],
                             text="Sender：%s [Link](tg://user?id=%s)"
                             % (update.message.from_user.full_name,
                             str(update.message.from_user.id)),
                             parse_mode=telegram.ParseMode.MARKDOWN,
                             reply_to_message_id=fwd_msg.message_id)
        if preference_list[str(update.message.from_user.id)]['notification']: 
            bot.send_message(chat_id=update.message.from_user.id,text="Your message has been forwarded to my master.")
        message_list[str(fwd_msg.message_id)] = {}
        message_list[str(fwd_msg.message_id)]['sender_id'] = update.message.from_user.id
        threading.Thread(target=save_data).start()  
    pass

def process_command(bot, update):  
    init_user(update.message.from_user)
    id = update.message.from_user.id
    global CONFIG
    global preference_list
    command = update.message.text[1:].replace(CONFIG['Username'], ''
            ).lower().split()
    if command[0] == 'start':
        bot.send_message(chat_id=update.message.chat_id,
                         text="Hey!! there I'm Zeo Two, I'm help to contact with my master.\nAll your messages sent to me will be forwarded to my master.\n/togglenotification can toggle message sending notification status, off by default.\n/help list commands.\n\nJoin our support chat @allukatm\nNOTE: Don't try to PM me you will be block by bot.")
        return
    elif command[0] == 'help':
        bot.send_message(chat_id=update.message.chat_id,
                         text="""/ping Check server ping 🏓.
/togglenotification to the bot to enable/disable the message sending notification.
/info to the message which you want to get its sender's info more clearly.
/aboutme to know about more my master.
/botlist list of bots.
/ban to a message to block the sender of the message from sending messages to you. (admin only)
/unban to a message or send /unban <User ID> to unban a user. (admin only)
/setadmin to set new admin. (admin only)

Join our Support chat @allukatm"""
                         )
        return
    elif command[0] == 'setadmin':
        if CONFIG['Admin'] == 0:  
            CONFIG['Admin'] = int(update.message.from_user.id)
            save_config()
            bot.send_message(chat_id=update.message.chat_id,
                             text= "You have been set as the admin successfully.")
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="The admin has been set. ")
        return
    elif command[0] == 'togglenotification':
        preference_list[str(id)]['notification'] = \
            preference_list[str(id)]['notification'] == False
        threading.Thread(target=save_preference).start()
        if preference_list[str(id)]['notification']:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Enabled message sending notification. Now I'm start will give a feedback when I  receives your message.")
        else:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Disabled message sending notification. Now I'm will not give a feedback when I receives your message.")
    elif command[0] == 'info': 
        if update.message.from_user.id == CONFIG['Admin'] \
            and update.message.chat_id == CONFIG['Admin']:
            if update.message.reply_to_message:
                if str(update.message.reply_to_message.message_id) in message_list:
                    sender_id = message_list[str(update.message.reply_to_message.message_id)]['sender_id']
                    bot.send_message(chat_id=update.message.chat_id,
                            text="Sender：%s [Link](tg://user?id=%s)"
                            % (preference_list[str(sender_id)]['name'],
                            str(sender_id)),
                            parse_mode=telegram.ParseMode.MARKDOWN,
                            reply_to_message_id=update.message.reply_to_message.message_id)
                else:
                    bot.send_message(chat_id=update.message.chat_id,text="No data of this message. Cannot inquire or reply.")
            else:
                bot.send_message(chat_id=update.message.chat_id,text="Please reply to a message.")
        else:
            bot.send_message(chat_id=update.message.chat_id, text="You have no permission.")
    elif command[0] == 'ping':
        start_time = time.time()
        bot.send_message(chat_id=update.message.chat_id, text='Pong!') 
        end_time = time.time()
        ping_time = float(end_time - start_time)
        bot.send_message(chat_id=update.message.chat_id,parse_mode='Markdown', text=f"Pong!\nThe speed: {ping_time} ms 🏓")
     
    elif command[0] == 'aboutme':
        bot.send_message(chat_id=update.message.chat_id,
                         text="Personal Website: meanii.me\nInsta: @mitshuhataki\nDiscord: @meanii\nGithub: @anilchauhanxda")

    elif command[0] == 'botlist':
        bot.send_message(chat_id=update.message.chat_id,
                         text="""@allukabot: specially customized for used sudo and normal users based on uniborg.
 @zoldycktmbot: Modular Telegram bot for managing your groups with a few extras features with zoldyck family theme.
 @meanyabot: She will help you to download audio files from youtube link.
 @ShinoaRobot: You can use it to create custom sticker packs using existing stickers or PNG files.
 @jubiaRobot: She can make for you todo list.
 @erzaRobot: Send to her what you want and you will get the same message back, then forward the message where you want and the forward label will have the name of this bot.
 It works also if you edit messages or forward messages. It also keeps the same text formatting style.
 @mirajaneRobot: She will help to upload any telegram video to youtube once you authorise her.
 @akameRobot: She can checks grammar of every message sent in PM or group. 
 @lisannaRobot: She can help you not to forget important tasks 🙌🏻 
 @zerotwopmbot: I'm Zeo Two, I'm help to contact with my master.
 
 Join our Support chat @allukatm""")
    
    
    elif command[0] == 'ban': 
        if update.message.from_user.id == CONFIG['Admin'] \
            and update.message.chat_id == CONFIG['Admin']:
            if update.message.reply_to_message:
                if str(update.message.reply_to_message.message_id) in message_list:
                    sender_id = message_list[str(update.message.reply_to_message.message_id)]['sender_id']
                    preference_list[str(sender_id)]['blocked'] = True
                    bot.send_message(chat_id=update.message.chat_id,
                            text="ser %s [Link](tg://user?id=%s)\nHas been banned."
                            % (preference_list[str(sender_id)]['name'],
                            str(sender_id)),
                            parse_mode=telegram.ParseMode.MARKDOWN)
                    bot.send_message(chat_id=sender_id,text="You won't be able to send messages to the admin because you have been banned.")
                else:
                    bot.send_message(chat_id=update.message.chat_id,text="No data of this message. Cannot inquire or reply.")
            else:
                bot.send_message(chat_id=update.message.chat_id,text="Please reply to a message.")
        else:
            bot.send_message(chat_id=update.message.chat_id, text="You have no permission.")
    elif command[0] == 'unban': 
        if update.message.from_user.id == CONFIG['Admin'] \
            and update.message.chat_id == CONFIG['Admin']:
            if update.message.reply_to_message:
                if str(update.message.reply_to_message.message_id) in message_list:
                    sender_id = message_list[str(update.message.reply_to_message.message_id)]['sender_id']
                    preference_list[str(sender_id)]['blocked'] = False
                    bot.send_message(chat_id=update.message.chat_id,
                            text="User %s [Link](tg://user?id=%s)\nHas been unbanned."
                            % (preference_list[str(sender_id)]['name'],
                            str(sender_id)),
                            parse_mode=telegram.ParseMode.MARKDOWN)
                    bot.send_message(chat_id=sender_id,text="You have been unbanned.")
                else:
                    bot.send_message(chat_id=update.message.chat_id,text="No data of this message. Cannot inquire or reply.")
            elif len(command) == 2:
                if command[1] in preference_list:
                    preference_list[command[1]]['blocked'] = False
                    bot.send_message(chat_id=update.message.chat_id,
                            text="User %s [Link](tg://user?id=%s)\nHas been unbanned."
                            % (preference_list[command[1]]['name'],
                            command[1]),
                            parse_mode=telegram.ParseMode.MARKDOWN)
                    bot.send_message(chat_id=int(command[1]),text="You have been unbanned.")
                else:
                    bot.send_message(chat_id=update.message.chat_id,text="User not found.")
            else:
                bot.send_message(chat_id=update.message.chat_id,text="Please reply to a message or enter the ID of the user who has been banned.")
        else:
            bot.send_message(chat_id=update.message.chat_id, text="Please reply to a message or enter the ID of the user who has been banned.")
    else: 
        bot.send_message(chat_id=update.message.chat_id, text="Command not found.")



dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.all
                       & telegram.ext.Filters.private
                       & ~telegram.ext.Filters.command
                       & ~telegram.ext.Filters.status_update,
                       process_msg)) 

dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.command
                       & telegram.ext.Filters.private, process_command)) 

updater.start_polling()  
print('Started')
updater.idle()
print('Stopping...')
save_data()  
save_preference() 
print('Data saved.')
print('Stopped.')
