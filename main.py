from config import token, API_KEY

from sqlite3 import connect, Error
from requests import get

from time import time
from datetime import timedelta, date

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup

from py_exchangeratesapi import Api, ExchangeRatesApiException


bot = TeleBot(token)
ftxt = ["Hello, i'm CurrencyBot!",
        "Enter your message in the format -> 10 USD CAD",
        "Enter a message in the format -> USD EUR"]


def APIrequest():
    try:
        res = get(f"http://api.exchangeratesapi.io/v1/latest?access_key={API_KEY}")    # &base=USD

        conn = connect("mydatabase.db")
        cursor = conn.cursor()
        curr = str(res.json()["rates"])
        dt = str(res.json()['date'])
        sec = int(time())

        cursor.execute("""CREATE TABLE IF NOT EXISTS currency (
                      id INTEGER NOT NULL PRIMARY KEY,
                      CURR text,
                      LASTDATE DATE,
                      SEC INT)
                   """)
        cursor.execute("INSERT INTO currency (CURR, LASTDATE, SEC) VALUES (?,?,?)", (curr, dt, sec))
        conn.commit()

        conn.close()

        return curr

    except Error as error:
        return f'Error APIrequest, {error}'


def datecheck():
    try:
        conn = connect("mydatabase.db")
        cursor = conn.cursor()

        _date = cursor.execute("SELECT SEC from currency").fetchall()[-1]

        conn.close()

        if _date[0] + 600 <= int(time()):
            print('Прошло > 10 минут')
            return True
        return False

    except:
        return 'Datecheck Err'


@bot.message_handler(commands=['start'])
def handle_text(message):
    button = ReplyKeyboardMarkup(True, False)
    button.row('/lst')
    button.row('/exchange', '/history')
    if message.text == '/start':
        bot.send_message(message.from_user.id, ftxt[0], reply_markup=button)


@bot.message_handler(commands=['lst', 'exchange', 'history'])
def lst(message):
    if message.text == '/lst':
        if datecheck() == True:
            bot.send_message(message.from_user.id, APIrequest())
        else:
            conn = connect("mydatabase.db")
            cursor = conn.cursor()

            _date = cursor.execute("SELECT CURR from currency").fetchall()[-1]

            conn.close()
            bot.send_message(message.from_user.id, str(_date))

    if message.text == '/exchange':
        sent = bot.send_message(message.from_user.id, ftxt[1])
        bot.register_next_step_handler(sent, exchange)

    if message.text == '/history':
        sent = bot.send_message(message.from_user.id, ftxt[2])
        bot.register_next_step_handler(sent, history)


def exchange(message):
    try:
        api = Api(API_KEY)
        mes = message.text.split(' ')

        bot.send_message(message.from_user.id, str(api.convert(int(mes[0]), mes[1], mes[2])))

    except ExchangeRatesApiException as err:
        bot.send_message(message.from_user.id, str(err))


def history(message):
    try:
        mes = message.text.split(' ')

        end_date = date.today()
        start_date = end_date + timedelta(days=-7)

        res = get(f"http://api.exchangeratesapi.io/v1/history?access_key={API_KEY}&start_at={str(start_date)}&end_at={str(end_date)}&base={mes[0]}&symbols={mes[-1]}")
        # res = api.get_rates(target_list=[mes[0], mes[-1]],
        #                     start_date=str(start_date),
        #                     end_date=str(end_date))
        print(res.text)
        result = res.json()['rates']

        bot.send_message(message.from_user.id, result)

    except KeyError or ExchangeRatesApiException as err:
        bot.send_message(message.from_user.id, str(err))



if __name__ == '__main__':
    bot.polling()