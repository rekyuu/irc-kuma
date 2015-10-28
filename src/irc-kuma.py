import auth
import os
import random
import re
import socket
import sys
import time
import sqlite3 as sql
from markov import Markov

DIR = os.path.dirname(os.path.realpath(__file__))
print(DIR)

"""
Helper functions.
"""

# Initiation.


def init():
    init_ops()


# Average output generator
def avg(list_):
    x = 0
    for i in list_:
        x += i
    return int(x / len(list_))


"""
Markov cleaning functions.
"""

# Characters that define what lines to ignore for the output
WEECHAT = ['>>', '<<', '--', '-->', '<--', '@Satsuki']
IGNORE = ['.luser', 'Raw', '!user', '.s']

# Counter of how many words are in a message to be averaged later
chat_average = {}


def chan_check(chan):
    log = '/home/bo1g/.weechat/logs/irc.animebytes.' + chan + '.weechatlog'
    if os.path.isfile(log) is True:
        return True
    elif os.path.isfile(log) is False:
        return False


def clean_file(file_):
    global chat_average

    word_count = []
    avg_words = 0

    """
	This will create a file of just user submitted messages.

	Weechat logs in the following format:

	YYYY-MM-DD HH:MM:SS USERNAME	MESSAGE
	YYYY-MM-DD HH:MM:SS << USERNAME (ADDRESS) has quit (REASON)
	"""
    chat_name = file_.split('/')[-1].split('.')[2]
    send_message(CHAN, "Just one second while refresh the logs.")
    print('[LOG] Creating clean output file for {0}.'.format(chat_name))

    file_i = open(file_, encoding="utf8").read().splitlines()
    file_o = open(
        DIR + '/__cache__/clean_log_{0}'.format(chat_name), 'w', encoding="utf8")

    for line in file_i:
        try:
            msg = line.split('	')  # Splits to [time / name / message] etc
            words = msg[2].split()  # Splits the message into words
            try:
                if msg[1] not in WEECHAT:
                    if len(msg[2].split('::')) == 1:
                        if words[0] not in IGNORE:
                            if words[0].split(':')[0] not in ['http', 'https']:
                                word_count.append(len(words))
                                words.append('\n')
                                file_o.write(' '.join(words))
            except:
                pass
        except:
            pass
    chat_average[chat_name] = avg(word_count)
    file_o.close()


def refresh(chat_name):
    global chat_average

    try:
        clean_file(
            '/home/bo1g/.weechat/logs/irc.animebytes.{0}.weechatlog'.format(chat_name))
        print('[LOG] Chat log file for {0} refreshed.'.format(chat_name))
    except FileNotFoundError:
        send_message(
            CHAN, "Sorry, either that log does not exist or you forgot to enter a parameter.")


def gen_markov(chat_name):
    global chat_average

    while True:
        try:
            with open(DIR + '/__cache__/clean_log_{0}'.format(chat_name), 'w', encoding="utf8") as f:
                markov = Markov(f)
                return markov.generate_markov_text(chat_average[chat_name] + random.randint(0, int(chat_average[chat_name] / 2)))
            break
        except FileNotFoundError:
            send_message(CHAN, "what????")
            break
        except:
            refresh(chat_name)


def gen_batch_markov(chat_name):
    print('[LOG] Creating batch lines for {0}.'.format(chat_name))
    with open(DIR + '/__cache__/markov_{0}'.format(chat_name), 'w', encoding="utf8") as f:
        for i in range(0, 100):
            out = gen_markov(chat_name)
            f.write('{0}\n'.format(out))


def return_markov(chat_name):
    lines = []
    rand = 0
    out = ''

    while True:
        try:
            with open(DIR + '/__cache__/markov_{0}'.format(chat_name), encoding="utf8") as f:
                lines = f.read().splitlines()
                if len(lines) == 0:
                    gen_batch_markov(chat_name)
                    lines = f.read().splitlines()

                rand = random.randint(0, len(lines))

                out = lines[rand]
                del lines[rand]

            with open(DIR + '/__cache__/markov_{0}'.format(chat_name), 'w', encoding="utf8") as f:
                for line in lines:
                    f.write('{0}\n'.format(line))

            return out
            break

        except FileNotFoundError:
            if chan_check(chat_name) is False:
                return "but nobody came"
                break
            else:
                gen_batch_markov(chat_name)


# Sends a markov message at random percentage rate.
def random_markov(x):
    rand = int(random.randint(1, 1000))
    x = int(x * 10)

    if rand <= x:
        chat = random.choice(["#animebytes", "#mango"])
        out = return_markov(chat)
        send_message(CHAN, out)

"""
Database functions.
"""

# Initializes ops.


def init_ops():
    global OPS

    con = sql.connect(DIR + '/__cache__/living_in_the_.db')

    with con:
        con.row_factory = sql.Row
        db = con.cursor()

        OPS = []
        db.execute('SELECT * FROM Ops;')
        rows = db.fetchall()

        for row in rows:
            OPS.append(row['Name'])

# Sends a message of current ops.


def get_ops():
    out = ', '.join(OPS)
    send_message(CHAN, "Current ops: {0}".format(out))

# Adds a new op.


