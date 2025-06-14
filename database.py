import sqlite3
import os
import json
from contextlib import closing
from typing import List, Dict, Tuple, Optional, Any
from datetime import date, datetime, timedelta

DB_PATH = "static/data/data.db"
CABINETS_PATH = "static/data/cabinets/"
CABINETS_DESC_PATH = "static/data/descriptions/"



def get_user(user_id):
    conn = sqlite3.connect("static/data/data.db")
    cursor = conn.cursor()
    user_data = cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return user_data

def login_user(username):
    conn = sqlite3.connect("static/data/data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password_hash FROM users WHERE login = ?", (username,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data


def add_user(data):
    conn = sqlite3.connect("static/data/data.db")
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO users (name, surname, patronymic, login, email, password_hash) VALUES (?, ?, ?, ?, ?, ?)""", (
        data['name'], data['surname'], data['patronymic'],
        data['username'], data['email'], data['password']
    ))
    conn.commit()
    conn.close()


def add_book(data, name, user_id):
    conn = sqlite3.connect("static/data/data.db")
    cursor = conn.cursor()
    
    d = datetime(int(data['date'][:4]), int(data['date'][5:7]), int(data['date'][8:]))
    week_day = d.weekday()
    if week_day == 6:
        return -1
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    day = day_names[week_day]
    file_path = "static/data/cabinets/cab" + data['cab_num'] + ".json"
    schedule_list = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            cabinet_data = json.load(file)
            schedule_list = cabinet_data
    except Exception as e:
        print(f"⚠️ Ошибка в файле {file_path}: {str(e)}")
    for i in range(1, 11):
        if str(i) in data.keys():
            if schedule_list[day][i] != "свободен":
                return -1
    
    for i in range(1, 11):
        if str(i) in data.keys():
            books = cursor.execute("""
                SELECT 
                    id
                FROM books 
                WHERE cab_id = ? AND date = ? AND lesson = ?
            """, (data['cab_num'], data['date'], i)).fetchone()
            if books != None:
                return -1
    
    for i in range(1, 11):
        if str(i) in data.keys():
            cursor.execute(
                """INSERT INTO books (name, cab_id, date, pers_id, lesson, type) VALUES (?, ?, ?, ?, ?, ?)""", (
                name, data['cab_num'], data['date'],
                user_id, i, data['type']
                ))
    conn.commit()
    conn.close()
    return 0

def delete_booking(date: str, cab_num: int, lesson: int):
    conn = sqlite3.connect("static/data/data.db")
    cursor = conn.cursor()
    
    # Удаляем все уроки брони по её ID
    cursor.execute(
        "DELETE FROM books WHERE date = ? AND cab_id = ? AND lesson = ?", 
        (date, cab_num, lesson)
    )
    
    conn.commit()
    conn.close()

def update_booking_date(new_date: str, old_date: str, cab_num: int, lesson: int):
    conn = sqlite3.connect("static/data/data.db")
    cursor = conn.cursor()
    
    # Обновляем дату для указанной брони
    cursor.execute(
        "UPDATE books SET date = ? WHERE cab_id = ? AND lesson = ? AND date = ?", 
        (new_date, cab_num, lesson, old_date)
    )
    
    conn.commit()
    conn.close()


def get_books(user_id):
    cabs = []
    try:
        # Подключаемся к базе данных
        with sqlite3.connect('data.db') as conn:
            conn = sqlite3.connect("static/data/data.db")
            cursor = conn.cursor()
            # Выполняем SQL-запрос с группировкой
            cursor.execute("""
                SELECT 
                    id,
                    date, 
                    cab_id, 
                    GROUP_CONCAT(lesson ORDER BY lesson) 
                FROM books 
                WHERE pers_id = ? 
                GROUP BY date, cab_id 
                ORDER BY date, cab_id
            """, (user_id,))
            
            # Обрабатываем результаты
            for row in cursor.fetchall():
                id = row[0]
                date = row[1]
                cab_id = row[2]
                lessons = list(map(int, row[3].split(','))) if row[3] else []
                cabs.append((date, cab_id, lessons, id))
                
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
    
    return cabs

def load_cab_schedule(file_path):
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Папка {file_path} не существует")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            cabinet_data = json.load(file)
            schedules_list = cabinet_data
            
    except Exception as e:
        print(f"⚠️ Ошибка в файле {file_path}: {str(e)}")
    
    return schedules_list


def load_class_schedules(folder_path):
    schedules_list = []
    
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Папка {folder_path} не существует")
    files = os.listdir(folder_path)
    filtered_files = [f for f in files if f.startswith('cab') and f.endswith('.json')]
    sorted_files = sorted(filtered_files, 
                      key=lambda x: int(x[3:].replace('.json', '')))
    for filename in sorted_files:
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    cabinet_data = json.load(file)
                    schedules_list.append(cabinet_data)
                    
            except Exception as e:
                print(f"⚠️ Ошибка в файле {filename}: {str(e)}")
    
    return schedules_list

def load_all_cabs_one_day(day, folder_path):
    schedules_list = []
    
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Папка {folder_path} не существует")
    files = os.listdir(folder_path)
    filtered_files = [f for f in files if f.startswith('cab') and f.endswith('.json')]
    sorted_files = sorted(filtered_files, 
                      key=lambda x: int(x[3:].replace('.json', '')))
    for filename in sorted_files:
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    cabinet_data = dict(json.load(file))
                    needed_data = dict()
                    needed_data['cabinet'] = cabinet_data['cabinet']
                    needed_data[day] = cabinet_data[day]
                    #print(needed_data)
                    schedules_list.append(needed_data)
                    
            except Exception as e:
                print(f"⚠️ Ошибка в файле {filename}: {str(e)}")
    
    return schedules_list

def load_one_cab_one_day(day, file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Папка {file_path} не существует")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            cabinet_data = json.load(file)
            needed_data = dict()
            needed_data['cabinet'] = cabinet_data['cabinet']
            needed_data[day] = cabinet_data[day]
            schedules_list = needed_data
            
    except Exception as e:
        print(f"⚠️ Ошибка в файле {file_path}: {str(e)}")
    
    return schedules_list

def _load_description_file(file_path: str) -> Dict:
    """Внутренняя функция для загрузки файла расписания"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading schedule file {file_path}: {e}")
        return {'find' : -1}

def load_cab_info(cab_id: int) -> Dict:
    """Загрузить информацию о кабинете"""
    file_path = os.path.join(CABINETS_DESC_PATH, f"cab{cab_id}.json")
    desc_data = _load_description_file(file_path)
    desc_data['cabinet'] = cab_id
    return desc_data

def get_books_on_date(cab_id, date):
    conn = sqlite3.connect("static/data/data.db")
    cursor = conn.cursor()
    
    books = cursor.execute("""
                SELECT
                    lesson, type
                FROM books 
                WHERE date = ? AND cab_id = ?
            """, (date, cab_id)).fetchall()
    return books
    
    conn.commit()
    conn.close()