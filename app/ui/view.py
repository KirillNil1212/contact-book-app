import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser  # Для открытия ссылок на соцсети


class ViewContactWindow(tk.Toplevel):
    """
    Класс окна просмотра контакта.
    """

    def __init__(self, parent, db, contact_id, on_edit_request, on_delete_request):
        super().__init__(parent)
        self.db = db
        self.contact_id = contact_id

        # Callback-функции для переключения режимов
        self.on_edit_request = on_edit_request
        self.on_delete_request = on_delete_request

        self.title("Просмотр контакта")
        self.width = 500
        self.height = 600
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(False, False)
        self.center_window()
        self.transient(parent)

        # Контейнер для контента
        self.main_frame = tk.Frame(self, padx=15, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_ui()  # Создание пустых виджетов
        self.load_data()  # Заполнение данными из БД
        self.bind_keys()  # Горячие клавиши

    def center_window(self):
        """Центрирование окна."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 2) - (self.height // 2)
        self.geometry(f"+{x}+{y}")

    def bind_keys(self):
        """Закрытие на Esc."""
        self.bind("<Escape>", lambda e: self.destroy())

    def create_ui(self):
        """Создание структуры окна (лейблы, рамки, кнопки)."""
        # Большой заголовок с именем
        self.lbl_name = tk.Label(self.main_frame, text="", font=(
            "Arial", 18, "bold"), fg="#333", wraplength=450, justify="center")
        self.lbl_name.pack(pady=(0, 15))

        # Группы полей (LabelFrame)
        self.frame_contacts = ttk.LabelFrame(self.main_frame, text="Связь")
        self.frame_contacts.pack(fill=tk.X, pady=5, padx=2)

        self.frame_socials = ttk.LabelFrame(
            self.main_frame, text="Социальные сети")
        self.frame_socials.pack(fill=tk.X, pady=5, padx=2)

        self.frame_info = ttk.LabelFrame(self.main_frame, text="Информация")
        self.frame_info.pack(fill=tk.X, pady=5, padx=2)

        # Кнопки действий внизу
        frame_actions = tk.Frame(self.main_frame, pady=15)
        frame_actions.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Button(frame_actions, text="Редактировать", command=self.go_to_edit, bg="#2196F3",
                  fg="white", width=12, cursor="hand2").pack(side=tk.LEFT, padx=5, expand=True)
        tk.Button(frame_actions, text="Удалить", command=self.delete_me, bg="#F44336",
                  fg="white", width=12, cursor="hand2").pack(side=tk.LEFT, padx=5, expand=True)
        tk.Button(frame_actions, text="Закрыть", command=self.destroy,
                  width=12, cursor="hand2").pack(side=tk.LEFT, padx=5, expand=True)

    def load_data(self):
        """Получение данных из БД и динамическое создание строк."""
        data = self.db.get_contact_by_id(self.contact_id)
        if not data:
            self.destroy()
            return

        full_name = f"{data[1]} {data[2]} {data[3]}".strip()
        self.lbl_name.config(text=full_name)

        # Заполнение блока "Связь"
        row = 0
        if data[4]:  # Если есть основной телефон
            self.add_row_with_copy(self.frame_contacts,
                                   row, "Телефон:", data[4])
            row += 1
        if data[5]:  # Доп. телефон
            self.add_row_with_copy(self.frame_contacts,
                                   row, "Доп. тел:", data[5])
            row += 1
        if data[6]:  # Email
            self.add_row_with_copy(self.frame_contacts, row, "Email:", data[6])
            row += 1
        if data[7]:  # Адрес
            self.add_row_with_copy(self.frame_contacts, row, "Адрес:", data[7])
            row += 1

        # Заполнение блока "Соцсети"
        social_row = 0
        has_socials = False
        for i in range(0, 3):
            # Вычисляем индексы полей в кортеже данных
            base_idx = 8 + (i * 3)
            net, nick, link = data[base_idx], data[base_idx +
                                                   1], data[base_idx+2]
            if net:
                has_socials = True
                self.add_social_row(self.frame_socials,
                                    social_row, net, nick, link)
                social_row += 1
        if not has_socials:
            tk.Label(self.frame_socials, text="Нет данных",
                     fg="gray").pack(pady=5)

        # Заполнение блока "Информация"
        info_row = 0
        self.add_row_simple(self.frame_info, info_row, "Категория:", data[20])
        info_row += 1

        if len(data) > 21 and data[21]:
            self.add_row_simple(self.frame_info, info_row,
                                "День рождения:", data[21])
            info_row += 1

        if data[17]:  # Заметки
            tk.Label(self.frame_info, text="Заметки:", font=("Arial", 9, "bold")).grid(
                row=info_row, column=0, sticky="nw", padx=5, pady=2)
            lbl_note = tk.Label(
                self.frame_info, text=data[17], wraplength=350, justify="left")
            lbl_note.grid(row=info_row, column=1, sticky="w", padx=5, pady=2)
            info_row += 1

        self.add_row_simple(self.frame_info, info_row, "Добавлен:", data[18])

    def add_row_with_copy(self, parent, row, label, value):
        """Строка с данными и кнопкой копирования."""
        tk.Label(parent, text=label, font=("Arial", 9, "bold")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2)
        tk.Label(parent, text=value, font=("Arial", 10)).grid(
            row=row, column=1, sticky="w", padx=5, pady=2)
        btn_copy = tk.Button(parent, text="📋", width=2, relief="flat", bg="#eee",
                             cursor="hand2", command=lambda: self.copy_to_clipboard(value))
        btn_copy.grid(row=row, column=2, padx=5)

    def add_social_row(self, parent, row, net, nick, link):
        """Строка соцсети (ссылка кликабельна)."""
        tk.Label(parent, text=f"{net}:", font=("Arial", 9, "bold")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2)

        display_text = nick if nick else (link if link else "Ссылка")

        lbl_link = tk.Label(parent, text=display_text, fg="blue",
                            cursor="hand2", font=("Arial", 10, "underline"))
        lbl_link.grid(row=row, column=1, sticky="w", padx=5, pady=2)

        # Если есть ссылка, делаем кликабельной
        if link:
            lbl_link.bind("<Button-1>", lambda e: webbrowser.open(link))
        else:
            lbl_link.config(fg="black", font=("Arial", 10), cursor="arrow")

        # Кнопка копирования
        val_to_copy = link if link else nick
        if val_to_copy:
            btn_copy = tk.Button(parent, text="📋", width=2, relief="flat", bg="#eee",
                                 cursor="hand2", command=lambda: self.copy_to_clipboard(val_to_copy))
            btn_copy.grid(row=row, column=2, padx=5)

    def add_row_simple(self, parent, row, label, value):
        """Простая строка без кнопок."""
        tk.Label(parent, text=label, font=("Arial", 9, "bold")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2)
        tk.Label(parent, text=value).grid(
            row=row, column=1, sticky="w", padx=5, pady=2)

    def copy_to_clipboard(self, text):
        """Копирование в буфер."""
        self.clipboard_clear()
        self.clipboard_append(text)

    def go_to_edit(self):
        """Закрывает просмотр и открывает редактирование."""
        self.destroy()
        self.on_edit_request(self.contact_id)

    def delete_me(self):
        """Удаляет текущий контакт."""
        if messagebox.askyesno("Удаление", "Удалить этот контакт?"):
            self.on_delete_request([self.contact_id])
            self.destroy()
