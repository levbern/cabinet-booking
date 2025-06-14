import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    jsonify
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
import database, parser_cabinet_info

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_here'  # Замените на реальный секретный ключ
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройка системы аутентификации
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id):
        user_data = database.get_user(user_id)
        if user_data:
            self.id = user_data[0]
            self.username = user_data[5]


@login_manager.user_loader
def load_user(user_id):
    user_data = database.get_user(user_id)
    return User(user_data[0]) if user_data else None


def process_lessons(lessons_str):
    """Универсальная обработка строки с уроками"""
    return [int(lesson) for lesson in lessons_str.strip('[]').replace(' ', '').split(',')]


# =======================
# Маршруты аутентификации
# =======================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return render_template('error.html', loggedIn=True, error="Вы уже зарегистрированы")
    
    if request.method == 'POST':
        data = request.form.to_dict()
        database.add_user(data)
        user_data = database.login_user(data['username'])
        login_user(User(user_data[0]))
        return redirect(url_for('home'))
    
    return render_template("register.html", loggedIn=False)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return render_template('error.html', loggedIn=True, error="Вы уже вошли в систему")
    
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user_data = database.login_user(username)
        
        if user_data and user_data[1] == password:
            login_user(User(user_data[0]))
            return redirect(url_for('home'))
        
        return render_template('login.html', loggedIn=False, error='Неверные данные!')
    
    return render_template('login.html', loggedIn=False)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# ===================
# Основные маршруты
# ===================
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', loggedIn=current_user.is_authenticated)


@app.route('/week')
@login_required
def week():
    return render_template('week.html', loggedIn=True)


@app.route('/list')
@login_required
def list_books():
    bookings = database.get_books(current_user.id)
    return render_template('list.html', cabs=bookings, loggedIn=True)


# =====================
# Маршруты бронирования
# =====================
@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    week_day = date.today().weekday()
    tod = datetime.now()
    d = timedelta(days = week_day)
    a = tod - d
    a += timedelta(days = 20)
    if request.method == 'GET':
        return render_template('book.html', loggedIn=True, today_date=date.today(), week3_date=str(a)[:10], err=0)
    
    form_data = request.form.to_dict()
    user_data = database.get_user(current_user.id)
    name = f"{user_data[2]} {user_data[1][0]}."
    res = database.add_book(form_data, name, current_user.id)
    print(res)
    if res == -1:
        return render_template('book.html', loggedIn=True, today_date=date.today(), week3_date=str(a)[:10], err=1)
    return redirect(url_for('home'))


@app.route('/move_booking', methods=['POST'])
@login_required
def move_booking():
    form_data = request.form
    lessons = process_lessons(form_data['lessons'])
    
    for lesson in lessons:
        database.update_booking_date(
            form_data['new_date'],
            form_data['old_date'],
            form_data['cab_num'],
            lesson
        )
    
    return redirect(url_for('list_books'))


@app.route('/delete_booking', methods=['POST'])
@login_required
def delete_booking():
    form_data = request.form
    lessons = process_lessons(form_data['lessons'])
    
    for lesson in lessons:
        database.delete_booking(
            form_data['date'],
            form_data['cab_num'],
            lesson
        )
    
    return redirect(url_for('list_books'))


# =======================
# Маршруты кабинетов
# =======================
@app.route('/info_cab', methods=['GET', 'POST'])
@login_required
def info_cab():
    week_day = date.today().weekday()
    tod = datetime.now()
    d = timedelta(days = week_day)
    a = tod - d
    a += timedelta(days = 20)
    if request.method == 'GET':
        return render_template('info_cab.html', loggedIn=True, today_date=date.today(), cab=0, week3_date=str(a)[:10], err=0)
    cab_num = request.form['cab_num']
    cab = database.load_cab_info(cab_num)
    return render_template('info_cab.html', loggedIn=True, today_date=date.today(), cab=cab, week3_date=str(a)[:10], err=0)


