from mimetypes import init
import kivy
import kivymd
import logging
import sys
import csv
import os
import time
import pathlib
import pickle
import random
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import PeerFloodError
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.types import InputPeerEmpty
from kivymd.app import MDApp
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivymd.uix.screen import MDScreen
from kivymd.uix.recycleview import RecycleView
from kivy.config import Config
from configparser import ConfigParser
from kivy.resources import resource_add_path, resource_find
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton

# Global Window Settings
Window.size =[480,480]

# Path variables
config_path = pathlib.Path(__file__).parent.absolute() / "daten" / "config.ini"
logging_path = pathlib.Path(__file__).parent.absolute()/ "daten" /  "log.txt"
dir_name = pathlib.Path(__file__).parent.absolute() 

# Config file
config_parser = ConfigParser()
config_parser.read(str(config_path))
api_id = config_parser.getint('account1', 'api_id')
api_hash = config_parser.get('account1', 'api_hash')
phone = config_parser.get('account1', 'phone')
error_timer = config_parser.getint('settings', 'error_time')

# Logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%m-%d-%Y %H:%M:%S')
handler = logging.FileHandler(str(logging_path))
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.info('Starting...')

# Global variables
chats = []
last_date = None
chunk_size = 200
groups=[]
i=0
users = []
folder_selected = False
called_safe = False
called_normal = False
called_rapid = False
safe_mode = False
normal_mode = False
rapid_mode = False
SLEEP_TIME = 61

# Clear last session
try:
    for item in os.listdir(dir_name):
        if item.endswith(".session"):
            os.remove(os.path.join(dir_name, item))
except Exception as e:
    logger.error(e)
    pass

# Telegram client
try:
    client = TelegramClient(phone, api_id, api_hash)
    client.connect()
except Exception as e:
    logger.error(e)
    sys.exit(1)

def zähl():
    global i
    i = i + 1
    return i

def get_groups():
    global groups
    result = client(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=chunk_size,
                hash = 0
            ))
    chats.extend(result.chats)

    for chat in chats:
        try:
            if chat.megagroup== True:
                groups.append(chat)
        except:
            continue
class MyToggleButton(MDFlatButton, MDToggleButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background_down = self.theme_cls.primary_color

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)

class main_screen(MDScreen):
    def anmelden(self):
        logging.debug("MainMenu.anmelden()")
        if not client.is_user_authorized():
            try:
                client.send_code_request(phone)
                self.manager.current = 'auth_s'
            except Exception as e:
                logging.debug("MainMenu.anmelden() - Fehler")
                logging.debug(e)
        else:
            get_groups()
            self.manager.current = 'group_s'
    pass
    
    def kacken(self):
        print("kacken")



class group_screen(MDScreen):

    def refresh_data(self):
        global i
        self.ids.rv.data = [{'text':"Nr. "+str(i)+" || "+ x.title, "on_press": zähl(), "outline_color": [1,1,1]} for x in groups]
        i = 0
    
    def get_members(self, value):
        try:
            target_group=groups[int(value)]
            all_participants = []
            all_participants = client.get_participants(target_group, aggressive=False, limit=2000)
            with open("member.csv","w",encoding='UTF-8') as f:
                writer = csv.writer(f,delimiter=",",lineterminator="\n")
                writer.writerow(['username','user id', 'access hash','name','group', 'group id'])
                for user in all_participants:
                    if user.username:
                        username= user.username
                    else:
                        username= ""
                    if user.first_name:
                        first_name= user.first_name
                    else:
                        first_name= ""
                    if user.last_name:
                        last_name= user.last_name
                    else:
                        last_name= ""
                    name= (first_name + ' ' + last_name).strip()
                    writer.writerow([username,user.id,user.access_hash,name,target_group.title, target_group.id])
                input_file = "member.csv"
                with open(input_file, encoding='UTF-8') as f:
                    rows = csv.reader(f,delimiter=",",lineterminator="\n")
                    next(rows, None)
                    for row in rows:
                        user = {}
                        user['username'] = row[0]
                        user['user id'] = int(row[1])
                        user['access hash'] = int(row[2])
                        user['name'] = row[3]
                        users.append(user)
                for admins in client.iter_participants(groups[int(1)], filter=ChannelParticipantsAdmins):
                    for user in users:
                        if admins.id == user['user id']:
                            print("Admin entfernt: ", user['name'])
                            users.remove(user)
            pickle.dump(users, open("users.p", "wb"))
            self.manager.current = 'send_s'

        except Exception as e:
            logging.debug("GruppenScreen.get_members() - Fehler")
            logging.debug(e)
        
    def load_members(self):
        global users
        try:
            users = pickle.load(open("users.p", "rb"))
            self.manager.current = 'send_s'
        except Exception as e:
            logging.debug("GruppenScreen.load_members() - Fehler")
            logging.debug(e)

