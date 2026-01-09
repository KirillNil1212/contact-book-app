import tkinter as tk


class MainMenu:
    """
    Класс управления главным меню.
    """

    def __init__(self, root, app):
        self.root = root
        # Ссылка на ContactApp (контроллер), чтобы вызывать его методы
        self.app = app
        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)  # Привязываем меню к окну

        # --- Меню "Файл" ---
        # tearoff=0 убирает пунктирную линию отрыва
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Новый контакт", command=self.app.open_add_dialog, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт в CSV...",
                              command=self.app.export_csv, accelerator="Ctrl+S")
        file_menu.add_command(label="Импорт из CSV...",
                              command=self.app.import_csv, accelerator="Ctrl+O")
        file_menu.add_command(label="Создать резервную копию",
                              command=self.app.create_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)

        menubar.add_cascade(label="Файл", menu=file_menu)

        # --- Меню "Правка" ---
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(
            label="Выбрать всё", command=self.app.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="Снять выделение",
                              command=self.app.deselect_all)

        menubar.add_cascade(label="Правка", menu=edit_menu)

        # --- Меню "Вид" ---
        view_menu = tk.Menu(menubar, tearoff=0)

        # Подменю масштаба
        zoom_menu = tk.Menu(view_menu, tearoff=0)
        # Переменная для хранения текущего масштаба
        self.app.scale_var = tk.IntVar(value=100)

        # Генерируем пункты меню масштаба циклом
        for scale in [50, 75, 90, 100, 110, 125, 150]:
            zoom_menu.add_radiobutton(label=f"{scale}%", variable=self.app.scale_var,
                                      value=scale, command=lambda s=scale: self.app.set_scale(s))
        view_menu.add_cascade(label="Масштаб", menu=zoom_menu)
        view_menu.add_separator()

        # Переменные состояния для чекбоксов в меню
        self.app.compact_var = tk.BooleanVar(value=True)
        self.app.maximized_var = tk.BooleanVar(value=False)
        self.app.fullscreen_var = tk.BooleanVar(value=False)

        view_menu.add_checkbutton(
            label="Компактный вид", variable=self.app.compact_var, command=self.app.toggle_compact)
        view_menu.add_checkbutton(label="Развернуть на весь экран",
                                  variable=self.app.maximized_var, command=self.app.toggle_maximize)
        view_menu.add_checkbutton(
            label="Полноэкранный режим", variable=self.app.fullscreen_var, command=self.app.toggle_fullscreen)

        menubar.add_cascade(label="Вид", menu=view_menu)

        # --- Меню "Сервис" ---
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Статистика базы",
                               command=self.app.show_statistics)
        tools_menu.add_command(label="Поиск дубликатов",
                               command=self.app.show_duplicates)
        tools_menu.add_separator()
        tools_menu.add_command(label="Очистить базу",
                               command=self.app.clear_all_data)

        menubar.add_cascade(label="Сервис", menu=tools_menu)

        # --- Меню "Справка" ---
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Горячие клавиши",
                              command=self.app.show_hotkeys)
        help_menu.add_command(label="О программе", command=self.app.show_about)

        menubar.add_cascade(label="Справка", menu=help_menu)