@app.route('/make_book', methods=['POST'])
@login_required
def make_book():
    form_data = request.form.to_dict()
    print(form_data)
    user_data = database.get_user(current_user.id)
    name = f"{user_data[2]} {user_data[1][0]}."
    res = database.add_book(form_data, name, current_user.id)
    if res == -1:
        week_day = date.today().weekday()
        tod = datetime.now()
        d = timedelta(days = week_day)
        a = tod - d
        a += timedelta(days = 20)
        cab = database.load_cab_info(form_data['cab_num'])
        return render_template('info_cab.html', loggedIn=True, today_date=date.today(), cab=cab, week3_date=str(a)[:10], err=1)
    return redirect(url_for('home'))


# =======================
# Маршруты расписания
# =======================
@app.route('/week_one', methods=['GET', 'POST'])
@login_required
def week_one():
    if request.method == 'GET':
        return render_template('week_one.html', loggedIn=True, cab=0)
    
    cab_num = int(request.form.get("cab_num", 0))
    class_path = f"static/data/cabinets/cab{cab_num}.json"
    cabinet = database.load_cab_schedule(class_path)
    today_date = date.today()
    week_day = date.today().weekday()
    tod = datetime.now()
    d = timedelta(days = week_day)
    a = tod - d
    a += timedelta(days = 7 * int(request.form["week"]))
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    dates = {}
    for i in day_names:
        books = database.get_books_on_date(cab_num, str(a)[:10])
        print(books)
        for l in books:
            type = ""
            if l[1] == '0':
                type = "Урок"
            elif l[1] == '1':
                type = "Кружок"
            else:
                type = "Внеклассная деятельность"
            cabinet[i][l[0]] = type
        dates[i] = str(a)[:10]
        a += timedelta(days = 1)
    return render_template('week_one.html', loggedIn=True, cab=cabinet, dates=dates)


@app.route('/week_all')
@login_required
def week_all():
    classes_folder = "static/data/cabinets/"
    all_cabinets = database.load_class_schedules(classes_folder)
    return render_template('week_all.html', all_cabinets=all_cabinets, loggedIn=True)


@app.route('/all_cabs_one_day', methods=['GET', 'POST'])
@login_required
def all_cabs_one_day():
    today_date = date.today()
    
    if request.method == 'GET':
        return render_template('all_cabs_one_day.html', loggedIn=True, cabs=0, today_date=today_date)
    
    selected_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    if selected_date.weekday() == 6:  # Воскресенье
        return render_template('all_cabs_one_day.html', loggedIn=True, cabs=0, today_date=today_date)
    
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    classes_folder = "static/data/cabinets/"
    cabinets = database.load_all_cabs_one_day(day_names[selected_date.weekday()], classes_folder)
    
    return render_template(
        'all_cabs_one_day.html',
        loggedIn=True,
        cabs=cabinets,
        day=day_names[selected_date.weekday()],
        today_date=today_date
    )


@app.route('/one_cab_one_day', methods=['GET', 'POST'])
@login_required
def one_cab_one_day():
    today_date = date.today()
    
    if request.method == 'GET':
        return render_template('one_cab_one_day.html', loggedIn=True, cab=None, today_date=today_date)
    
    cab_num = int(request.form.get("cab_num", 0))
    selected_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    
    if selected_date.weekday() == 6:  # Воскресенье
        return render_template('one_cab_one_day.html', loggedIn=True, cab=None, today_date=today_date)
    
    day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    class_path = f"static/data/cabinets/cab{cab_num}.json"
    cabinet = database.load_one_cab_one_day(day_names[selected_date.weekday()], class_path)
    
    return render_template(
        'one_cab_one_day.html',
        loggedIn=True,
        cab=cabinet,
        day=day_names[selected_date.weekday()],
        today_date=today_date
    )


# ===================
# Обработка ошибок
# ===================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                           loggedIn=current_user.is_authenticated,
                           error='Страница не найдена'), 404


if __name__ == "__main__":
    parser_cabinet_info.start_loader_cabinets()
    app.run(port=8080, host="0.0.0.0", debug=True)
 