class settings_screen(MDScreen):

    def safe_settings(self, value1, value2, value3):
        if value1 and value2 and value3:
            config_parser.set('account1', 'api_id', value1)
            config_parser.set('account1', 'api_hash', value2)
            config_parser.set('account1', 'phone', value3)
            with open(str(config_path), 'w') as configfile:
                config_parser.write(configfile)
            logger.info('Settings saved')
            sys.exit()
        else:
            logger.info('Settings not saved')
            self.manager.current = 'main_s'
        pass

    def show_settings(self):
        self.ids.api_id.text = config_parser.get('account1', 'api_id')
        self.ids.api_hash.text = config_parser.get('account1', 'api_hash')
        self.ids.phone.text = config_parser.get('account1', 'phone')
        pass
    
    def switch_normal(self):
        global called_normal, normal_mode
        if called_normal == False:
            normal_mode = True
            called_normal = True
            logger.info('Normal mode wurde aktiviert')
        elif called_normal == True:
            normal_mode = False
            called_normal = False
            logger.info('Normal mode wurde deaktiviert')

    def switch_safe(self):
        global called_safe, safe_mode
        if called_safe == False:
            safe_mode = True
            called_safe = True
            logger.info('Safe mode wurde aktiviert')
        elif called_safe == True:
            safe_mode = False
            called_safe = False
            logger.info('Safe mode wurde deaktiviert')
    
    def switch_rapid(self):
        global called_rapid, rapid_mode
        if called_rapid == False:
            rapid_mode = True
            called_rapid = True
            logger.info('Rapid mode wurde aktiviert')
        elif called_rapid == True:
            rapid_mode = False
            called_rapid = False
            logger.info('Rapid mode wurde deaktiviert')

class send_screen(MDScreen):
    global SLEEP_TIME

    def text(self, message):
        try:
            for user in users:
                if safe_mode == True:
                    SLEEP_TIME = int(random.uniform(60, 120))
                elif rapid_mode == True:
                    SLEEP_TIME = int(random.uniform(1, 5))
                else:
                    SLEEP_TIME = int(random.uniform(30, 60))
                receiver = InputPeerUser(user['user id'],user['access hash'])
                try:
                    print("Sende Nachricht an ", user['name'])                    
                    client.send_message(receiver, message.format(user['name']))
                    print("Warte {} sekunden".format(SLEEP_TIME))
                    del users[users.index(user)]
                    pickle.dump(users, open("users.p", "wb"))
                    time.sleep(SLEEP_TIME)
                except PeerFloodError:
                    print(f"""Ich bekomme einen FloodError von Telegram, zu viele anfragen wurden gesendet mit: {phone}
                    Bitte warte 24h und versuche es erneut
                    Oder verwende ein anderes Telegram Konto""")                    
                    print("Warte {} sekunden".format(error_timer))
                    self.manager.current = 'send_s'
                    client.disconnect()
                    break
                except Exception as e:
                    print("Error:", e)
                    print("Nachricht konnte nicht gesendet werden")
                    self.manager.current = 'send_s'
                    break
        except Exception as e:  
            logging.error(e)
            pass
    
    def send_bild(self, caption):
        global SLEEP_TIME
        if caption == "":
            try:
                for user in users:
                        if normal_mode == True:
                            SLEEP_TIME = int(random.uniform(30, 60))
                        elif safe_mode == True:
                            SLEEP_TIME = int(random.uniform(60, 120))
                        elif rapid_mode == True:
                            SLEEP_TIME = int(random.uniform(1, 5))
                        try:
                            print("Sende Bild an: ", user['username'])
                            client.send_file(user['user id'], folder_selected, caption=caption)
                            del users[users.index(user)]
                            pickle.dump(users, open("users.p", "wb"))
                            print("Warte {} sekunden".format(SLEEP_TIME))
                            time.sleep(SLEEP_TIME)
                        except PeerFloodError:
                            print(f"""Ich bekomme einen FloodError von Telegram, zu viele anfragen wurden gesendet mit: {phone}
                            Bitte warte 24h und versuche es erneut
                            Oder verwende ein anderes Telegram Konto""")
                            print("Warte {} sekunden".format(error_timer))
                            self.manager.current = 'send_s'
                            client.disconnect()
                            break
                        except Exception as e:
                            print("Error:", e)
                            print("Nachricht konnte nicht gesendet werden")
                            self.manager.current = 'send_s'
                            break
            except Exception as e:
                logging.error(e)
                pass
    
    pass

class datei_screen(MDScreen):
    global SLEEP_TIME

    def file_selected(self, value):
        global folder_selected
        folder_selected = value[0]
        print(folder_selected+" wurde ausgewählt")
        pass
    def load_folder(self):
        self.ids.file_label.text = "Datei: "+folder_selected+" wurde ausgewählt"
    pass

class auth_screen(MDScreen):
    def load_number(self):
        self.ids.code_label.text = "Code wurde an " + config_parser.get('account1', 'phone') + " gesendet"
        pass
    
    def code_senden(self, code):
        try:
            logging.debug("AuthScreen.code_senden()")
            client.sign_in(phone, code)
            get_groups()
            self.manager.current = 'group_s'
        except Exception as e:
            logging.error(e)
            pass
    pass

class myApp(MDApp):

    def build(self):
        sm = ScreenManager()
        sm.add_widget(main_screen(name='main_s'))
        sm.add_widget(group_screen(name='group_s'))
        sm.add_widget(settings_screen(name='settings_s'))
        sm.add_widget(send_screen(name='send_s'))
        sm.add_widget(datei_screen(name='datei_s'))
        sm.add_widget(auth_screen(name='auth_s'))
        return sm


if __name__ == '__main__':
    myApp().run()
