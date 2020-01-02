# pip install python-telegram-bot
import telegram.bot
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, ConversationHandler)
from telegram.ext.dispatcher import run_async
import logging
from functools import wraps
import random
import time
from cred import bottoken, adminpass, port
import json

# pip install pyopenssl
from requests import get
ip = get('https://api.ipify.org').text
try:
    certfile = open("cert.pem")
    keyfile = open("private.key")
    certfile.close()
    keyfile.close()
except IOError:
    from OpenSSL import crypto
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    cert = crypto.X509()
    cert.get_subject().CN = ip
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    with open("cert.pem", "wt") as certfile:
        certfile.write(crypto.dump_certificate(
            crypto.FILETYPE_PEM, cert).decode('ascii'))
    with open("private.key", "wt") as keyfile:
        keyfile.write(crypto.dump_privatekey(
            crypto.FILETYPE_PEM, key).decode('ascii'))

logging.basicConfig(filename='debug.log', filemode='a+', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

TARGET, CONTENT = range(2)


def loader():
    global users
    try:
        with open('users.json') as usersfile:
            users = json.load(usersfile)
    except:
        with open('users.json', 'w+') as usersfile:
            users = {}
    global usernames
    try:
        with open('usernames.json') as usernamesfile:
            usernames = json.load(usernamesfile)
    except:
        with open('usernames.json', 'w+') as usernamesfile:
            usernames = {}
    global admins
    try:
        with open('admins.json') as adminsfile:
            admins = json.load(adminsfile)
    except:
        with open('admins.json', 'w+') as adminsfile:
            admins = []
    global mymortal
    try:
        with open('mymortal.json') as mymortalfile:
            mymortal = json.load(mymortalfile)
    except:
        with open('mymortal.json', 'w+') as mymortalfile:
            mymortal = {}
    global myangel
    try:
        with open('myangel.json') as myangelfile:
            myangel = json.load(myangelfile)
    except:
        with open('myangel.json', 'w+') as myangelfile:
            myangel = {}


def parse(text, length):
    start = int(length) + 2
    message = text[start:]
    return message


def adminonly(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id not in admins:
            flood(context, user_id, "*ADMIN ONLY*\nYou shall not pass!")
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def useronly(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if user_id not in users:
            flood(context, user_id, "Please /join first.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped


@run_async
def start(update, context):
    update.message.reply_text(
        "*Welcome to LTF Angel & Mortal!*\n\nPress /join to enter.", parse_mode=telegram.ParseMode.MARKDOWN)


@run_async
def unknown(update, context):
    commands = '''
*COMMANDS*
/join - Join the game
/leave - Leave the game
/message - Send messages
/cc - Message to admins

*ADMIN COMMANDS*
/botadmin - Hmm...
/newgame - Start game
/endgame - Stop game
/broadcast - Send to all players
/players - List of all players
/reset - Reloads lists from file
/who - Check player's angel
/tester - Do not touch!
    '''
    update.message.reply_text(commands, parse_mode=telegram.ParseMode.MARKDOWN)


def join(update, context):
    user_id = str(update.message.from_user.id)
    first_name = update.message.from_user.first_name
    last_name = update.message.from_user.last_name
    full_name = (str(first_name or '') + ' ' + str(last_name or '')).strip()
    users[user_id] = full_name
    with open('users.json', 'w') as userfile:
        json.dump(users, userfile)
    username = update.message.from_user.username
    if username:
        usernames[username] = user_id
        with open('usernames.json', 'w') as usernamesfile:
            json.dump(usernames, usernamesfile)
    responder(
        update, "Welcome *{}*.\n\nPress /help for info on commands.".format(full_name))


@useronly
def leave(update, context):
    user_id = str(update.message.from_user.id)
    if user_id not in mymortal:
        del users[user_id]
        with open('users.json', 'w') as userfile:
            json.dump(users, userfile)
        responder(update, "_You have left the game._")
    else:
        responder(update, "_You cannot leave while game is in progress._")


def botadmin(update, context):
    user_id = str(update.message.from_user.id)
    if user_id in admins:
        responder(update, "`You are already an admin!`")
    else:
        message = parse(update.message.text, len("botadmin"))
        if message == adminpass:
            admins.append(user_id)
            with open('admins.json', 'w') as adminfile:
                json.dump(admins, adminfile)
            responder(update, "`You are now an admin!`")
        else:
            responder(update, "`Nope.`")


@adminonly
def newgame(update, context):
    responder(update, "_Randomising angels & mortals..._")
    time.sleep(0.05)
    if len(users) < 3:
        responder(update, "_Error! At least 3 players needed._")
        return
    do_pairings()
    responder(update, "_Sending everyone their mortal's names..._")
    time.sleep(0.05)
    for user_id in mymortal:
        mortal_id = mymortal[user_id]
        mortal_name = users[mortal_id]
        address = user_id
        msg = "Your mortal is: *{mortal}*\nUse /message to talk to them.".format(
            mortal=mortal_name)
        flood(context, address, msg)
        time.sleep(0.05)
        sendprofilepic(context, mortal_id, address)
        time.sleep(0.05)
    responder(update, "_Game started!_")


def shuffle():
    list1 = []
    list2 = []
    for user_id in users:
        list1.append(user_id)
        list2.append(user_id)
    random.shuffle(list1)
    random.shuffle(list2)
    mymortal = dict(zip(list1, list2))
    for key, value in mymortal.items():
        if key == value:
            return False
        if key == mymortal[value]:
            return False
    myangel = {value: key for key, value in mymortal.items()}
    with open('mymortal.json', 'w') as mymortalfile:
        json.dump(mymortal, mymortalfile)
    with open('myangel.json', 'w') as myangelfile:
        json.dump(myangel, myangelfile)
    return True


def do_pairings():
    result = shuffle()
    while not result:
        result = shuffle()
    loader()


@adminonly
def endgame(update, context):
    responder(update, "_Revealing angels & mortals..._")
    time.sleep(0.05)
    compose = '*Game Ended!*\n\n*Angel -> Mortal list:*\n'
    for user_id in myangel:
        angel_id = myangel[user_id]
        angel_name = users[angel_id]
        address = user_id
        msg = "Your angel was: *{angel}*".format(angel=angel_name)
        flood(context, address, msg)
        time.sleep(0.05)
        sendprofilepic(context, angel_id, address)
        time.sleep(0.05)
        user_name = users[user_id]
        compose += "[{}](tg://user?id={}) -> [{}](tg://user?id={})\n".format(
            angel_name, angel_id, user_name, user_id)
    for user_id in admins:
        address = user_id
        flood(context, address, compose)
        time.sleep(0.05)
    blank = {}
    with open('mymortal.json', 'w') as mymortalfile:
        json.dump(blank, mymortalfile)
    with open('myangel.json', 'w') as myangelfile:
        json.dump(blank, myangelfile)
    loader()


@adminonly
def broadcast(update, context):
    message = parse(update.message.text, len("broadcast"))
    if len(message) < 1:
        responder(
            update, "_Type your message after the command\ne.g._ /broadcast Hello.")
    else:
        responder(update, "_Sending..._")
        time.sleep(0.05)
        for address in users:
            msg = "*BROADCAST FROM ADMINS:*\n\n{}".format(message)
            flood(context, address, msg)
            time.sleep(0.05)
        responder(update, "_Broadcast sent!_")


@useronly
def cc(update, context):
    message = parse(update.message.text, len("cc"))
    if len(message) < 1:
        responder(update, "_Type your message after the command\ne.g._ /cc Hello.")
    else:
        responder(update, "_Sending..._")
        time.sleep(0.05)
        user_id = str(update.message.from_user.id)
        sender_name = users[user_id]
        for address in admins:
            msg = "*Message to Admins from {}:*\n\n{}".format(
                sender_name, message)
            flood(context, address, msg)
            time.sleep(0.05)
        responder(update, "_Message sent to Admins!_")


@run_async
def flood(context, address, msg):
    context.bot.send_message(chat_id=int(address), text=msg,
                             parse_mode=telegram.ParseMode.MARKDOWN)


@run_async
def responder(update, msg):
    update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN,
                              reply_markup=telegram.ReplyKeyboardRemove())


@run_async
def sendprofilepic(context, subject, address):
    try:
        profilepic = (context.bot.get_user_profile_photos(
            subject, limit=1)['photos'][0][-1]['file_id'])
        context.bot.send_photo(address, profilepic)
    except:
        pass


@adminonly
def players(update, context):
    context.bot.send_chat_action(
        chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    count = 1
    compose = "*Players:*\n"
    playerlist = sorted(users.items(), key=lambda x: x[1].lower())
    for (playerid, playername) in playerlist:
        taggedplayer = "[{}](tg://user?id={})".format(playername, playerid)
        if playerid in admins:
            taggedplayer += " `[Admin]`"
        compose += "{}. {}\n".format(count, taggedplayer)
        count += 1
    responder(update, compose)


@useronly
def message_err(update, context):
    responder(
        update, "Are you trying to send a message to your angel or mortal? Type /message first.")


@run_async
def message_choice(update):
    update.message.reply_text("*Who do you want to send to?*\nSelect an option from the buttons below, or type a username.",
                              parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardMarkup([['My Mortal'], ['My Angel'], ['Exit']], resize_keyboard=True, one_time_keyboard=True))


@useronly
def message(update, context):
    user_id = str(update.message.from_user.id)
    mortal_id = mymortal.get(user_id)
    angel_id = myangel.get(user_id)
    if not mortal_id:
        responder(update, "You have not been assigned an angel/mortal.")
        return ConversationHandler.END
    else:
        context.user_data['mortal'] = int(mortal_id)
        context.user_data['angel'] = int(angel_id)
        message_choice(update)
    return TARGET


def invalid(update, context):
    if 'recipient' in context.user_data:
        responder(
            update, "_Unable to send this message to_ *{}*".format(context.user_data['recipient_name']))
        context.user_data.clear()
        responder(
            update, "*Exited messaging mode.*\nType /message again to send a message.")
        return ConversationHandler.END
    else:
        message_choice(update)
    return TARGET


def selectmortal(update, context):
    context.user_data['recipient'] = context.user_data['mortal']
    context.user_data['sender'] = 'Your Angel'
    context.user_data['recipient_name'] = users[str(
        context.user_data['recipient'])]
    responder(update, "I will send your messages (anonymously) to *{}* until you type /exit.".format(
        context.user_data['recipient_name']))
    context.bot.send_chat_action(
        chat_id=context.user_data['recipient'], action=telegram.ChatAction.TYPING)
    return CONTENT


def selectangel(update, context):
    context.user_data['recipient'] = context.user_data['angel']
    user_id = str(update.message.from_user.id)
    context.user_data['sender'] = users[user_id]
    context.user_data['recipient_name'] = 'Your Angel'
    responder(
        update, "I will send your messages (with your name) to *Your Angel* until you type /exit.")
    context.bot.send_chat_action(
        chat_id=context.user_data['recipient'], action=telegram.ChatAction.TYPING)
    return CONTENT


def selectplayer(update, context):
    context.user_data['sender'] = 'Anonymous'
    user_name = update.message.text
    user_name = user_name.strip('@')
    if user_name not in usernames:
        responder(update, "*Username not found.*")
        context.user_data.clear()
        time.sleep(0.05)
        responder(
            update, "*Exited messaging mode.*\nType /message again to send a message.")
        return ConversationHandler.END
    else:
        context.user_data['recipient'] = usernames[user_name]
        context.user_data['recipient_name'] = users[context.user_data['recipient']]
        responder(update, "I will send your messages (anonymously) to *{}* until you type /exit.".format(
            context.user_data['recipient_name']))
        context.bot.send_chat_action(
            chat_id=context.user_data['recipient'], action=telegram.ChatAction.TYPING)
        return CONTENT


@run_async
def message_out(update, context, msgtype):
    context.bot.send_message(
        chat_id=context.user_data['recipient'], text="_New {} from_ *{}* _below!_".format(msgtype, context.user_data['sender']), parse_mode=telegram.ParseMode.MARKDOWN)


@run_async
def message_in(update, context, msgtype):
    update.message.reply_text(
        "_{} sent to_ *{}*_!_".format(msgtype, context.user_data['recipient_name']), parse_mode=telegram.ParseMode.MARKDOWN)


def sendtext(update, context):
    message_out(update, context, 'message')
    time.sleep(0.05)
    text_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Message')
    return CONTENT


@run_async
def text_out(update, context):
    context.bot.send_message(
        chat_id=context.user_data['recipient'], text=update.message.text, parse_mode=telegram.ParseMode.MARKDOWN)


def sendphoto(update, context):
    message_out(update, context, 'photo')
    time.sleep(0.05)
    photo_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Photo')
    return CONTENT


@run_async
def photo_out(update, context):
    context.bot.send_photo(
        chat_id=context.user_data['recipient'], photo=update.message.photo[-1], caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendaudio(update, context):
    message_out(update, context, 'audio')
    time.sleep(0.05)
    audio_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Audio')
    return CONTENT


@run_async
def audio_out(update, context):
    context.bot.send_audio(
        chat_id=context.user_data['recipient'], audio=update.message.audio, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def senddocument(update, context):
    message_out(update, context, 'document')
    time.sleep(0.05)
    document_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Document')
    return CONTENT


@run_async
def document_out(update, context):
    context.bot.send_document(
        chat_id=context.user_data['recipient'], document=update.message.document, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendvideo(update, context):
    message_out(update, context, 'video')
    time.sleep(0.05)
    video_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Video')
    return CONTENT


@run_async
def video_out(update, context):
    context.bot.send_video(
        chat_id=context.user_data['recipient'], video=update.message.video, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendanimation(update, context):
    message_out(update, context, 'animation')
    time.sleep(0.05)
    animation_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Animation')
    return CONTENT


@run_async
def animation_out(update, context):
    context.bot.send_animation(
        chat_id=context.user_data['recipient'], animation=update.message.animation, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendvoice(update, context):
    message_out(update, context, 'voice')
    time.sleep(0.05)
    voice_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Voice')
    return CONTENT


@run_async
def voice_out(update, context):
    context.bot.send_voice(
        chat_id=context.user_data['recipient'], voice=update.message.voice, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendvideonote(update, context):
    message_out(update, context, 'video message')
    time.sleep(0.05)
    videonote_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Video message')
    return CONTENT


@run_async
def videonote_out(update, context):
    context.bot.send_video_note(
        chat_id=context.user_data['recipient'], video_note=update.message.video_note)


def sendsticker(update, context):
    message_out(update, context, 'sticker')
    time.sleep(0.05)
    sticker_out(update, context)
    time.sleep(0.05)
    message_in(update, context, 'Sticker')
    return CONTENT


@run_async
def sticker_out(update, context):
    context.bot.send_sticker(
        chat_id=context.user_data['recipient'], sticker=update.message.sticker)


def exit(update, context):
    context.user_data.clear()
    responder(
        update, "*Exited messaging mode.*\nType /message again to send a message.")
    return ConversationHandler.END


@adminonly
def reset(update, context):
    loader()
    responder(update, "_Reset complete._")


@useronly
def who(update, context):
    global requester
    try:
        requester
    except NameError:
        requester = None
    user_id = str(update.message.from_user.id)
    if requester != None and user_id == requester:
        responder(update, "_You cannot check your own angel!_")
    elif requester != None:
        mortal = user_id
        mortal = users.get(user_id)
        angel = myangel.get(user_id)
        angel = users.get(angel)
        flood(context, requester, "*{}*'s angel is *{}*.".format(mortal, angel))
        responder(
            update, "Your angel has been revealed to *{}*.".format(users[requester]))
        requester = None
    elif requester == None and user_id in admins:
        requester = user_id
        responder(update, "_Type /who on player's phone to check their angel._")
    else:
        responder(update, "`Unable to use this command.`")


@adminonly
def tester(update, context):
    user_id = str(update.effective_user.id)
    mymortal[user_id] = user_id
    myangel[user_id] = user_id
    responder(
        update, "You are now set as your own angel/mortal.\nUse /reset to undo.")


def main():
    updater = Updater(token=bottoken, workers=32, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('message', message)],
        states={
            TARGET: [MessageHandler(Filters.regex('^My Mortal$'),
                                    selectmortal),
                     MessageHandler(Filters.regex('^My Angel$'),
                                    selectangel),
                     MessageHandler(Filters.regex('^Exit$'),
                                    exit),
                     MessageHandler(Filters.regex('^@'), selectplayer)],
            CONTENT: [MessageHandler(Filters.regex('^/exit$'), exit),
                      MessageHandler(Filters.photo, sendphoto),
                      MessageHandler(Filters.audio, sendaudio),
                      MessageHandler(Filters.document, senddocument),
                      MessageHandler(Filters.video, sendvideo),
                      MessageHandler(Filters.animation, sendanimation),
                      MessageHandler(Filters.voice, sendvoice),
                      MessageHandler(Filters.video_note, sendvideonote),
                      MessageHandler(Filters.sticker, sendsticker),
                      MessageHandler(Filters.text, sendtext)]
        },
        fallbacks=[MessageHandler(Filters.all, invalid)]
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('join', join))
    dispatcher.add_handler(CommandHandler('leave', leave))
    dispatcher.add_handler(CommandHandler('botadmin', botadmin))
    dispatcher.add_handler(CommandHandler('newgame', newgame))
    dispatcher.add_handler(CommandHandler('endgame', endgame))
    dispatcher.add_handler(CommandHandler('broadcast', broadcast))
    dispatcher.add_handler(CommandHandler('cc', cc))
    dispatcher.add_handler(CommandHandler('players', players))
    dispatcher.add_handler(CommandHandler('reset', reset))
    dispatcher.add_handler(CommandHandler('who', who))
    dispatcher.add_handler(CommandHandler('tester', tester))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))
    dispatcher.add_handler(MessageHandler(Filters.all, message_err))

    loader()

    updater.start_polling()
    updater.start_webhook(listen='0.0.0.0',
                          port=port,
                          url_path=bottoken,
                          key='private.key',
                          cert='cert.pem',
                          webhook_url='https://{}:{}/{}'.format(ip, port, bottoken))

    print("Bot is running. Press Ctrl+C to stop.")
    print("Please wait for confirmation before closing.")
    updater.idle()
    print("Bot stopped successfully.")


if __name__ == '__main__':
    main()
