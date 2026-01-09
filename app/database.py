import sqlite3  # Встроенная библиотека для работы с SQL-базами данных
from datetime import datetime  # Для работы с текущим временем и датами рождений
# Библиотека для операций с файлами (нужна для резервного копирования)
import shutil
import os  # Библиотека для работы с путями и файловой системой


class Database:
    """
    Класс для управления базой данных SQLite.
    Инкапсулирует (скрывает) SQL-запросы внутри методов Python.
    """

    def __init__(self, db_file="contacts.db"):
        # Имя файла базы данных
        self.db_file = db_file

        # Устанавливаем соединение с файлом БД
        self.connection = sqlite3.connect(db_file)

        # Создаем кастомную SQL-функцию 'py_lower'.
        # SQLite "из коробки" плохо умеет делать lower() для кириллицы.
        # Мы используем мощь Python (s.lower()) внутри SQL-запросов для поиска.
        self.connection.create_function(
            "py_lower", 1, lambda s: s.lower() if s else "")

        # Курсор — это инструмент, который выполняет SQL-запросы и получает результаты
        self.cursor = self.connection.cursor()

        # При старте сразу проверяем, созданы ли таблицы
        self.create_tables()

    def create_tables(self):
        """Создает структуру таблиц, если они еще не существуют."""

        # SQL-запрос для основной таблицы контактов
        # AUTOINCREMENT делает так, чтобы id сам увеличивался (1, 2, 3...)
        query_contacts = """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            patronymic TEXT,
            phone_primary TEXT,
            phone_secondary TEXT,
            email TEXT,
            address TEXT,
            social_network_1 TEXT,
            social_nickname_1 TEXT,
            social_link_1 TEXT,
            social_network_2 TEXT,
            social_nickname_2 TEXT,
            social_link_2 TEXT,
            social_network_3 TEXT,
            social_nickname_3 TEXT,
            social_link_3 TEXT,
            notes TEXT,
            date_added TEXT NOT NULL,
            date_modified TEXT NOT NULL,
            category TEXT DEFAULT 'Не распределён',
            birth_date TEXT
        );
        """

        # SQL-запрос для таблицы заметок (буфер обмена)
        query_notes = """
        CREATE TABLE IF NOT EXISTS saved_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT
        );
        """

        try:
            # Выполняем запросы
            self.cursor.execute(query_contacts)
            self.cursor.execute(query_notes)
            # Фиксируем изменения в файле (Commit)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка БД: {e}")

    # --- Методы для работы с контактами (CRUD) ---

    def add_contact(self, data):
        """Добавляет новый контакт в базу."""
        # Получаем текущее время для полей date_added и date_modified
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Запрос с плейсхолдерами (?) для защиты от SQL-инъекций
        query = """
        INSERT INTO contacts (
            last_name, first_name, patronymic, 
            phone_primary, phone_secondary, email, address,
            social_network_1, social_nickname_1, social_link_1,
            social_network_2, social_nickname_2, social_link_2,
            social_network_3, social_nickname_3, social_link_3,
            notes, category, birth_date, date_added, date_modified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Формируем список значений: данные от пользователя + 2 временные метки
        values = list(data) + [current_time, current_time]
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return True, "Контакт успешно добавлен"
        except sqlite3.IntegrityError:
            # Сработает, если нарушена уникальность (например, такой ID уже есть)
            return False, "Ошибка уникальности данных"
        except sqlite3.Error as e:
            return False, f"Ошибка базы данных: {e}"

    def update_contact(self, contact_id, data):
        """Обновляет существующий контакт по ID."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        UPDATE contacts SET
            last_name=?, first_name=?, patronymic=?, 
            phone_primary=?, phone_secondary=?, email=?, address=?,
            social_network_1=?, social_nickname_1=?, social_link_1=?,
            social_network_2=?, social_nickname_2=?, social_link_2=?,
            social_network_3=?, social_nickname_3=?, social_link_3=?,
            notes=?, category=?, birth_date=?, date_modified=?
        WHERE id=?
        """
        # Значения: поля + дата изменения + ID для WHERE
        values = list(data) + [current_time, contact_id]
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return True, "Контакт успешно обновлен"
        except sqlite3.Error as e:
            return False, f"Ошибка базы данных: {e}"

    def update_single_field(self, contact_id, field, value):
        """Быстрое обновление одного поля (используется в контекстном меню)."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Внимание: имя поля (field) подставляем через f-строку,
        # так как SQL не позволяет передавать имена колонок через ?
        query = f"UPDATE contacts SET {field}=?, date_modified=? WHERE id=?"
        try:
            self.cursor.execute(query, (value, current_time, contact_id))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False

    def delete_contacts(self, ids_list):
        """Удаляет список контактов по их ID."""
        if not ids_list:
            return
        # Создаем строку вида "?, ?, ?" в зависимости от количества ID
        placeholders = ', '.join('?' for _ in ids_list)
        query = f"DELETE FROM contacts WHERE id IN ({placeholders})"
        try:
            self.cursor.execute(query, ids_list)
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            return False

    def clear_database(self):
        """Полная очистка всех таблиц (Опасно!)."""
        try:
            self.cursor.execute("DELETE FROM contacts")
            self.cursor.execute("DELETE FROM saved_notes")
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False

    def get_contact_by_id(self, contact_id):
        """Получает полные данные одного контакта."""
        query = "SELECT * FROM contacts WHERE id = ?"
        self.cursor.execute(query, (contact_id,))
        return self.cursor.fetchone()  # Возвращает кортеж (tuple) или None

    def get_contacts(self, search_text="", category_filter="Все категории", sort_by="По ФИО (А-Я)"):
        """
        Главная функция выборки.
        Реализует поиск, фильтрацию и сортировку SQL-запросом.
        """
        # Начало запроса - всегда истинное условие 1=1, чтобы удобно добавлять AND
        query = "SELECT * FROM contacts WHERE 1=1"
        params = []

        # Логика поиска
        if search_text:
            # %текст% для поиска подстроки
            search_pattern = f"%{search_text.lower()}%"
            # Используем нашу функцию py_lower для поиска без учета регистра
            query += """ AND (
                py_lower(last_name) LIKE ? OR 
                py_lower(first_name) LIKE ? OR 
                phone_primary LIKE ? OR 
                py_lower(email) LIKE ? OR 
                py_lower(notes) LIKE ? OR 
                py_lower(category) LIKE ?
            )"""
            # Добавляем паттерн поиска 6 раз (для каждого поля)
            params.extend([search_pattern]*6)

        # Логика фильтрации по категории
        if category_filter != "Все категории":
            query += " AND category = ?"
            params.append(category_filter)

        # Логика сортировки (маппинг текста из UI в SQL команды)
        sort_map = {
            "По ФИО (А-Я)": "last_name ASC, first_name ASC",
            "По ФИО (Я-А)": "last_name DESC, first_name DESC",
            "По дате добавления (новые)": "date_added DESC",
            "По дате изменения (свежие)": "date_modified DESC",
            "По дате изменения (старые)": "date_modified ASC",
            "По основному телефону": "phone_primary ASC",
            "По категории": "category ASC",
            "По email": "email ASC"
        }
        order_clause = sort_map.get(sort_by, "last_name ASC")
        query += f" ORDER BY {order_clause}"

        self.cursor.execute(query, params)
        return self.cursor.fetchall()  # Возвращает список кортежей

    def get_statistics(self):
        """Возвращает общее кол-во и разбивку по категориям."""
        self.cursor.execute("SELECT COUNT(*) FROM contacts")
        total = self.cursor.fetchone()[0]
        self.cursor.execute(
            "SELECT category, COUNT(*) FROM contacts GROUP BY category")
        by_category = self.cursor.fetchall()
        return total, by_category

    def find_duplicates(self):
        """Ищет контакты с одинаковыми ФИО и Телефоном."""
        query = """
        SELECT last_name, first_name, phone_primary, COUNT(*) as c 
        FROM contacts 
        GROUP BY last_name, first_name, phone_primary 
        HAVING c > 1
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_upcoming_birthdays(self):
        """
        Сложная логика поиска ближайших дней рождений (на 30 дней вперед).
        Учитывает переход года (например, если сегодня 30 декабря, а ДР 2 января).
        """
        query = "SELECT last_name, first_name, birth_date FROM contacts WHERE birth_date IS NOT NULL AND birth_date != ''"
        self.cursor.execute(query)
        all_dates = self.cursor.fetchall()

        today = datetime.now().date()
        upcoming = []

        for last, first, bdate_str in all_dates:
            try:
                # Парсим строку даты
                bdate = datetime.strptime(bdate_str, "%d.%m.%Y").date()

                # Создаем временную дату ДР в ТЕКУЩЕМ году
                bday_this_year = bdate.replace(year=today.year)

                # Если ДР уже прошел в этом году, смотрим на следующий год
                if bday_this_year < today:
                    bday_this_year = bday_this_year.replace(
                        year=today.year + 1)

                # Считаем разницу в днях
                delta = (bday_this_year - today).days

                # Если ДР в ближайшие 30 дней
                if 0 <= delta <= 30:
                    upcoming.append((delta, f"{last} {first}", bday_this_year))
            except ValueError:
                continue  # Пропускаем некорректные даты

        # Сортируем: сначала те, у кого ДР ближе
        upcoming.sort(key=lambda x: x[0])
        return upcoming

    # --- Методы для заметок (аналогично контактам) ---

    def save_note(self, title, content):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute(
                "INSERT INTO saved_notes (title, content, created_at) VALUES (?, ?, ?)", (title, content, current_time))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False

    def get_all_notes(self):
        self.cursor.execute(
            "SELECT * FROM saved_notes ORDER BY created_at DESC")
        return self.cursor.fetchall()

    def delete_note(self, note_id):
        try:
            self.cursor.execute(
                "DELETE FROM saved_notes WHERE id = ?", (note_id,))
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False

    # --- Служебные методы ---

    def check_if_empty(self):
        """Проверяет, пустая ли база (для добавления демо-данных)."""
        self.cursor.execute("SELECT COUNT(*) FROM contacts")
        return self.cursor.fetchone()[0] == 0

    def add_test_data(self):
        """Добавляет пару контактов для примера, если база пуста."""
        if self.check_if_empty():
            test_contacts = [
                ("Иванов", "Иван", "Иванович", "+7 (900) 111-22-33", "", "ivan@test.ru", "Москва", "Telegram",
                 "@ivan_pro", "https://t.me/ivan_pro", "", "", "", "", "", "", "Директор", "Работа", "15.01.1990"),
                ("Петрова", "Анна", "", "+7 (999) 888-77-66", "", "anna@mail.ru", "СПб", "VK", "anna_k",
                 "https://vk.com/anna", "", "", "", "", "", "", "Одногруппница", "Учеба", "10.05.1995")
            ]
            for contact in test_contacts:
                self.add_contact(contact)

    def backup_db(self):
        """Создает копию файла contacts.db в папке backups."""
        if not os.path.exists(self.db_file):
            return False, "База данных не найдена"

        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Формируем имя файла с временной меткой
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.db_file}"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            shutil.copy2(self.db_file, backup_path)
            return True, os.path.abspath(backup_path)
        except Exception as e:
            return False, str(e)
