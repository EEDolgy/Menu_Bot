import telepot
from telepot.loop import MessageLoop
from telepot.delegate import pave_event_space, per_chat_id, create_open, per_callback_query_chat_id
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import re
import Google_Drive
import BD
import os
import time

TOKEN = "YOUR TOKEN GOES HERE"
BOT_COMANDS = {'start': '/start',
               'menu': '/menu',
               'Mama': '/i_am_mama'}
QUESTIONS = []
WHOLE_MENU = 'Меню целиком'
LAST_MENU = 'Старое меню'
MAMA_ACTIONS = {'Update menu': 'Загрузить новое меню',
                'Update Google Drive': 'Обновить таблицы заказов и клиентов'}
CURRENT_DATES = []
PREVIOUS_DATES = []

class Info_Collector(telepot.helper.UserHandler):
    def __init__(self, *args, **kwargs):
        super(Info_Collector, self).__init__(*args, **kwargs)
        self.username = None
        self.meta_data = {'permission list': BD.get_permissions(),
                          'actual dates': BD.get_actual_dates(),
                          'previous dates': BD.get_previous_dates()}
        self.mama_permission = False

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if not self.username:
            self.username = msg['chat']['username']
            if 'first_name' in msg['chat'].keys():
                self.first_name = msg['chat']['first_name']
            else:
                self.first_name = ''
            if 'last_name' in msg['chat'].keys():
                self.last_name = msg['chat']['last_name']
            else:
                self.last_name = ''

            if self.username in self.meta_data['permission list']:
                self.mama_permission = True

        if content_type == 'text':
            txt = msg['text']
            if txt == BOT_COMANDS['start']:
                self.start()
            elif txt == BOT_COMANDS['menu']:
                self.menu()
            elif txt == BOT_COMANDS['make_order']:
                self.make_order()
            elif txt == BOT_COMANDS['Mama']:
                if self.mama_permission:
                    self.mama_stuff()
                else:
                    bot.sendMessage(self.user_id, f'You are not the Owner, you are - {self.first_name} {self.last_name} :) ')
            elif self.mama_permission:
                if 'forward_sender_name' in msg.keys():
                    username = msg['forward_sender_name']
                else:
                    username = 'Имя не указано'
                if 'forward_date' in msg.keys():
                    date = datetime.fromtimestamp(msg['forward_date']).strftime("%Y-%m-%d")
                else:
                    date = datetime.fromtimestamp(msg['date']).strftime("%Y-%m-%d")
                BD.add_single_extra_wish(date, txt, username)
                bot.sendMessage(self.user_id, 'The client\'s wish has been saved')
            else:
                bot.sendMessage(self.user_id, 'Sorry, I didn\'t get it =(')

    def on_callback_query(self, msg):
        query_id, from_id, txt = telepot.glance(msg, flavor='callback_query')

        if txt == WHOLE_MENU:
            for date in self.meta_data['actual dates']:
                self.show_day(date)
                time.sleep(2)
        elif txt == LAST_MENU:
            for date in self.meta_data['previous dates']:
                self.show_day(date)
                time.sleep(5)
        elif re.fullmatch(r'\d{2}\.\d{2}', txt):
            day_month = datetime.datetime.strptime(txt, '%d.%m')
            day = day_month.day
            month = day_month.month
            year = datetime.datetime.today().year
            date = datetime.datetime(year, month, day)
            self.show_day(date)
        elif re.fullmatch(r'.+ \d{2}\.\d{2} 1.*', txt):
            keyboard = InlineKeyboardMarkup(keyboard=[['Вы выбрали: Мясное 1 порция', InlineKeyboardButton(text='Изменить выбор', callback_data=f'change meat')]])
            bot.editMessageText(msg_identifier=telepot.message_identifier(msg), text='wtf')
        elif self.mama_permission:
            if txt == 'Update menu':
                bot.sendMessage(self.user_id, 'Добавляю новое меню. Пожалуйста, подождите...')
                Google_Drive.add_new_data_to_DB()
                bot.sendMessage(self.user_id, 'База данных успешно обновлена.')
            elif txt == 'Update Google Drive':
                bot.sendMessage(self.user_id, 'Обновляю таблицы с данными. Пожалуйста, подождите...')
                Google_Drive.update_clients_orders_wishes()
                bot.sendMessage(self.user_id, 'Таблицы успешно обновлены.')

    def start(self):
        message = BD.get_hello_message()
        bot.sendMessage(self.id, message)

    def menu(self):
        dates = self.meta_data['actual dates']
        middle_index = len(dates) // 2
        dates = [dates[:middle_index], dates[middle_index:]]

        dates_keyboard = [[InlineKeyboardButton(text=i.strftime("%d.%m"), callback_data=i.strftime("%d.%m")) for i in item] for item in dates]

        keyboard = InlineKeyboardMarkup(inline_keyboard=[dates_keyboard[0], dates_keyboard[1],
                   [InlineKeyboardButton(text='Актуальное меню целиком', callback_data=WHOLE_MENU)],
                   [InlineKeyboardButton(text='Предыдущее меню целиком', callback_data=LAST_MENU)]
               ])

        bot.sendMessage(self.user_id, 'Меню за какой день Вы хотели бы посмотреть?', reply_markup=keyboard)

    def mama_stuff(self):
        keyboard = [[InlineKeyboardButton(text=item[1], callback_data=item[0])] for item in MAMA_ACTIONS.items()]

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

        bot.sendMessage(self.user_id, 'Что Вы хотите сделать?', reply_markup=keyboard)

    def show_day(self, date):
        sql_date = date.strftime("%Y-%m-%d")
        date = date.strftime("%d.%m")

        output = BD.get_day_menu(sql_date)
        bot.sendMessage(self.user_id, date)
        bot.sendMessage(self.user_id, output['description'])
        bot.sendPhoto(self.user_id, photo=open(output['foto'], 'rb'))
        os.remove(output['foto'])

bot = telepot.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(),
        create_open, Info_Collector, per_callback_query_chat_id(),
        timeout=600),
])
MessageLoop(bot).run_forever()