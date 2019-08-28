import telegram
from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, Filters, ConversationHandler)
import logging
from functools import wraps
import random
from time import sleep
from cred import (bottoken, adminpass)

bot = telegram.Bot(token=bottoken)

logging.basicConfig(filename='debug.log', filemode='a+', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

TARGET, CONTENT = range(2)


def adminonly(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in adminlist:
            bot.send_message(
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


def start(update, context):
    update.message.reply_text(
        "*Welcome to YF Camp 2019!*\nPress /join to enter the Angel & Mortal bot.", parse_mode=telegram.ParseMode.MARKDOWN)


def unknown(update, context):
    update.message.reply_text(
        "*COMMANDS*\n/join - Join the game\n/message - Send messages\n\n*ADMIN COMMANDS*\n/yfcampcomm - Hmm...\n/newgame - Start game\n/endgame - Stop game\n/broadcast - Send to all campers", parse_mode=telegram.ParseMode.MARKDOWN)


def join(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat_id,
                                 action=telegram.ChatAction.TYPING)
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
            usernamedict[user_id] = user_name
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
    do_pairings()
    get_gamelist()
    update.message.reply_text("Sending everyone their mortal's names...")
    for user_id in mymortal:
        mortal_id = mymortal[user_id]
        mortal_name = userdict[mortal_id]
        bot.send_message(
            chat_id=user_id, text="Your mortal is: *{mortal}*\nUse /message to talk to them.".format(mortal=mortal_name), parse_mode=telegram.ParseMode.MARKDOWN)
        sleep(0.05)
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
        bot.send_message(
            chat_id=user_id, text="Your angel was: *{angel}*".format(angel=angel_name), parse_mode=telegram.ParseMode.MARKDOWN)
        sleep(0.05)
    update.message.reply_text("Game stopped!")


@adminonly
def broadcast(update, context):
    message = parse(update.message.text, len("broadcast"))
    if len(message) < 1:
        update.message.reply_text(
            "_Type your message after the command\ne.g._ /message Hello.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        for user_id in userdict:
            bot.send_message(
                chat_id=user_id, text="*BROADCAST FROM YF CAMP COMM:*\n{}".format(message), parse_mode=telegram.ParseMode.MARKDOWN)
            sleep(0.05)


@useronly
def message(update, context):
    user_id = update.message.from_user.id
    mortal_id = mymortal.get(user_id)
    angel_id = myangel.get(user_id)
    if (mortal_id == None) or (angel_id == None):
        update.message.reply_text(
            "You have not been assigned an angel/mortal.")
        return ConversationHandler.END
    else:
        context.user_data['mortal'] = mortal_id
        context.user_data['angel'] = angel_id
        update.message.reply_text("*Who do you want to send to?*\nSelect an option from the buttons below, or type a username.",
                                  parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardMarkup([['My Mortal'], ['My Angel'], ['Exit']], resize_keyboard=True, one_time_keyboard=True))
    return TARGET


def invalid(update, context):
    update.message.reply_text(
        "_I was not expecting this response. Please try again._", parse_mode=telegram.ParseMode.MARKDOWN)


def message_err(update, context):
    update.message.reply_text(
        "Are you trying to send a message to your angel or mortal? Type /message first.")


def selectmortal(update, context):
    context.user_data['recipient'] = context.user_data['mortal']
    context.user_data['sender'] = 'your angel'
    recipient_name = userdict[context.user_data['recipient']]
    update.message.reply_text(
        "I will anonymously send your messages to *{recipient}* until you type /exit.".format(recipient=recipient_name), parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardRemove())
    update.message.reply_text(
        "I only accept: Text, Stickers, Photos, Voice/Video Messages. Other files will not be sent.")
    return CONTENT


def selectangel(update, context):
    context.user_data['recipient'] = context.user_data['angel']
    user_id = update.message.from_user.id
    sender_name = userdict[user_id]
    context.user_data['sender'] = sender_name
    update.message.reply_text(
        "I will anonymously send your messages to *your angel* until you type /exit.", parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardRemove())
    update.message.reply_text(
        "I only accept: Text, Stickers, Photos, Voice/Video Messages. Other files will not be sent.")
    return CONTENT


def selectcamper(update, context):
    context.user_data['sender'] = 'Anonymous'
    user_name = update.message.text
    user_name = user_name.strip('@')
    if user_name not in usernamedict:
        update.message.reply_text(
            "*Username not found.*\nType /message again to send a message.", parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardRemove())
    else:
        recipient = usernamedict[user_name]
        context.user_data['recipient'] = recipient
        recipient_name = userdict[recipient]
        update.message.reply_text(
            "I will anonymously send your messages to *{}* until you type /exit.".format(recipient_name), parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardRemove())
        update.message.reply_text(
            "I only accept: Text, Stickers, Photos, Voice/Video Messages. Other files will not be sent.")
    return CONTENT


def sendtext(update, context):
    bot.send_message(
        chat_id=context.user_data['recipient'], text="New message from *{sender}* below!".format(sender=context.user_data['sender']), parse_mode=telegram.ParseMode.MARKDOWN)
    bot.send_message(
        chat_id=context.user_data['recipient'], text=update.message.text)
    update.message.reply_text(
        "_Message sent!_", parse_mode=telegram.ParseMode.MARKDOWN)
    return CONTENT


def sendphoto(update, context):
    bot.send_message(
        chat_id=context.user_data['recipient'], text="New photo from *{sender}* below!".format(sender=context.user_data['sender']), parse_mode=telegram.ParseMode.MARKDOWN)
    bot.send_photo(
        chat_id=context.user_data['recipient'], photo=update.message.photo[-1], caption=update.message.caption)
    update.message.reply_text(
        "_Photo sent!_", parse_mode=telegram.ParseMode.MARKDOWN)
    return CONTENT


def sendvoice(update, context):
    bot.send_message(
        chat_id=context.user_data['recipient'], text="New voice message from *{sender}* below!".format(sender=context.user_data['sender']), parse_mode=telegram.ParseMode.MARKDOWN)
    bot.send_voice(
        chat_id=context.user_data['recipient'], voice=update.message.voice)
    update.message.reply_text(
        "_Voice message sent!_", parse_mode=telegram.ParseMode.MARKDOWN)
    return CONTENT


def sendvideonote(update, context):
    bot.send_message(
        chat_id=context.user_data['recipient'], text="New video message from *{sender}* below!".format(sender=context.user_data['sender']), parse_mode=telegram.ParseMode.MARKDOWN)
    bot.send_video_note(
        chat_id=context.user_data['recipient'], video_note=update.message.video_note)
    update.message.reply_text(
        "_Video message sent!_", parse_mode=telegram.ParseMode.MARKDOWN)
    return CONTENT


def sendsticker(update, context):
    bot.send_message(
        chat_id=context.user_data['recipient'], text="New sticker from *{sender}* below!".format(sender=context.user_data['sender']), parse_mode=telegram.ParseMode.MARKDOWN)
    bot.send_sticker(
        chat_id=context.user_data['recipient'], sticker=update.message.sticker)
    update.message.reply_text(
        "_Sticker sent!_", parse_mode=telegram.ParseMode.MARKDOWN)
    return CONTENT


def exit(update, context):
    update.message.reply_text(
        "*Exited messaging mode.*\nType /message again to send a message.", parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=telegram.ReplyKeyboardRemove())
    return ConversationHandler.END


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


@adminonly
def tester(update, context):
    pass


def main():
    updater = Updater(
        token=bottoken, use_context=True)
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
    updater.idle()


if __name__ == '__main__':
    main()
