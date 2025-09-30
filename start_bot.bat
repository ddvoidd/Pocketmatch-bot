@echo off
chcp 65001
title PocketMatch Bot Manager
cd /d "%~dp0"

:menu
cls
echo ===============================
echo    POCKETMATCH BOT MANAGER
echo ===============================
echo.
echo [1] Запустить бота (обычный режим)
echo [2] Запустить бота (с восстановлением базы)
echo [3] Безопасный сброс лайков
echo [4] Полный сброс базы данных
echo [5] Создать резервную копию
echo [6] Просмотреть логи
echo [7] Выход
echo.
set /p choice="Выберите действие [1-7]: "

if "%choice%"=="1" goto start_normal
if "%choice%"=="2" goto start_recovery
if "%choice%"=="3" goto reset_likes
if "%choice%"=="4" goto reset_full
if "%choice%"=="5" goto backup
if "%choice%"=="6" goto view_logs
if "%choice%"=="7" goto exit
goto menu

:start_normal
cls
echo ===============================
echo    ЗАПУСК БОТА - ОБЫЧНЫЙ РЕЖИМ
echo ===============================
echo.
echo [INFO] Проверка базы данных...
if exist "dating_bot.db" (
    echo [INFO] База данных найдена
) else (
    echo [INFO] База данных не найдена, будет создана автоматически
)
echo.
echo [INFO] Запуск бота...
echo [INFO] Для остановки нажмите Ctrl+C
echo.
python bot.py
echo.
echo [INFO] Бот завершил работу
pause
goto menu

:start_recovery
cls
echo ===============================
echo    ЗАПУСК БОТА - ВОССТАНОВЛЕНИЕ
echo ===============================
echo.
echo [INFO] Проверка и восстановление базы данных...
python -c "
import sqlite3
import os

def init_database():
    '''Полная инициализация базы данных'''
    conn = sqlite3.connect('dating_bot.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Создаем таблицы если они не существуют
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            target_gender TEXT NOT NULL,
            city TEXT NOT NULL,
            bio TEXT,
            interests TEXT,
            photos TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            viewed BOOLEAN DEFAULT FALSE,
            created_at TEXT NOT NULL,
            FOREIGN KEY (from_user_id) REFERENCES users (user_id),
            FOREIGN KEY (to_user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    
    # Проверяем что все таблицы созданы
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
    tables = [row['name'] for row in cursor.fetchall()]
    required_tables = ['users', 'profiles', 'likes']
    
    for table in required_tables:
        if table not in tables:
            print(f'[ERROR] Таблица {table} не создана')
            conn.close()
            return False
    
    print('[SUCCESS] База данных проверена и восстановлена')
    conn.close()
    return True

if init_database():
    print('[INFO] База данных готова к работе')
else:
    print('[ERROR] Не удалось восстановить базу данных')
"
echo.
echo [INFO] Запуск бота...
echo [INFO] Для остановки нажмите Ctrl+C
echo.
python bot.py
echo.
echo [INFO] Бот завершил работу
pause
goto menu

:reset_likes
cls
echo ===============================
echo    БЕЗОПАСНЫЙ СБРОС ЛАЙКОВ
echo ===============================
echo.
if not exist "dating_bot.db" (
    echo [ERROR] База данных не найдена!
    pause
    goto menu
)

echo [INFO] Этот сброс очистит только историю лайков
echo [INFO] Профили пользователей останутся нетронутыми
echo.
choice /C YN /M "Продолжить (Y-да, N-нет)"
if errorlevel 2 goto menu

echo [INFO] Выполняю безопасный сброс лайков...
python -c "
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

def safe_clear_likes():
    try:
        conn = sqlite3.connect('dating_bot.db')
        cursor = conn.cursor()
        
        # Проверяем что таблица существует
        cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"likes\"')
        if not cursor.fetchone():
            print('[ERROR] Таблица likes не найдена в базе данных!')
            return False
        
        # Получаем количество лайков до очистки
        cursor.execute('SELECT COUNT(*) FROM likes')
        count_before = cursor.fetchone()[0]
        
        # Очищаем таблицу
        cursor.execute('DELETE FROM likes')
        conn.commit()
        
        # Проверяем что очистка прошла успешно
        cursor.execute('SELECT COUNT(*) FROM likes')
        count_after = cursor.fetchone()[0]
        
        print(f'[INFO] Лайков до очистки: {count_before}')
        print(f'[INFO] Лайков после очистки: {count_after}')
        
        if count_after == 0:
            print('[SUCCESS] История лайков успешно очищена!')
            return True
        else:
            print('[ERROR] Не все лайки были удалены')
            return False
            
    except Exception as e:
        print(f'[ERROR] Ошибка при очистке лайков: {e}')
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if safe_clear_likes():
    print('[INFO] Сброс выполнен успешно')
else:
    print('[ERROR] Сброс не выполнен')
"
echo.
pause
goto menu

:reset_full
cls
echo ===============================
echo    ПОЛНЫЙ СБРОС БАЗЫ ДАННЫХ
echo ===============================
echo.
if exist "dating_bot.db" (
    echo [WARNING] ВНИМАНИЕ! Это приведет к полному удалению:
    echo           - Всех профилей пользователей
    echo           - Истории лайков и мэтчей
    echo           - Настроек всех пользователей
    echo.
    choice /C YN /M "Вы уверены что хотите удалить ВСЕ данные (Y-да, N-нет)"
    if errorlevel 2 goto menu
    
    echo [INFO] Создаю резервную копию...
    if not exist "backups" mkdir "backups"
    set TIMESTAMP=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
    set TIMESTAMP=%TIMESTAMP: =0%
    copy "dating_bot.db" "backups\dating_bot_backup_%TIMESTAMP%.db"
    
    echo [INFO] Удаляю базу данных...
    del "dating_bot.db"
    if exist "dating_bot.db" (
        echo [ERROR] Не удалось удалить базу данных
    ) else (
        echo [SUCCESS] База данных удалена
        echo [INFO] Новая база будет создана при запуске бота
    )
) else (
    echo [INFO] База данных не найдена
)
echo.
pause
goto menu

:backup
cls
echo ===============================
echo    СОЗДАНИЕ РЕЗЕРВНОЙ КОПИИ
echo ===============================
echo.
if exist "dating_bot.db" (
    if not exist "backups" mkdir "backups"
    set TIMESTAMP=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
    set TIMESTAMP=%TIMESTAMP: =0%
    copy "dating_bot.db" "backups\dating_bot_backup_%TIMESTAMP%.db"
    if errorlevel 1 (
        echo [ERROR] Не удалось создать резервную копию
    ) else (
        echo [SUCCESS] Резервная копия создана: backups\dating_bot_backup_%TIMESTAMP%.db
    )
) else (
    echo [INFO] База данных не найдена
)
echo.
pause
goto menu

:view_logs
cls
echo ===============================
echo    ПРОСМОТР ЛОГОВ
echo ===============================
echo.
echo [INFO] Последние логи бота (если есть):
echo.
if exist "bot.log" (
    type "bot.log" | more
) else (
    echo Лог-файл не найден
    echo Логи выводятся в консоль при запуске бота
)
echo.
pause
goto menu

:exit
cls
echo ===============================
echo    ВЫХОД
echo ===============================
echo.
echo [INFO] До свидания!
timeout /t 2 >nul