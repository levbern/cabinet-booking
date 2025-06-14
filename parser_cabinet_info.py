import csv
import json
import os

def csv_to_json(csv_filename, json_filename):
    # Соответствие номеров дней и названий
    days_map = {
        '0': "Понедельник",
        '1': "Вторник",
        '2': "Среда",
        '3': "Четверг",
        '4': "Пятница",
        '5': "Суббота"
    }
    
    # Номер кабинета
    class_number = int(csv_filename[12:].replace('.csv', ''))

    result = {"cabinet": class_number}
    
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        
        # Пропускаем заголовок с временем уроков
        next(reader)
        
        for row in reader:
            if not row or row[0] not in days_map:
                continue
                
            day_name = days_map[row[0]]
            lessons = []
            
            # Обрабатываем 11 уроков (индексы 1-11)
            for cell in row[1:12]:
                if not cell.strip():
                    lessons.append("свободен")
                else:
                    # Объединяем переносы строк в одну строку
                    cleaned = ' '.join(cell.splitlines()).strip()
                    lessons.append(cleaned)
            
            result[day_name] = lessons

    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(result, jsonfile, ensure_ascii=False, indent=4)

def start_loader_cabinets():
    files = os.listdir('cabinets')
    print(files)
    for file in files:
        res = file.replace("csv", "")
        res += "json"
        res = 'static/data/cabinets/' + res
        csv_to_json('cabinets/' + file, res)
