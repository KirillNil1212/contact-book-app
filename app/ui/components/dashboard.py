import tkinter as tk
from tkinter import messagebox, simpledialog


class DashboardFrame(tk.Frame):
    """
    Панель дашборда с буфером и днями рождения.
    Поле буфера теперь корректно обрабатывается глобальным контроллером
    в main_window (работают Ctrl+A/C/V и русская раскладка).
    """

    def __init__(self, parent, db):
        super().__init__(parent, bg="#f0f0f0", pady=5, padx=10)
        self.db = db
        self.notes_window = None  # Ссылка на окно заметок (Singleton)
        self.pack(fill=tk.X)

        self.create_left_panel()
        self.create_right_panel()

    def create_left_panel(self):
        left_frame = tk.Frame(self, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(left_frame, text="📝 Буфер:", bg="#f0f0f0",
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT)

        # Валидатор длины (не более 60 символов)
        vcmd = (self.register(lambda s: len(s) <= 60), '%P')

        # Поле ввода для быстрых заметок
        self.scratch_entry = tk.Entry(
            left_frame, width=30, bg="white", bd=1, relief=tk.SOLID, validate="key", validatecommand=vcmd)
        self.scratch_entry.pack(side=tk.LEFT, padx=(5, 2))

        # Кнопки управления
        self.create_btn(left_frame, "💾", self.save_note)
        self.create_btn(left_frame, "📂", self.load_notes_dialog)
        self.create_btn(left_frame, "📋", self.copy_scratch)
        self.create_btn(left_frame, "✖",
                        lambda: self.scratch_entry.delete(0, tk.END))

    def create_btn(self, parent, text, cmd):
        tk.Button(parent, text=text, command=cmd, width=2, bg="#ddd",
                  relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=1)

    def create_right_panel(self):
        right_frame = tk.Frame(self, bg="#f0f0f0")
        right_frame.pack(side=tk.RIGHT)
        self.lbl_birthdays = tk.Label(
            right_frame, text="Загрузка...", bg="#f0f0f0", fg="#555", font=("Arial", 9))
        self.lbl_birthdays.pack(side=tk.RIGHT)
        self.update_birthdays_display()

    def update_birthdays_display(self):
        upcoming = self.db.get_upcoming_birthdays()
        if not upcoming:
            self.lbl_birthdays.config(text="🎉 Дни рождения: Нет ближайших")
        else:
            text_parts = []
            for delta, name, date_obj in upcoming[:2]:
                day_str = "сегодня!" if delta == 0 else (
                    "завтра" if delta == 1 else f"{date_obj.strftime('%d.%m')}")
                text_parts.append(f"{name} ({day_str})")
            full_text = "🎉 " + ", ".join(text_parts)
            if len(upcoming) > 2:
                full_text += f" и еще {len(upcoming)-2}"
            self.lbl_birthdays.config(text=full_text, fg="#E91E63")

    def copy_scratch(self):
        txt = self.scratch_entry.get()
        if txt:
            self.clipboard_clear()
            self.clipboard_append(txt)

    def save_note(self):
        text = self.scratch_entry.get().strip()
        if not text:
            return
        name = simpledialog.askstring(
            "Сохранить заметку", "Введите название заметки:")
        if name:
            if self.db.save_note(name, text):
                messagebox.showinfo("Успех", "Заметка сохранена")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить")

    def load_notes_dialog(self):
        # Проверка, открыто ли уже окно
        if self.notes_window and self.notes_window.winfo_exists():
            self.notes_window.lift()
            return

        notes = self.db.get_all_notes()
        if not notes:
            messagebox.showinfo("Заметки", "Нет сохраненных заметок")
            return

        self.notes_window = tk.Toplevel(self)
        self.notes_window.title("Сохраненные заметки")
        self.notes_window.geometry("400x300")
        self.notes_window.resizable(False, False)

        lb = tk.Listbox(self.notes_window, width=50, height=15)
        lb.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        for n in notes:
            lb.insert(tk.END, f"{n[1]} ({n[2]})")

        def on_select(event=None):
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            note_content = notes[idx][2]
            self.scratch_entry.delete(0, tk.END)
            self.scratch_entry.insert(0, note_content)
            self.notes_window.destroy()

        def delete_note():
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            if messagebox.askyesno("Удалить", "Удалить эту заметку?"):
                self.db.delete_note(notes[idx][0])
                self.notes_window.destroy()
                # Сбрасываем ссылку, чтобы можно было открыть снова
                self.notes_window = None
                self.load_notes_dialog()

        lb.bind("<Double-Button-1>", on_select)

        btn_frame = tk.Frame(self.notes_window)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Вставить", command=on_select,
                  cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Удалить", command=delete_note,
                  fg="red", cursor="hand2").pack(side=tk.LEFT, padx=5)
