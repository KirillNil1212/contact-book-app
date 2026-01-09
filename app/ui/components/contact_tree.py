import tkinter as tk
from tkinter import ttk


class ContactTableFrame(tk.Frame):
    """
    Фрейм, содержащий таблицу контактов и полосу прокрутки.
    Принимает callback-функции, чтобы передавать управление в ContactApp при кликах.
    """

    def __init__(self, parent, on_click_callback, on_double_click_callback, on_right_click_callback):
        super().__init__(parent)
        # Растягиваем фрейм на все доступное пространство
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.create_tree(on_click_callback,
                         on_double_click_callback, on_right_click_callback)

    def create_tree(self, on_click, on_dbl_click, on_r_click):
        """Создание и настройка виджета Treeview."""

        # Определяем внутренние имена колонок
        columns = ("select", "fio", "phone", "email",
                   "social", "category", "date_add")

        # show="headings" скрывает пустой нулевой столбец (дерево), оставляя только заголовки
        # selectmode="none" отключает встроенное синее выделение (мы делаем свое через теги)
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", selectmode="none")

        # Настройка визуальных тегов для строк
        # Цвет выделенной строки
        self.tree.tag_configure("selected", background="#e1f5fe")
        self.tree.tag_configure(
            "normal", background="white")     # Обычный цвет

        # --- Настройка колонок (ширина и выравнивание) ---
        # Колонка с чекбоксом (узкая, без растяжения)
        self.tree.column("select", width=30, minwidth=30,
                         stretch=False, anchor="center")
        # ФИО (растягивается - stretch=True)
        self.tree.column("fio", width=180, minwidth=150, stretch=True)
        self.tree.column("phone", width=140, minwidth=100, stretch=False)
        self.tree.column("email", width=200, minwidth=100, stretch=False)
        self.tree.column("social", width=140, minwidth=100, stretch=False)
        self.tree.column("category", width=100, minwidth=80, stretch=False)
        self.tree.column("date_add", width=150, minwidth=120, stretch=False)

        # --- Настройка заголовков (текст в шапке) ---
        self.tree.heading("select", text="☐")  # Пустой чекбокс в заголовке

        headers = ["ФИО", "Телефон", "Email",
                   "Соц. сети", "Категория", "Добавлен"]
        cols_data = ["fio", "phone", "email", "social", "category", "date_add"]

        for col, h in zip(cols_data, headers):
            self.tree.heading(col, text=h)

        # --- Полоса прокрутки (Scrollbar) ---
        sb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        # Связываем таблицу со скроллбаром
        self.tree.configure(yscroll=sb.set)

        # Размещаем таблицу слева, скроллбар справа
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Привязка событий мыши ---
        self.tree.bind("<Button-1>", on_click)      # ЛКМ (выделение)
        self.tree.bind("<Double-1>", on_dbl_click)  # Двойной ЛКМ (просмотр)
        self.tree.bind("<Button-3>", on_r_click)    # ПКМ (контекстное меню)

    def clear(self):
        """Удаляет все строки из таблицы (перед обновлением)."""
        for row in self.tree.get_children():
            self.tree.delete(row)

    def insert_contact(self, cid, values, tag="normal"):
        """Вставляет новую строку. iid=cid позволяет использовать ID из БД как ID строки таблицы."""
        self.tree.insert("", tk.END, iid=cid, values=values, tags=(tag,))

    def update_header_checkbox(self, is_checked):
        """Меняет значок чекбокса в заголовке (выбрано всё или нет)."""
        char = "☑" if is_checked else "☐"
        self.tree.heading("select", text=char)
