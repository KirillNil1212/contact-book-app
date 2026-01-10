import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import csv
import os
import sys  # Нужно для доступа к системным переменным PyInstaller

# Импорт диалоговых окон
from .about import AboutWindow
from .forms import ContactFormWindow
from .view import ViewContactWindow

# Импорт компонентов
from .components.main_menu import MainMenu
from .components.dashboard import DashboardFrame
from .components.contact_tree import ContactTableFrame


def resource_path(relative_path):
    """
    Получает абсолютный путь к ресурсам.
    Работает и для режима разработки (dev), и для PyInstaller (onefile).
    """
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Если запускаем просто скрипт, берем текущую папку
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class ContactApp:
    """
    Основной контроллер приложения.
    Управляет главным окном, логикой взаимодействия компонентов и горячими клавишами.
    """

    def __init__(self, root, db_instance):
        self.root = root
        self.db = db_instance

        # Добавляем тестовые данные, если база пустая (можно убрать в продакшене)
        self.db.add_test_data()

        # Хранение ID выбранных контактов
        self.selected_ids = set()
        self.current_view_window = None

        # Список категорий для фильтрации
        self.categories_list = ["Не распределён", "Работа", "Семья",
                                "Друзья", "Знакомые", "Клиенты", "Учеба", "Избранное"]

        # Настройка окна и стилей
        self.setup_window()
        self.configure_styles()

        # --- Инициализация компонентов UI ---
        self.menu_manager = MainMenu(self.root, self)
        self.dashboard = DashboardFrame(self.root, self.db)

        self.create_toolbar()
        self.create_filters()

        # Таблица контактов
        self.table_frame = ContactTableFrame(
            self.root,
            on_click_callback=self.on_tree_click,
            on_double_click_callback=self.on_tree_double_click,
            on_right_click_callback=self.show_table_context_menu
        )
        self.tree = self.table_frame.tree

        self.create_statusbar()
        self.create_context_menus()

        # Привязка горячих клавиш
        self.bind_hotkeys()

        # Снятие фокуса/закрытие окон при клике в пустоту
        self.root.bind("<Button-1>", self.on_root_click)

        # Первичная загрузка данных
        self.load_contacts()

    def setup_window(self):
        """Базовая настройка главного окна."""
        self.root.title("Адресник v1.0")
        self.width = 1100
        self.height = 600
        self.min_width = 900
        self.min_height = 500
        self.root.geometry(f"{self.width}x{self.height}")
        self.center_window()
        self.set_app_icon()  # Установка иконки

        # Настройка шрифтов по умолчанию
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(size=10)
        self.root.option_add("*Font", self.default_font)

    def set_app_icon(self):
        """
        Установка иконки окна.
        Использует resource_path для корректной работы внутри EXE.
        """
        try:
            # Ищем иконку внутри упакованного приложения или в папке проекта
            # Важно: путь "assets/..." должен совпадать с тем, что указали в --add-data
            icon_path = resource_path(os.path.join("assets", "cont_icon.gif"))

            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                # True распространяет иконку на все дочерние окна
                self.root.iconphoto(True, icon)
            else:
                print(f"Warning: Иконка не найдена по пути {icon_path}")
        except Exception as e:
            print(f"Error setting icon: {e}")

    def center_window(self):
        """Центрирование окна на мониторе."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (self.width // 2)
        y = (screen_height // 2) - (self.height // 2)
        self.root.geometry(f"+{x}+{y}")

    def configure_styles(self):
        """Настройка стилей для Treeview (таблицы)."""
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("Arial", 10), rowheight=25)
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def create_toolbar(self):
        """Создание панели инструментов с кнопками действий."""
        self.toolbar_frame = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        self.toolbar_frame.pack(fill=tk.X)

        self.create_tb_btn("Добавить", self.open_add_dialog, "#e1f5fe")
        self.btn_view = self.create_tb_btn(
            "Просмотр", self.view_contact, bg="#e8f5e9", state="disabled")
        self.btn_edit = self.create_tb_btn(
            "Редактировать", self.edit_contact, bg="#fff3e0", state="disabled")
        self.btn_delete = self.create_tb_btn(
            "Удалить", self.delete_selected, bg="#ffebee", state="disabled")

    def create_tb_btn(self, text, cmd, bg=None, state="normal"):
        """Вспомогательный метод для кнопки тулбара."""
        btn = tk.Button(self.toolbar_frame, text=text,
                        command=cmd, width=12, state=state, cursor="hand2")
        if bg:
            btn.config(bg=bg)
        btn.pack(side=tk.LEFT, padx=2, pady=5)
        return btn

    def create_filters(self):
        """Создание панели фильтров и поиска."""
        filter_frame = tk.Frame(self.root, pady=10)
        filter_frame.pack(fill=tk.X, padx=10)

        # Поле поиска
        tk.Label(filter_frame, text="Поиск:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_search = tk.Entry(filter_frame, width=25)
        self.entry_search.pack(side=tk.LEFT, padx=(0, 15))
        self.entry_search.bind("<KeyRelease>", self.refresh_table_with_filter)

        # Фильтр категорий
        self.combo_category = ttk.Combobox(filter_frame, values=[
                                           "Все категории"] + self.categories_list, state="readonly", width=15)
        self.combo_category.current(0)
        self.combo_category.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_category.bind(
            "<<ComboboxSelected>>", self.refresh_table_with_filter)

        # Сортировка
        sort_options = ["По ФИО (А-Я)", "По ФИО (Я-А)", "По дате добавления (новые)",
                        "По дате изменения (свежие)", "По дате изменения (старые)", "По основному телефону"]
        self.combo_sort = ttk.Combobox(
            filter_frame, values=sort_options, state="readonly", width=25)
        self.combo_sort.current(0)
        self.combo_sort.pack(side=tk.LEFT)
        self.combo_sort.bind("<<ComboboxSelected>>",
                             self.refresh_table_with_filter)

    def create_statusbar(self):
        """Создание строки состояния (внизу)."""
        status_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.lbl_count = tk.Label(
            status_frame, text="Всего: 0", bd=1, relief=tk.SUNKEN, width=20)
        self.lbl_count.pack(side=tk.RIGHT)
        self.lbl_selected = tk.Label(
            status_frame, text="Выбрано: 0", bd=1, relief=tk.SUNKEN, width=15)
        self.lbl_selected.pack(side=tk.RIGHT)

    def create_context_menus(self):
        """Создание контекстных меню (ПКМ)."""
        # Меню для таблицы
        self.context_menu_table = tk.Menu(self.root, tearoff=0)
        self.context_menu_table.add_command(
            label="👁 Просмотр", command=self.view_contact)
        self.context_menu_table.add_command(
            label="✏️ Редактировать", command=self.edit_contact)
        self.context_menu_table.add_command(
            label="🗑 Удалить", command=self.delete_selected)
        self.context_menu_table.add_separator()
        self.context_menu_table.add_command(
            label="Копировать телефон", command=lambda: self.copy_from_row("phone"))
        self.context_menu_table.add_command(
            label="Копировать Email", command=lambda: self.copy_from_row("email"))
        self.context_menu_table.add_command(
            label="Копировать ФИО", command=lambda: self.copy_from_row("fio"))

        # Меню для поля поиска
        self.context_menu_search = tk.Menu(self.root, tearoff=0)
        self.context_menu_search.add_command(
            label="Очистить", command=lambda: self.entry_search.delete(0, tk.END))
        self.entry_search.bind(
            "<Button-3>", lambda e: self.context_menu_search.post(e.x_root, e.y_root))

    def bind_hotkeys(self):
        """Привязка глобальных горячих клавиш."""
        self.root.bind("<Control-Key>", self.handle_ctrl_key)
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<F5>", lambda e: self.refresh_table_with_filter())
        self.root.bind("<Return>", lambda e: self.view_contact())
        self.root.bind(
            "<Escape>", lambda e: self.entry_search.delete(0, tk.END))

    def handle_ctrl_key(self, event):
        """
        Умная обработка Ctrl+...
        Разделяет логику для полей ввода (copy/paste) и команд приложения.
        """
        code = event.keycode
        widget = self.root.focus_get()

        # --- Если фокус в текстовом поле (Entry, Combobox, Text) ---
        if isinstance(widget, (tk.Entry, ttk.Combobox, tk.Text)):

            # Ctrl+A (Select All)
            if code == 65:
                if isinstance(widget, (tk.Entry, ttk.Combobox)):
                    widget.select_range(0, tk.END)
                    widget.icursor(tk.END)
                elif isinstance(widget, tk.Text):
                    widget.tag_add("sel", "1.0", "end")
                return "break"  # Прерываем, чтобы не сработало выделение таблицы

            # Стандартные команды буфера обмена (для русской раскладки)
            elif code == 67:  # Ctrl+C
                widget.event_generate("<<Copy>>")
                return "break"
            elif code == 86:  # Ctrl+V
                widget.event_generate("<<Paste>>")
                return "break"
            elif code == 88:  # Ctrl+X
                widget.event_generate("<<Cut>>")
                return "break"
            elif code == 90:  # Ctrl+Z
                try:
                    widget.event_generate("<<Undo>>")
                except:
                    pass
                return "break"

            # Если нажали другую комбинацию (например Ctrl+S), пропускаем дальше

        # --- Глобальные команды приложения ---

        # Ctrl+N (New Contact)
        if code == 78:
            self.open_add_dialog()
            return "break"

        # Ctrl+F (Find)
        elif code == 70:
            self.entry_search.focus_set()
            return "break"

        # Ctrl+S (Export)
        elif code == 83:
            self.export_csv()
            return "break"

        # Ctrl+O (Import)
        elif code == 79:
            self.import_csv()
            return "break"

        # Ctrl+A (Select All Table) - только если фокус НЕ в поле ввода
        elif code == 65:
            self.select_all()
            return "break"

    def set_scale(self, scale_percent):
        """Изменение масштаба интерфейса."""
        new_size = int(10 * (scale_percent / 100))
        self.default_font.configure(size=new_size)
        new_row_height = int(25 * (scale_percent / 100))
        self.style.configure("Treeview", font=(
            "Arial", new_size), rowheight=new_row_height)
        self.style.configure("Treeview.Heading",
                             font=("Arial", new_size, "bold"))
        self.root.update()

    def toggle_fullscreen(self):
        """Переключение полноэкранного режима."""
        is_full = self.fullscreen_var.get()
        self.root.attributes("-fullscreen", is_full)
        if is_full:
            self.compact_var.set(False)
            self.maximized_var.set(False)

    def toggle_maximize(self):
        """Переключение развернутого окна."""
        if self.maximized_var.get():
            self.root.state('zoomed')
            self.compact_var.set(False)
            self.fullscreen_var.set(False)
            self.root.attributes("-fullscreen", False)
        else:
            self.root.state('normal')

    def toggle_compact(self):
        """Переключение компактного вида."""
        if self.compact_var.get():
            self.root.state('normal')
            self.root.attributes("-fullscreen", False)
            self.root.geometry(f"{self.width}x{self.height}")
            self.root.resizable(False, False)
        else:
            self.root.resizable(True, True)
            self.root.minsize(self.min_width, self.min_height)

    def load_contacts(self, search_text="", category="Все категории", sort_by="По ФИО (А-Я)"):
        """Загрузка контактов из БД в таблицу."""
        self.selected_ids.clear()
        self.update_buttons_state()
        self.table_frame.clear()

        contacts = self.db.get_contacts(search_text, category, sort_by)
        for row in contacts:
            full_name = f"{row[1]} {row[2]} {row[3] if row[3] else ''}".strip()
            social = f"{row[8] if row[8] else ''} {row[9] if row[9] else ''}".strip()
            self.table_frame.insert_contact(
                row[0], ("☐", full_name, row[4], row[6], social, row[20], row[18]))

        self.lbl_count.config(text=f"Всего: {len(contacts)}")
        self.dashboard.update_birthdays_display()

    def refresh_table_with_filter(self, event=None):
        """Обновление таблицы с учетом текущих фильтров."""
        search_text = self.entry_search.get().strip()
        category = self.combo_category.get()
        sort_val = self.combo_sort.get()
        self.load_contacts(search_text, category, sort_val)

    def on_root_click(self, event):
        """Обработка клика мимо окон."""
        if self.current_view_window and self.current_view_window.winfo_exists():
            widget = event.widget
            if str(widget).startswith(str(self.toolbar_frame)):
                return
            self.current_view_window.destroy()
            self.current_view_window = None

    def on_tree_click(self, event):
        """Клик по строке таблицы."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            return
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            self.deselect_all()
            return

        is_ctrl_pressed = (event.state & 4) != 0
        if is_ctrl_pressed:
            if int(item_id) in self.selected_ids:
                self.selected_ids.remove(int(item_id))
                self.set_row_checked(item_id, False)
            else:
                self.selected_ids.add(int(item_id))
                self.set_row_checked(item_id, True)
        else:
            self.deselect_all()
            self.selected_ids.add(int(item_id))
            self.set_row_checked(item_id, True)
        self.update_buttons_state()

    def set_row_checked(self, item_id, checked):
        """Визуальное выделение строки (галочка и цвет)."""
        current_values = self.tree.item(item_id, "values")
        char = "☑" if checked else "☐"
        tag = "selected" if checked else "normal"
        self.tree.item(item_id, values=(char,) +
                       current_values[1:], tags=(tag,))

    def on_tree_double_click(self, event):
        """Двойной клик - открытие просмотра."""
        item_id = self.tree.identify_row(event.y) or self.tree.focus()
        if not item_id:
            return
        self.deselect_all()
        self.selected_ids.add(int(item_id))
        self.set_row_checked(item_id, True)
        self.update_buttons_state()
        self.view_contact()
        return "break"

    def show_table_context_menu(self, event):
        """Контекстное меню таблицы."""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            if int(item_id) not in self.selected_ids:
                self.deselect_all()
                self.selected_ids.add(int(item_id))
                self.set_row_checked(item_id, True)
                self.update_buttons_state()
            self.context_menu_table.post(event.x_root, event.y_root)

    def select_all(self):
        """Выбрать все строки."""
        self.selected_ids.clear()
        for item_id in self.tree.get_children():
            self.selected_ids.add(int(item_id))
            self.set_row_checked(item_id, True)
        self.update_buttons_state()

    def deselect_all(self):
        """Снять выделение."""
        for item_id in self.tree.get_children():
            self.set_row_checked(item_id, False)
        self.selected_ids.clear()
        self.update_buttons_state()

    def update_buttons_state(self):
        """Активация кнопок в зависимости от выделения."""
        count = len(self.selected_ids)
        self.lbl_selected.config(text=f"Выбрано: {count}")
        self.table_frame.update_header_checkbox(count > 0)

        state = "normal" if count > 0 else "disabled"
        single_state = "normal" if count == 1 else "disabled"

        self.btn_delete.config(state=state)
        self.btn_edit.config(state=single_state)
        self.btn_view.config(state=single_state)

    def open_add_dialog(self, event=None):
        """Открыть окно добавления."""
        self.deselect_all()
        ContactFormWindow(self.root, self.db,
                          lambda: self.refresh_table_with_filter())

    def view_contact(self, event=None):
        """Открыть окно просмотра."""
        if len(self.selected_ids) != 1:
            return
        contact_id = list(self.selected_ids)[0]
        if self.current_view_window and self.current_view_window.winfo_exists():
            self.current_view_window.destroy()
        self.current_view_window = ViewContactWindow(
            self.root, self.db, contact_id, self.open_edit_from_view, self.db.delete_contacts)

    def open_edit_from_view(self, contact_id):
        """Переход к редактированию из окна просмотра."""
        ContactFormWindow(
            self.root, self.db, lambda: self.refresh_table_with_filter(), contact_id=contact_id)

    def edit_contact(self):
        """Редактировать выбранный контакт."""
        if len(self.selected_ids) != 1:
            return
        contact_id = list(self.selected_ids)[0]
        ContactFormWindow(
            self.root, self.db, lambda: self.refresh_table_with_filter(), contact_id=contact_id)

    def delete_selected(self):
        """Удаление выбранных."""
        count = len(self.selected_ids)
        if count == 0:
            return
        if messagebox.askyesno("Подтверждение", f"Удалить {count} контактов?"):
            self.db.delete_contacts(list(self.selected_ids))
            self.refresh_table_with_filter()

    def export_csv(self):
        """Экспорт в CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return
        contacts = self.db.get_contacts()
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                writer.writerow(["ID", "Фамилия", "Имя", "Отчество", "Телефон",
                                 "Email", "Категория", "Заметки", "Дата рождения"])
                for c in contacts:
                    writer.writerow(
                        [c[0], c[1], c[2], c[3], c[4], c[6], c[20], c[17], c[21]])
            messagebox.showinfo(
                "Экспорт", f"Успешно экспортировано {len(contacts)} контактов.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def import_csv(self):
        """Импорт из CSV."""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return
        try:
            with open(filename, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter=';')
                next(reader, None)
                count = 0
                for row in reader:
                    if len(row) < 5:
                        continue
                    birth_date = row[8] if len(row) > 8 else ""
                    data = [row[1], row[2], row[3] if len(row) > 3 else "", row[4], "", row[5] if len(
                        row) > 5 else "", "", "", "", "", "", "", "", "", "", "", row[7] if len(row) > 7 else "", row[6] if len(row) > 6 else "Не распределён", birth_date]
                    self.db.add_contact(data)
                    count += 1
            self.refresh_table_with_filter()
            messagebox.showinfo("Импорт", f"Импортировано {count} контактов.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def create_backup(self):
        """Бэкап базы данных."""
        success, msg = self.db.backup_db()
        if success:
            messagebox.showinfo("Backup", f"Резервная копия:\n{msg}")
        else:
            messagebox.showerror("Ошибка", msg)

    def show_statistics(self):
        """Окно статистики."""
        total, by_cat = self.db.get_statistics()
        msg = f"Всего: {total}\n\nПо категориям:\n"
        for cat, count in by_cat:
            msg += f"- {cat}: {count}\n"
        messagebox.showinfo("Статистика", msg)

    def show_duplicates(self):
        """Поиск дублей."""
        dups = self.db.find_duplicates()
        if not dups:
            messagebox.showinfo("Дубликаты", "Дубликатов не найдено.")
        else:
            msg = "Возможные дубли:\n\n"
            for d in dups:
                msg += f"{d[0]} {d[1]} ({d[2]})\n"
            messagebox.showinfo("Дубликаты", msg)

    def clear_all_data(self):
        """Очистка всей базы."""
        if messagebox.askyesno("ВНИМАНИЕ", "Удалить ВСЕ контакты?"):
            self.db.clear_database()
            self.refresh_table_with_filter()

    def show_about(self):
        """Окно 'О программе'."""
        AboutWindow(self.root)

    def show_hotkeys(self):
        """Справка по клавишам."""
        messagebox.showinfo(
            "Горячие клавиши", "Ctrl+N: Новый\nCtrl+F: Поиск\nDel: Удалить\nEnter: Просмотр\nCtrl+S: Экспорт")

    def copy_from_row(self, what):
        """Копирование данных из строки таблицы в буфер."""
        if len(self.selected_ids) != 1:
            return
        cid = list(self.selected_ids)[0]
        data = self.db.get_contact_by_id(cid)
        text = ""
        if what == "phone":
            text = data[4]
        elif what == "email":
            text = data[6]
        elif what == "fio":
            text = f"{data[1]} {data[2]} {data[3]}".strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
