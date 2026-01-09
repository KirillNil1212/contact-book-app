import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser  # Модуль для открытия ссылок в браузере по умолчанию


class AboutWindow(tk.Toplevel):
    """
    Класс окна 'О программе'. Наследуется от Toplevel (второстепенное окно).
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("О программе")
        self.geometry("600x650")
        self.resizable(False, False)  # Запрещаем менять размер окна

        # Делаем окно зависимым от родителя (свернется вместе с ним)
        self.transient(parent)
        self.center_window()  # Центрируем на экране

        # Создаем контейнер для виджетов
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем виджет Text для отображения форматированного текста
        # exportselection=0 нужен, чтобы выделение текста не сбрасывалось при потере фокуса
        self.text_area = tk.Text(main_frame, wrap=tk.WORD, padx=15, pady=15, bd=0, bg="#f9f9f9", font=(
            "Arial", 10), cursor="arrow", exportselection=0)

        # Добавляем полосу прокрутки
        scrollbar = ttk.Scrollbar(
            main_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        # Связываем скроллбар и текст друг с другом
        self.text_area.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Настраиваем стили (теги) для текста
        self.configure_tags()
        # Вставляем весь текст
        self.insert_content()
        # Блокируем текст от редактирования (read-only)
        self.text_area.config(state=tk.DISABLED)

        # Запрещаем выделение текста мышкой ("break" прерывает событие)
        self.text_area.bind("<B1-Motion>", lambda e: "break")
        # Но обрабатываем клики (для ссылок)
        self.text_area.bind("<Button-1>", self.handle_click)

        # Кнопка закрытия внизу
        btn_close = tk.Button(
            self, text="Закрыть", command=self.destroy, width=15, pady=5, cursor="hand2")
        btn_close.pack(pady=10)

    def handle_click(self, event):
        """Обработка клика по тексту. Если клик не по ссылке, блокируем его."""
        tags = self.text_area.tag_names(f"@{event.x},{event.y}")
        if "link" in tags:
            return  # Разрешаем клик, если это ссылка
        return "break"  # Иначе запрещаем выделение и установку курсора

    def center_window(self):
        """Вычисляет координаты для размещения окна по центру экрана."""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (600 // 2)
        y = (screen_height // 2) - (650 // 2)
        self.geometry(f"+{x}+{y}")

    def configure_tags(self):
        """
        Настройка стилей (тегов) для Text widget.
        Это похоже на CSS в вебе.
        """
        # Заголовки H1
        self.text_area.tag_configure("h1", font=(
            "Arial", 18, "bold"), justify="center", spacing3=10)
        # Заголовки H2
        self.text_area.tag_configure("h2", font=(
            "Arial", 12, "bold"), spacing1=15, spacing3=5)
        # Жирный шрифт
        self.text_area.tag_configure("bold", font=("Arial", 10, "bold"))
        # Блок "Миссия" (курсив, фон)
        self.text_area.tag_configure("mission", font=(
            "Georgia", 11, "italic"), lmargin1=20, lmargin2=20, background="#e8f5e9", spacing1=5, spacing3=5)
        # Обычный текст
        self.text_area.tag_configure("normal", font=("Arial", 10), spacing1=2)
        # Списки
        self.text_area.tag_configure("bullet", lmargin1=20, lmargin2=35)

        # Ссылки (синий цвет, подчеркивание, поведение мыши)
        self.text_area.tag_configure("link", foreground="blue", underline=1)
        self.text_area.tag_bind(
            "link", "<Enter>", lambda e: self.text_area.config(cursor="hand2"))
        self.text_area.tag_bind(
            "link", "<Leave>", lambda e: self.text_area.config(cursor="arrow"))
        # При клике открываем почтовую программу
        self.text_area.tag_bind(
            "link", "<Button-1>", lambda e: webbrowser.open("mailto:Kolmikol12@gmail.com"))

        # Контекстное меню для копирования email
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(
            label="Копировать Email", command=lambda: self.copy_to_clipboard("Kolmikol12@gmail.com"))
        # Привязка правой кнопки мыши
        self.text_area.tag_bind(
            "link", "<Button-3>", lambda e: self.context_menu.post(e.x_root, e.y_root))

    def copy_to_clipboard(self, text):
        """Копирует текст в буфер обмена."""
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Скопировано", f"Email скопирован:\n{text}")

    def insert_content(self):
        """
        Заполнение виджета текстом.
        Мы вставляем куски текста и сразу назначаем им теги (стили).
        """
        t = self.text_area
        t.insert(tk.END, "АДРЕСНИК\n", "h1")
        t.insert(tk.END, "АДРЕСНИК — это безопасная электронная записная книга для управления контактами, написанная на Python с использованием библиотеки Tkinter. Приложение предназначено для локального хранения конфиденциальных данных контактов в защищённом и организованном виде.\n\n", "normal")

        # Мета-данные
        t.insert(tk.END, "Версия: ", "bold")
        t.insert(tk.END, "1.0.0\n", "normal")
        t.insert(tk.END, "Разработчик: ", "bold")
        t.insert(tk.END, "Николаев Кирилл Викторович\n", "normal")
        t.insert(tk.END, "Студент 1 курса магистратуры ИТМО. Направление: \"Цифровые методы в гуманитарных исследованиях\"\n", "normal")
        t.insert(tk.END, "Год создания: ", "bold")
        t.insert(tk.END, "2026\n", "normal")
        t.insert(tk.END, "Email: ", "bold")
        # Здесь мы применяем тег "link", который делает текст интерактивным
        t.insert(tk.END, "Kolmikol12@gmail.com", "link")
        t.insert(tk.END, " (ПКМ - скопировать)\n", "normal")
        t.insert(tk.END, "Язык программирования: ", "bold")
        t.insert(tk.END, "Python 3.8+\n", "normal")
        t.insert(tk.END, "Графический интерфейс: ", "bold")
        t.insert(tk.END, "Tkinter\n", "normal")
        t.insert(tk.END, "Язык интерфейса: ", "bold")
        t.insert(tk.END, "Русский\n", "normal")

        # Миссия
        t.insert(tk.END, "Наша миссия\n", "h2")
        t.insert(tk.END, "Сделать управление контактами простым, надёжным и приятным.\nАдресник — это место, где ваши контакты в полной безопасности, быстро находятся, и никогда не будут потеряны.\n", "mission")
        t.insert(tk.END, "\nКаждый ваш контакт важен — будь то близкий друг, деловой партнёр или важная организация. АДРЕСНИК создан, чтобы:\n\n", "normal")

        # Списки
        t.insert(
            tk.END, "• Хранить — надёжно и безопасно, без риска утечки данных\n", "bullet")
        t.insert(
            tk.END, "• Искать — за доли секунды, без ненужных сложностей\n", "bullet")
        t.insert(
            tk.END, "• Управлять — легко и удобно, с минимальными усилиями\n", "bullet")

        # История (длинный текст разбитый на блоки)
        t.insert(tk.END, "История создания\n", "h2")
        t.insert(tk.END, "АДРЕСНИК родился из простой идеи: объединить привычку человека вести записную книгу с удобством современных технологий, решив проблемы обоих подходов.\n\n", "normal")
        t.insert(tk.END, "Физические записные книги имеют серьезные ограничения: нужно листать страницы, чтобы найти контакт, нельзя быстро поискать по номеру телефона или email, исправления выглядят неприглядно (помарки, зачеркивания), нет способа сделать резервную копию, и все контакты могут быть потеряны при потере книги.\n\n", "normal")
        t.insert(tk.END, "Электронные инструменты вроде Excel или Word тоже не идеальны: это просто таблицы и документы без нормальной базы данных, в них нет удобного поиска, фильтрации и организации контактов, а облачные сервисы (Google Sheets, Microsoft 365) сканируют и отслеживают содержимое ваших данных.\n\n", "normal")
        t.insert(tk.END, "Поэтому был создан АДРЕСНИК — приложение, которое объединяет надежность и простоту традиционной записной книги с мощью современных технологий: быстрый поиск, база данных, безопасное локальное хранение, резервное копирование, категоризация и импорт/экспорт контактов. Все это работает на вашем компьютере, без облака, без сканирования данных, без подписок — просто надежный инструмент для управления контактами.\n", "normal")

        # Контекст
        t.insert(tk.END, "Контекст: Digital Humanities\n", "h2")
        t.insert(tk.END, "АДРЕСНИК разработан в рамках Digital Humanities (Цифровые гуманитарные исследования). Проект демонстрирует, как принципы человеко-ориентированного дизайна и уважение к традиционным подходам (классическая записная книга) могут быть соединены с современными цифровыми технологиями для создания удобного и безопасного инструмента.\n\n", "normal")
        t.insert(tk.END, "Идея АДРЕСНИКА отражает суть DH — не просто оцифровка, а переосмысление традиционных практик через призму современных возможностей. Это демонстрирует, как технология может служить человеку, а не наоборот, и как традиционные методы управления информацией могут быть обогащены, но не заменены цифровыми инструментами.\n", "normal")

        # Возможности
        t.insert(tk.END, "Основные возможности\n", "h2")
        t.insert(tk.END, "Безопасность и конфиденциальность\n", "bold")
        t.insert(tk.END, "• Надежное управление контактами: Все контакты сохраняются в защищённую локальную базу данных SQLite.\n", "bullet")
        t.insert(tk.END, "• Локальное хранение — полная безопасность: Ваши контакты НЕ отправляются в облако. Все данные хранятся в contacts.db прямо на вашем компьютере.\n\n", "bullet")
        t.insert(tk.END, "Простота и удобство\n", "bold")
        t.insert(
            tk.END, "• Быстрый и удобный поиск: Мгновенный поиск по имени, телефону, email.\n", "bullet")
        t.insert(tk.END, "• Интуитивный интерфейс: Минималистичный дизайн, горячие клавиши, адаптивная раскладка.\n", "bullet")
        t.insert(tk.END, "• Удобное управление: Добавление, просмотр, редактирование и дублирование контактов.\n\n", "bullet")
        t.insert(tk.END, "Организация и структурирование\n", "bold")
        t.insert(
            tk.END, "• Категории контактов: Личные, Деловые, Сервисы и т.д.\n", "bullet")
        t.insert(
            tk.END, "• Группировка и сортировка: По имени, дате, категории, избранному.\n", "bullet")
        t.insert(
            tk.END, "• Заметки и комментарии: Доп. информация для каждого контакта.\n\n", "bullet")
        t.insert(tk.END, "Управление данными\n", "bold")
        t.insert(tk.END, "• Импорт контактов: CSV\n", "bullet")
        t.insert(tk.END, "• Экспорт: CSV для других программ\n", "bullet")
        t.insert(
            tk.END, "• Резервное копирование: Ручное создание бэкапов в указанную папку.\n\n", "bullet")

        # Подвал
        t.insert(tk.END, "Поддержка и обратная связь\n", "h2")
        t.insert(
            tk.END, "Если у вас есть предложения, вопросы или вы нашли ошибку:\nОтправьте email на почту: ", "normal")
        t.insert(tk.END, "Kolmikol12@gmail.com", "link")
        t.insert(tk.END, "\n", "normal")
        t.insert(tk.END, "\nСпасибо за использование АДРЕСНИКА!", "h2")