def add_op(user):
    global OPS

    con = sql.connect(DIR + '/__cache__/living_in_the_.db')

    with con:
        con.row_factory = sql.Row
        db = con.cursor()

        try:
            if user not in OPS:
                db.execute(
                    "INSERT OR IGNORE INTO Ops(Name) VALUES('{0}');".format(user))
                OPS.append(user)
                send_message(
                    CHAN, "Added {0} to ops. They will be automatically opped from here on out.".format(user))
            else:
                send_message(CHAN, "That user is already an op!")
        except sql.Error as e:
            send_message(CHAN, "Unable to add user: {0}".format(e.args[0]))

    init_ops()

# Removes an op.


def delete_op(user):
    global OPS

    con = sql.connect(DIR + '/__cache__/living_in_the_.db')

    with con:
        con.row_factory = sql.Row
        db = con.cursor()

        try:
            if user in OPS:
                db.execute("DELETE FROM Ops WHERE Name='{0}';".format(user))
                OPS.remove(user)
                send_message(CHAN, "Removed {0} from ops.".format(user))
            else:
                send_message(CHAN, "That user does not exist!")
        except sql.Error as e:
            send_message(CHAN, "Unable to remove user: {0}".format(e.args[0]))

    init_ops()


"""
IRC functions.
"""

# IRC settings
HOST = "irc.animebytes.tv"
PORT = 6667
CHAN = "#mango"
NICK = "KumaKaiNi"
OPS = []
init()

# IRC commands


def send_pong(msg):
    irc.send(bytes('PONG %s\r\n' % msg, 'utf8'))


def send_message(chan, msg):
    irc.send(bytes('PRIVMSG %s :%s\r\n' % (chan, msg), 'utf8'))


def send_action(chan, msg):
    irc.send(bytes('PRIVMSG %s :\x01ACTION %s\x01\r\n' % (chan, msg), 'utf8'))


def send_mode(chan, mode, user):
    irc.send(bytes('MODE %s %s: %s\r\n' % (chan, mode, user), 'utf8'))


def send_nick(nick):
    irc.send(bytes('USER %s %s %s %s\n' % (nick, nick, nick, nick), 'utf8'))
    irc.send(bytes('NICK %s\n' % nick, 'utf8'))


def send_pass(password):
    irc.send(bytes('PASS %s\r\n' % password, 'utf8'))


def join_channel(chan):
    irc.send(bytes('JOIN %s\r\n' % chan, 'utf8'))


def part_channel(chan):
    irc.send(bytes('PART %s\r\n' % chan, 'utf8'))


# IRC chat functions
def get_sender(msg):
    result = ""
    for char in msg:
        if char == "!":
            break
        if char != ":":
            result += char
    return result


def get_message(msg):
    result = ""
    i = 3
    length = len(msg)
    while i < length:
        result += msg[i] + " "
        i += 1
    result = result.lstrip(':')
    return result


# Automod function.
def auto_op(username):
    send_mode(CHAN, "+o", username)


"""
IRC command definitions and functions.
"""


def send_help():
    out = "> .markov [#animebytes, #mango], .op [user], .deop [user], .getops"
    send_action(CHAN, out)


def send_markov(chat_name):
    out = return_markov(chat_name)
    send_message(CHAN, out)
    print("[OUT] " + out)

commands = {
    '.help': 	send_help,
    '.markov': 	send_markov
}


def parse_message(msg):
    msg = msg.split(' ')
    if len(msg) == 2:
        try:
            if msg[0] in commands:
                commands[msg[0]]()
        except:
            send_message(CHAN, 'That requires one additional argument!')
    elif len(msg) >= 3:
        if msg[0] in commands:
            commands[msg[0]](msg[1])


"""
IRC op command definitions and functions.
"""

commands_ops = {
    '.refresh':	refresh,
    '.op':		add_op,
    '.deop':	delete_op,
    '.getops': 	get_ops
}


def parse_message_ops(msg):
    msg = msg.split(' ')
    if len(msg) == 2:
        if msg[0] in commands_ops:
            commands_ops[msg[0]]()
    elif len(msg) >= 3:
        if msg[0] in commands_ops:
            commands_ops[msg[0]](msg[1])


"""
Server connection and listening.
"""

init()

irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
data = ""

irc.connect((HOST, PORT))
print("[LOG] Connected!")
send_nick(NICK)

data = ""
joined = False

while True:
    try:
        data = data + irc.recv(4096).decode('utf8')
        data_split = re.split(r"[~\r\n]+", data)
        data = data_split.pop()

        for line in data_split:
            line = str.rstrip(line)
            line = str.split(line)

            if len(line) >= 1:

                if line[0] == 'PING':
                    send_pong(line[1])

            if len(line) >= 2:

                if line[1] == 'MODE':
                    if joined == False:
                        send_message(
                            "NickServ", "IDENTIFY {0}".format(auth.PASS))
                        join_channel(CHAN)
                        joined = True
                        print("[LOG] Joined channel!")

                if line[1] == 'JOIN':
                    sender = get_sender(line[0])
                    if sender in OPS:
                        auto_op(sender)

                if line[1] == 'PRIVMSG':
                    sender = get_sender(line[0])
                    message = get_message(line)
                    print("[MSG] " + sender + ": " + message)

                    random_markov(0.5)

                    if sender in OPS:
                        parse_message_ops(message)
                    parse_message(message)

    except socket.error:
        print("[ERR] Socket died")
        raise

    except socket.timeout:
        print("[ERR] Socket timeout")
