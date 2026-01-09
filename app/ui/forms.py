import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime


class ContactFormWindow(tk.Toplevel):
    """
    Класс окна для добавления или редактирования контакта.
    Поддерживает валидацию полей и автоформатирование (маски) ввода.
    """

    def __init__(self, parent_window, db, refresh_callback, contact_id=None):
        super().__init__()
        self.db = db
        self.refresh_callback = refresh_callback
        self.contact_id = contact_id  # Если ID передан, режим редактирования

        # Настройка размеров окна
        self.width = 580
        self.height = 680
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)

        # Хранение дат создания/изменения для режима редактирования
        self.contact_dates = {"added": "", "modified": ""}

        if self.contact_id:
            self.title("Редактирование")
        else:
            self.title("Новый контакт")

        self.center_window()

        # Делаем окно модальным (блокирует родительское)
        self.transient(parent_window)
        self.grab_set()

        # --- Инициализация валидаторов ---
        # Обертка для Tkinter валидации
        self.vcmd_limit = (self.register(
            self.validate_input), '%P', '%d', '%W')
        self.limits = {}   # Ограничения по длине для конкретных виджетов
        self.patterns = {}  # Ограничения по regex символам
        self.entries = {}  # Словарь для хранения ссылок на поля ввода

        # Основной контейнер
        self.main_frame = tk.Frame(self, padx=10, pady=5)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_form()

        # Если редактируем, загружаем данные из БД
        if self.contact_id:
            self.load_existing_data()

        # Горячие клавиши
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-Key>", self.handle_local_hotkeys)

    def center_window(self):
        """Центрирование окна на экране."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 2) - (self.height // 2)
        self.geometry(f"+{x}+{y}")

    def handle_local_hotkeys(self, event):
        """
        Локальная обработка горячих клавиш.
        Нужна, чтобы работать даже если глобальный перехватчик в main_window
        перекрывает события, и для поддержки русской раскладки (Ctrl+C/V).
        """
        code = event.keycode
        widget = self.focus_get()

        # Ctrl+S - Сохранить
        if code == 83:
            self.save_contact()
            return "break"

        # Если фокус не в поле ввода, выходим
        if not isinstance(widget, (tk.Entry, tk.Text, ttk.Combobox)):
            return

        # Стандартные операции с буфером обмена
        if code == 67:    # Copy
            widget.event_generate("<<Copy>>")
            return "break"
        elif code == 86:  # Paste
            widget.event_generate("<<Paste>>")
            return "break"
        elif code == 88:  # Cut
            widget.event_generate("<<Cut>>")
            return "break"
        elif code == 65:  # Select All
            if isinstance(widget, (tk.Entry, ttk.Combobox)):
                widget.select_range(0, tk.END)
                widget.icursor(tk.END)
            elif isinstance(widget, tk.Text):
                widget.tag_add("sel", "1.0", "end")
            return "break"

    def validate_input(self, new_value, action, widget_name):
        """
        Функция валидации ввода (вызывается Tkinter при каждом нажатии).
        Проверяет длину строки и разрешенные символы (Regex).
        """
        if action != '1':  # 1 = insert (вставка)
            return True

        # Проверка длины
        limit = self.limits.get(widget_name)
        if limit and len(new_value) > limit:
            return False

        # Проверка паттерна (например, только буквы)
        pattern = self.patterns.get(widget_name)
        if pattern and not re.match(pattern, new_value):
            return False

        return True

    def register_config(self, widget, limit=None, allow_regex=None):
        """Настройка валидации для конкретного виджета."""
        widget_id = str(widget)
        if limit:
            self.limits[widget_id] = limit
        if allow_regex:
            self.patterns[widget_id] = allow_regex
        widget.config(validate="key", validatecommand=self.vcmd_limit)

    # ---------------------------------------------------------
    # ЛОГИКА АВТОФОРМАТИРОВАНИЯ (МАСКИ ВВОДА)
    # ---------------------------------------------------------

    def format_date_live(self, event):
        """
        Автоформатирование даты при вводе.
        Формат: ДД.ММ.ГГГГ
        Срабатывает на отпускание клавиши (KeyRelease).
        """
        # Если нажали Backspace, не мешаем пользователю удалять
        if event.keysym == "BackSpace":
            return

        entry = event.widget
        text = entry.get()

        # Удаляем все нечисловые символы
        digits = re.sub(r"\D", "", text)

        formatted = ""
        # Собираем строку: первые 2 цифры (ДД)
        if len(digits) > 0:
            formatted += digits[:2]
        # Если есть 3-я цифра, добавляем точку и ММ
        if len(digits) >= 2:
            formatted += "." + digits[2:4]
        # Если есть 5-я цифра, добавляем точку и ГГГГ
        if len(digits) >= 4:
            formatted += "." + digits[4:8]

        # Если текст изменился, обновляем поле
        if text != formatted:
            entry.delete(0, tk.END)
            entry.insert(0, formatted)

    def format_phone_live(self, event):
        """
        Автоформатирование телефона при вводе.
        Формат: +7 (XXX) XXX-XX-XX
        """
        if event.keysym == "BackSpace":
            return

        entry = event.widget
        text = entry.get()

        # Оставляем только цифры
        digits = re.sub(r"\D", "", text)

        # Если поле пустое, но начали ввод - подставляем 7
        if not digits:
            digits = "7"

        # Ограничиваем ввод 11 цифрами (7 + 10 цифр номера)
        digits = digits[:11]

        # Формируем маску
        formatted = "+7"
        if len(digits) > 1:
            formatted += " (" + digits[1:4]
        if len(digits) >= 4:
            formatted += ") " + digits[4:7]
        if len(digits) >= 7:
            formatted += "-" + digits[7:9]
        if len(digits) >= 9:
            formatted += "-" + digits[9:11]

        # Обновляем поле, если формат отличается от текущего
        if text != formatted:
            entry.delete(0, tk.END)
            entry.insert(0, formatted)

    # ---------------------------------------------------------

    def create_form(self):
        """Создание всех виджетов формы."""
        pad_opts = {'padx': 5, 'pady': 3}

        # --- Группа: Личные данные ---
        lbl_frame_personal = ttk.LabelFrame(
            self.main_frame, text="Личные данные")
        lbl_frame_personal.pack(fill=tk.X, **pad_opts)

        # Regex для имен (буквы, пробелы, дефис)
        name_regex = r"^[a-zA-Zа-яА-ЯёЁ\s-]*$"

        self.create_entry(lbl_frame_personal, "Фамилия*", "last_name",
                          0, limit=25, required=True, regex=name_regex)
        self.create_entry(lbl_frame_personal, "Имя*", "first_name",
                          1, limit=25, required=True, regex=name_regex)
        self.create_entry(lbl_frame_personal, "Отчество",
                          "patronymic", 2, limit=25, regex=name_regex)

        # Поле Даты рождения
        # limit=10 здесь условно, так как format_date_live сама обрежет лишнее
        self.create_entry(lbl_frame_personal, "Дата рождения",
                          "birth_date", 3, limit=10)

        # Подключаем "живое" форматирование к полю даты
        self.entries["birth_date"].bind("<KeyRelease>", self.format_date_live)

        # Подсказка
        tk.Label(lbl_frame_personal, text="(ДД.ММ.ГГГГ)", fg="gray",
                 font=("Arial", 8)).grid(row=3, column=2, sticky="w")

        # --- Группа: Связь ---
        lbl_frame_contacts = ttk.LabelFrame(self.main_frame, text="Связь")
        lbl_frame_contacts.pack(fill=tk.X, **pad_opts)

        # Создаем поля телефонов через спец. метод (с форматированием)
        self.create_phone_entry(
            lbl_frame_contacts, "Телефон осн.", "phone_primary", 0, required=False)
        self.create_phone_entry(
            lbl_frame_contacts, "Телефон доп.", "phone_secondary", 1, required=False)

        self.create_entry(lbl_frame_contacts, "Email",
                          "email", 2, limit=30, is_email=True)
        self.create_entry(lbl_frame_contacts, "Адрес", "address", 3, limit=30)

        # --- Группа: Соцсети ---
        frame_all_socials = ttk.LabelFrame(
            self.main_frame, text="Социальные сети")
        frame_all_socials.pack(fill=tk.X, **pad_opts)

        social_networks = ["", "Telegram", "VK",
                           "WhatsApp", "Instagram", "Facebook", "YouTube"]

        # Цикл для создания 3 строк соцсетей
        for i in range(1, 4):
            row_frame = tk.Frame(frame_all_socials)
            row_frame.pack(fill=tk.X, pady=2)

            tk.Label(row_frame, text=f"#{i}",
                     width=3, fg="gray").pack(side=tk.LEFT)

            # Выпадающий список сетей
            cb = ttk.Combobox(row_frame, values=social_networks,
                              state="readonly", width=11)
            cb.pack(side=tk.LEFT, padx=(0, 5))
            self.entries[f"social_network_{i}"] = cb

            # Поле Ника
            tk.Label(row_frame, text="Ник:").pack(side=tk.LEFT)
            entry_nick = tk.Entry(row_frame, width=19)
            entry_nick.pack(side=tk.LEFT, padx=(2, 5))
            self.register_config(entry_nick, limit=25)
            self.entries[f"social_nickname_{i}"] = entry_nick

            # Поле Ссылки
            tk.Label(row_frame, text="URL:").pack(side=tk.LEFT)
            entry_link = tk.Entry(row_frame, width=19)
            entry_link.pack(side=tk.LEFT, padx=2)
            self.register_config(entry_link, limit=40)
            self.entries[f"social_link_{i}"] = entry_link

        # --- Группа: Дополнительно ---
        lbl_frame_other = ttk.LabelFrame(self.main_frame, text="Дополнительно")
        lbl_frame_other.pack(fill=tk.X, **pad_opts)

        # Категория
        tk.Label(lbl_frame_other, text="Категория:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2)
        categories = ["Не распределён", "Работа", "Семья",
                      "Друзья", "Знакомые", "Клиенты", "Учеба", "Избранное"]
        cb_cat = ttk.Combobox(
            lbl_frame_other, values=categories, state="readonly", width=30)
        cb_cat.current(0)
        cb_cat.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.entries["category"] = cb_cat

        # Заметки (Text widget)
        tk.Label(lbl_frame_other, text="Заметки:").grid(
            row=1, column=0, sticky=tk.NW, padx=5, pady=2)
        txt_notes = tk.Text(lbl_frame_other, height=3, width=33, wrap=tk.WORD)
        txt_notes.grid(row=1, column=1, padx=5, pady=2)

        # Ограничение длины заметок (нет встроенного validate для Text, делаем через bind)
        def check_notes_length(event):
            content = txt_notes.get("1.0", "end-1c")
            if len(content) > 60:
                txt_notes.delete("1.60", tk.END)  # Удаляем лишнее
        txt_notes.bind("<KeyRelease>", check_notes_length)
        self.entries["notes"] = txt_notes

        # --- Кнопки управления ---
        btn_frame = tk.Frame(self.main_frame, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        save_text = "Сохранить изменения" if self.contact_id else "Сохранить"

        tk.Button(btn_frame, text=save_text, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                  command=self.save_contact, height=2, width=18, cursor="hand2").pack(side=tk.LEFT, padx=10, expand=True)

        if self.contact_id:
            tk.Button(btn_frame, text="История", command=self.show_history,
                      height=2, width=10, cursor="hand2").pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Отмена", command=self.destroy, height=2,
                  width=15, cursor="hand2").pack(side=tk.RIGHT, padx=10, expand=True)

    def load_existing_data(self):
        """Загрузка данных контакта в поля (для режима редактирования)."""
        data = self.db.get_contact_by_id(self.contact_id)
        if not data:
            messagebox.showerror("Ошибка", "Контакт не найден!")
            self.destroy()
            return

        full_name = f"{data[1]} {data[2]}".strip()
        self.title(f"Редактировать: {full_name}")

        # Сохраняем даты для кнопки "История"
        self.contact_dates["added"] = data[18]
        self.contact_dates["modified"] = data[19]

        # Маппинг ключей полей к индексам столбцов в БД
        mapping = {
            "last_name": 1, "first_name": 2, "patronymic": 3,
            "phone_primary": 4, "phone_secondary": 5, "email": 6, "address": 7,
            "social_network_1": 8, "social_nickname_1": 9, "social_link_1": 10,
            "social_network_2": 11, "social_nickname_2": 12, "social_link_2": 13,
            "social_network_3": 14, "social_nickname_3": 15, "social_link_3": 16,
            "category": 20, "birth_date": 21
        }

        for key, idx in mapping.items():
            if len(data) > idx:
                val = data[idx]
                if val:
                    if isinstance(self.entries[key], ttk.Combobox):
                        self.entries[key].set(val)
                    elif isinstance(self.entries[key], tk.Entry):
                        self.entries[key].delete(0, tk.END)
                        self.entries[key].insert(0, val)

        if data[17]:  # Заметки
            self.entries["notes"].insert("1.0", data[17])

    def show_history(self):
        msg = f"Дата создания:\n{self.contact_dates['added']}\n\nПоследнее изменение:\n{self.contact_dates['modified']}"
        messagebox.showinfo("История изменений", msg)

    def create_entry(self, parent, label_text, key, row, limit=255, required=False, regex=None, is_email=False):
        """Вспомогательный метод для создания стандартного поля ввода с Label."""
        lbl = tk.Label(parent, text=label_text)
        lbl.grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        entry = tk.Entry(parent, width=32)
        entry.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)

        # Для полей с масками валидация regex/limit может мешать, поэтому для birth_date не ставим
        if key != "birth_date":
            self.register_config(entry, limit=limit, allow_regex=regex)

        self.entries[key] = entry
        self.entries[f"{key}_required"] = required

        # Валидация Email при потере фокуса
        if is_email:
            def validate_email_focus(event):
                val = entry.get().strip()
                if val and not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", val):
                    entry.config(bg="#fff0f0")  # Подсветка ошибки
                else:
                    entry.config(bg="white")
            entry.bind("<FocusOut>", validate_email_focus)

    def create_phone_entry(self, parent, label_text, key, row, required=False):
        """
        Создание поля для телефона.
        Отдельный метод, так как нужна привязка маски и начальное значение '+7'.
        """
        lbl = tk.Label(parent, text=label_text)
        lbl.grid(row=row, column=0, sticky='n', padx=5, pady=(5, 0))

        frame_phone = tk.Frame(parent)
        frame_phone.grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)

        entry = tk.Entry(frame_phone, width=32)
        entry.insert(0, "+7")  # Начальное значение
        entry.pack(side=tk.TOP)

        # Подсказка формата под полем (только для основного)
        if key == "phone_primary":
            tk.Label(frame_phone, text="+7 xxx xxx xx xx", fg="gray",
                     font=("Arial", 8)).pack(side=tk.TOP, anchor=tk.W)

        # Привязываем "живое" форматирование
        entry.bind("<KeyRelease>", self.format_phone_live)
        entry.bind("<FocusIn>", lambda e: entry.config(bg="white"))

        self.entries[key] = entry
        self.entries[f"{key}_required"] = required

    def save_contact(self):
        """Сбор данных, проверка и сохранение в БД."""
        data = {}
        error_fields = []

        # Список текстовых полей для проверки
        text_fields = ["last_name", "first_name", "patronymic",
                       "phone_primary", "phone_secondary", "email", "address", "birth_date"]

        for key in text_fields:
            if key in self.entries:
                entry_widget = self.entries[key]
                entry_widget.config(bg="white")
                value = entry_widget.get().strip()
                is_required = self.entries.get(f"{key}_required", False)

                # Проверка обязательных полей
                if is_required:
                    # Для телефона проверяем, что там не просто "+7", а есть цифры
                    if not value or (key.startswith("phone") and len(re.sub(r"\D", "", value)) <= 1):
                        entry_widget.config(bg="#ffcccc")
                        error_fields.append(key)
                        continue

                # Валидация даты рождения перед сохранением
                if key == "birth_date" and value:
                    if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", value):
                        entry_widget.config(bg="#ffcccc")
                        messagebox.showerror(
                            "Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ")
                        return
                    try:
                        datetime.strptime(value, "%d.%m.%Y")
                    except ValueError:
                        entry_widget.config(bg="#ffcccc")
                        messagebox.showerror(
                            "Ошибка", "Такой даты не существует")
                        return

                data[key] = value

        # Проверка соцсетей (если выбрана сеть, должен быть ник или ссылка)
        for i in range(1, 4):
            net = self.entries[f"social_network_{i}"].get()
            nick = self.entries[f"social_nickname_{i}"].get().strip()
            link = self.entries[f"social_link_{i}"].get().strip()
            if net and not (nick or link):
                messagebox.showwarning(
                    "Внимание", f"Укажите ник или ссылку для {net}")
                return
            data[f"social_nickname_{i}"] = nick
            data[f"social_link_{i}"] = link
            data[f"social_network_{i}"] = net

        if error_fields:
            messagebox.showwarning("Ошибка", "Заполните обязательные поля!")
            return

        # Финальная проверка телефона
        ph = data.get("phone_primary", "")
        if ph:
            digits = re.sub(r"\D", "", ph)
            if len(digits) < 11:
                self.entries["phone_primary"].config(bg="#ffcccc")
                messagebox.showerror(
                    "Ошибка", "Телефон должен содержать 11 цифр")
                return

        # Сбор остальных данных
        data["category"] = self.entries["category"].get()
        data["notes"] = self.entries["notes"].get("1.0", "end-1c").strip()

        # Подготовка списка для БД (порядок важен!)
        db_values = [
            data["last_name"], data["first_name"], data["patronymic"],
            data["phone_primary"], data["phone_secondary"], data["email"], data["address"],
            data["social_network_1"], data.get(
                "social_nickname_1"), data.get("social_link_1"),
            data["social_network_2"], data.get(
                "social_nickname_2"), data.get("social_link_2"),
            data["social_network_3"], data.get(
                "social_nickname_3"), data.get("social_link_3"),
            data["notes"], data["category"], data["birth_date"]
        ]

        # Вызов методов БД
        if self.contact_id:
            success, message = self.db.update_contact(
                self.contact_id, db_values)
        else:
            success, message = self.db.add_contact(db_values)

        if success:
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("Ошибка", message)
