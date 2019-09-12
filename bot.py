import telegram.bot
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, ConversationHandler)
from telegram.ext.dispatcher import run_async
import logging
from functools import wraps
import random
import time
from cred import bottoken, adminpass

logging.basicConfig(filename='debug.log', filemode='a+', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

TARGET, CONTENT = range(2)


def get_users():
    global userdict
    with open('users.txt', 'a+') as userfile:
        userdict = {}
    with open('users.txt', 'r') as userfile:
        for line in userfile:
            line = line.strip('\n')
            line = line.split(',')
            userdict[int(line[0])] = line[1]


def get_usernames():
    global usernamedict
    with open('usernames.txt', 'a+') as usernamefile:
        usernamedict = {}
    with open('usernames.txt', 'r') as usernamefile:
        for line in usernamefile:
            line = line.strip('\n')
            line = line.split(',')
            usernamedict[line[0]] = int(line[1])


def get_admin():
    global adminlist
    with open('admin.txt', 'a+') as adminfile:
        adminlist = []
    with open('admin.txt', 'r') as adminfile:
        for line in adminfile:
            line = line.strip('\n')
            adminlist.append(int(line))


def get_gamelist():
    global mymortal
    global myangel
    with open('mymortal.txt', 'a+') as mortalfile:
        mymortal = {}
    with open('myangel.txt', 'a+') as angelfile:
        myangel = {}
    with open('mymortal.txt', 'r') as mortalfile:
        for line in mortalfile:
            line = line.strip('\n')
            line = line.split(',')
            mymortal[int(line[0])] = int(line[1])
    with open('myangel.txt', 'r') as angelfile:
        for line in angelfile:
            line = line.strip('\n')
            line = line.split(',')
            myangel[int(line[0])] = int(line[1])


def parse(text, length):
    start = int(length) + 2
    message = text[start:]
    return message


def adminonly(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in adminlist:
            context.bot.send_message(
                chat_id=user_id, text="*CAMP COMM ONLY*\nYou shall not pass!", parse_mode=telegram.ParseMode.MARKDOWN)
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def useronly(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in userdict:
            context.bot.send_message(
                chat_id=user_id, text="Please /join first.")
            return
        return func(update, context, *args, **kwargs)
    return wrapped


@run_async
def start(update, context):
    update.message.reply_text(
        "*Welcome to YF Camp 2019!*\nPress /join to enter the Angel & Mortal bot.", parse_mode=telegram.ParseMode.MARKDOWN)


@run_async
def unknown(update, context):
    commands = '''
*COMMANDS*
/join - Join the game
/message - Send messages
/cc - Message to Camp Comm

*ADMIN COMMANDS*
/yfcampcomm - Hmm...
/newgame - Start game
/endgame - Stop game
/broadcast - Send to all campers
/players - List of all players
/reset - Reloads lists from file
/tester - Do not touch!
    '''
    update.message.reply_text(commands, parse_mode=telegram.ParseMode.MARKDOWN)


def join(update, context):
    context.bot.send_chat_action(
        chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    user_id = update.message.from_user.id
    if user_id in userdict:
        update.message.reply_text(
            "You are already in the list.\nPress /help for info on commands.")
    else:
        user_first = update.message.from_user.first_name
        user_last = update.message.from_user.last_name
        if user_last != None:
            user_first = user_first + ' ' + user_last
        with open('users.txt', 'a+') as userfile:
            userfile.write("{},{}\n".format(user_id, user_first))
        userdict[user_id] = user_first
        user_name = update.message.from_user.username
        if user_name != None:
            with open('usernames.txt', 'a+') as usernamefile:
                usernamefile.write("{},{}\n".format(user_name, user_id))
            usernamedict[user_name] = user_id
        update.message.reply_text(
            "Your name has been added to the list.\nPress /help for info on commands.")


@useronly
def yfcampcomm(update, context):
    user_id = update.message.from_user.id
    if user_id in adminlist:
        update.message.reply_text("You are already an admin!")
    else:
        message = parse(update.message.text, len("yfcampcomm"))
        if message == adminpass:
            with open('admin.txt', 'a+') as adminfile:
                adminfile.write("{}\n".format(user_id))
                adminlist.append(user_id)
            update.message.reply_text("You are now an admin!")
        else:
            update.message.reply_text("Nope.")


@adminonly
def newgame(update, context):
    update.message.reply_text("Randomising angels & mortals...")
    if len(userdict) < 2:
        update.message.reply_text("Error! Only 1 player.")
        return None
    do_pairings()
    get_gamelist()
    update.message.reply_text("Sending everyone their mortal's names...")
    for user_id in mymortal:
        mortal_id = mymortal[user_id]
        mortal_name = userdict[mortal_id]
        address = user_id
        msg = "Your mortal is: *{mortal}*\nUse /message to talk to them.".format(
            mortal=mortal_name)
        flood(context, address, msg)
        time.sleep(0.05)
    update.message.reply_text("Game started!")


def shuffle():
    list1 = []
    list2 = []
    for user_id in userdict:
        list1.append(user_id)
        list2.append(user_id)
    random.shuffle(list1)
    random.shuffle(list2)
    for i in range(len(list1)):
        if list1[i] == list2[i]:
            return True
    with open('mymortal.txt', 'w') as mortalfile:
        with open('myangel.txt', 'w') as angelfile:
            for i in range(len(list1)):
                mortalfile.write("{},{}\n".format(list1[i], list2[i]))
                angelfile.write("{},{}\n".format(list2[i], list1[i]))
    return False


def do_pairings():
    result = shuffle()
    while result:
        result = shuffle()


@adminonly
def endgame(update, context):
    update.message.reply_text("Revealing angels & mortals...")
    for user_id in myangel:
        angel_id = myangel[user_id]
        angel_name = userdict[angel_id]
        address = user_id
        msg = "Your angel was: *{angel}*".format(angel=angel_name)
        flood(context, address, msg)
        time.sleep(0.05)
    update.message.reply_text("Game stopped!")


@adminonly
def broadcast(update, context):
    message = parse(update.message.text, len("broadcast"))
    if len(message) < 1:
        update.message.reply_text(
            "_Type your message after the command\ne.g._ /broadcast Hello.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        for user_id in userdict:
            address = user_id
            msg = "*BROADCAST FROM YF CAMP COMM:*\n{}".format(message)
            flood(context, address, msg)
            time.sleep(0.05)
        update.message.reply_text(
            "_Broadcast sent!_", parse_mode=telegram.ParseMode.MARKDOWN)


@useronly
def cc(update, context):
    message = parse(update.message.text, len("cc"))
    if len(message) < 1:
        update.message.reply_text(
            "_Type your message after the command\ne.g._ /cc Hello.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        user_id = update.message.from_user.id
        sender_name = userdict[user_id]
        for user_id in adminlist:
            address = user_id
            msg = "*Message to Camp Comm from {}:*\n{}".format(
                sender_name, message)
            flood(context, address, msg)
            time.sleep(0.05)
        update.message.reply_text(
            "_Message sent to Camp Comm!_", parse_mode=telegram.ParseMode.MARKDOWN)


@run_async
def flood(context, address, msg):
    context.bot.send_message(chat_id=address, text=msg,
                             parse_mode=telegram.ParseMode.MARKDOWN)


@adminonly
def players(update, context):
    context.bot.send_chat_action(
        chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    count = 1
    playerlist = "*Players:*\n"
    for playername in userdict.values():
        playerlist += "{}. {}\n".format(count, playername)
        count += 1
    update.message.reply_text(
        playerlist, parse_mode=telegram.ParseMode.MARKDOWN)


@useronly
def message_err(update, context):
    responder(
        update, "Are you trying to send a message to your angel or mortal? Type /message first.")


@useronly
def message(update, context):
    user_id = update.message.from_user.id
    mortal_id = mymortal.get(user_id)
    angel_id = myangel.get(user_id)
    if (mortal_id == None) or (angel_id == None):
        responder(update, "You have not been assigned an angel/mortal.")
        return ConversationHandler.END
    else:
        context.user_data['mortal'] = mortal_id
        context.user_data['angel'] = angel_id
        update.message.reply_text("*Who do you want to send to?*\nSelect an option from the buttons below, or type a username.",
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardMarkup([['My Mortal'], ['My Angel'], ['Exit']], resize_keyboard=True, one_time_keyboard=True))
        return TARGET


@run_async
def responder(update, msg):
    update.message.reply_text(msg, parse_mode=telegram.ParseMode.MARKDOWN,
                              reply_markup=telegram.ReplyKeyboardRemove())


def invalid(update, context):
    if 'recipient' in context.user_data:
        responder(
            update, "_Unable to send this message to_ *{}*".format(context.user_data['recipient_name']))
        context.user_data.clear()
        responder(
            update, "*Exited messaging mode.*\nType /message again to send a message.")
        return ConversationHandler.END
    else:
        update.message.reply_text("*Who do you want to send to?*\nSelect an option from the buttons below, or type a username.",
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardMarkup([['My Mortal'], ['My Angel'], ['Exit']], resize_keyboard=True, one_time_keyboard=True))
        return TARGET


def selectmortal(update, context):
    context.user_data['recipient'] = context.user_data['mortal']
    context.user_data['sender'] = 'Your Angel'
    context.user_data['recipient_name'] = userdict[context.user_data['recipient']]
    responder(update, "I will send your messages (anonymously) to *{}* until you type /exit.".format(
        context.user_data['recipient_name']))
    context.bot.send_chat_action(
        chat_id=context.user_data['recipient'], action=telegram.ChatAction.TYPING)
    return CONTENT


def selectangel(update, context):
    context.user_data['recipient'] = context.user_data['angel']
    user_id = update.message.from_user.id
    sender_name = userdict[user_id]
    context.user_data['sender'] = sender_name
    context.user_data['recipient_name'] = 'Your Angel'
    responder(
        update, "I will send your messages (with your name) to *Your Angel* until you type /exit.")
    context.bot.send_chat_action(
        chat_id=context.user_data['recipient'], action=telegram.ChatAction.TYPING)
    return CONTENT


def selectcamper(update, context):
    context.user_data['sender'] = 'Anonymous'
    user_name = update.message.text
    user_name = user_name.strip('@')
    if user_name not in usernamedict:
        responder(update, "*Username not found.*")
        context.user_data.clear()
        responder(
            update, "*Exited messaging mode.*\nType /message again to send a message.")
        return ConversationHandler.END
    else:
        context.user_data['recipient'] = usernamedict[user_name]
        context.user_data['recipient_name'] = userdict[context.user_data['recipient']]
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
    text_out(update, context)
    message_in(update, context, 'Message')
    return CONTENT


@run_async
def text_out(update, context):
    context.bot.send_message(
        chat_id=context.user_data['recipient'], text=update.message.text)


def sendphoto(update, context):
    message_out(update, context, 'photo')
    photo_out(update, context)
    message_in(update, context, 'Photo')
    return CONTENT


@run_async
def photo_out(update, context):
    context.bot.send_photo(
        chat_id=context.user_data['recipient'], photo=update.message.photo[-1], caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendaudio(update, context):
    message_out(update, context, 'audio')
    audio_out(update, context)
    message_in(update, context, 'Audio')
    return CONTENT


@run_async
def audio_out(update, context):
    context.bot.send_audio(
        chat_id=context.user_data['recipient'], audio=update.message.audio, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def senddocument(update, context):
    message_out(update, context, 'document')
    document_out(update, context)
    message_in(update, context, 'Document')
    return CONTENT


@run_async
def document_out(update, context):
    context.bot.send_document(
        chat_id=context.user_data['recipient'], document=update.message.document, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendvideo(update, context):
    message_out(update, context, 'video')
    video_out(update, context)
    message_in(update, context, 'Video')
    return CONTENT


@run_async
def video_out(update, context):
    context.bot.send_video(
        chat_id=context.user_data['recipient'], video=update.message.video, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendanimation(update, context):
    message_out(update, context, 'animation')
    animation_out(update, context)
    message_in(update, context, 'Animation')
    return CONTENT


@run_async
def animation_out(update, context):
    context.bot.send_animation(
        chat_id=context.user_data['recipient'], animation=update.message.animation, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendvoice(update, context):
    message_out(update, context, 'voice')
    voice_out(update, context)
    message_in(update, context, 'Voice')
    return CONTENT


@run_async
def voice_out(update, context):
    context.bot.send_voice(
        chat_id=context.user_data['recipient'], voice=update.message.voice, caption=update.message.caption, parse_mode=telegram.ParseMode.MARKDOWN)


def sendvideonote(update, context):
    message_out(update, context, 'video message')
    videonote_out(update, context)
    message_in(update, context, 'Video message')
    return CONTENT


@run_async
def videonote_out(update, context):
    context.bot.send_video_note(
        chat_id=context.user_data['recipient'], video_note=update.message.video_note)


def sendsticker(update, context):
    message_out(update, context, 'sticker')
    sticker_out(update, context)
    message_out(update, context, 'Sticker')
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
    get_users()
    get_usernames()
    get_admin()
    get_gamelist()
    update.message.reply_text(
        "_Reset complete._", parse_mode=telegram.ParseMode.MARKDOWN)


@adminonly
def tester(update, context):
    user_id = update.effective_user.id
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
                     MessageHandler(Filters.regex('^@'), selectcamper)],
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

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    join_handler = CommandHandler('join', join)
    dispatcher.add_handler(join_handler)
    yfcampcomm_handler = CommandHandler('yfcampcomm', yfcampcomm)
    dispatcher.add_handler(yfcampcomm_handler)
    newgame_handler = CommandHandler('newgame', newgame)
    dispatcher.add_handler(newgame_handler)
    endgame_handler = CommandHandler('endgame', endgame)
    dispatcher.add_handler(endgame_handler)
    broadcast_handler = CommandHandler('broadcast', broadcast)
    dispatcher.add_handler(broadcast_handler)
    cc_handler = CommandHandler('cc', cc)
    dispatcher.add_handler(cc_handler)
    players_handler = CommandHandler('players', players)
    dispatcher.add_handler(players_handler)
    reset_handler = CommandHandler('reset', reset)
    dispatcher.add_handler(reset_handler)
    tester_handler = CommandHandler('tester', tester)
    dispatcher.add_handler(tester_handler)
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)
    message_handler = MessageHandler(Filters.all, message_err)
    dispatcher.add_handler(message_handler)

    get_users()
    get_usernames()
    get_admin()
    get_gamelist()

    updater.start_polling()
    print("Bot is running. Press Ctrl+C to stop.")
    print("Please wait for confirmation before closing.")
    updater.idle()
    print("Bot stopped successfully.")


if __name__ == '__main__':
    main()
