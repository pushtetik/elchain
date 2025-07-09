import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from mysql.connector import Error
class ProfileManager:
    def __init__(self, connection, error_handler, parent_window):
        self.connection = connection
        self.error_handler = error_handler
        self.parent_window = parent_window
    def load_data(self):
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customer_user_view")
        user_data = cursor.fetchone()
        cursor.execute("SELECT * FROM customer_view")
        customer_data = cursor.fetchone()
        cursor.execute("SELECT * FROM customer_phone_view")
        phone_data = cursor.fetchall()
        cursor.close()
        return user_data, customer_data, phone_data
    def save_customer_changes(self, customer_data, first_name_var, last_name_var, middle_name_var,
                              organization_var, email_var):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           UPDATE customer_view
                           SET First_Name   = %s,
                               Last_Name    = %s,
                               Middle_Name  = %s,
                               Organization = %s,
                               Email        = %s
                           """, (
                               first_name_var.get(),
                               last_name_var.get(),
                               middle_name_var.get(),
                               organization_var.get(),
                               email_var.get(),
                           ))
            self.connection.commit()
            cursor.close()
            messagebox.showinfo("Успех", "Данные обновлены")
        except Error as e:
            self.error_handler.show_error("Ошибка", f"Не удалось обновить данные:\n{str(e)}")
    def update_phone_list(self, phones_listbox, customer_data):
        phones_listbox.delete(0, tk.END)
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customer_phone_view")
        for phone in cursor.fetchall():
            phones_listbox.insert(tk.END, phone['Phone'])
        cursor.close()
    def add_phone(self, new_phone_var, phones_listbox, customer_data):
        phone = new_phone_var.get()
        if not phone:
            self.error_handler.show_error("Ошибка", "Введите номер телефона")
            return
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           INSERT INTO customer_phone_view (Customer_ID, Phone)
                           VALUES (%s, %s)
                           """, (customer_data['ID'], phone))
            self.connection.commit()
            cursor.close()
            new_phone_var.set("")
            self.update_phone_list(phones_listbox, customer_data)
        except Error as e:
            self.error_handler.show_error("Ошибка", f"Не удалось добавить телефон:\n{str(e)}")
    def edit_phone(self, phones_listbox, customer_data):
        selection = phones_listbox.curselection()
        if not selection:
            self.error_handler.show_error("Ошибка", "Выберите телефон для изменения")
            return
        old_phone = phones_listbox.get(selection[0])
        new_phone = simpledialog.askstring("Изменение телефона", "Новый номер:", initialvalue=old_phone)
        if new_phone and new_phone != old_phone:
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                               UPDATE customer_phone_view
                               SET Phone = %s
                               WHERE Customer_ID = %s
                                 AND Phone = %s
                               """, (new_phone, customer_data['ID'], old_phone))
                self.connection.commit()
                cursor.close()
                self.update_phone_list(phones_listbox, customer_data)
            except Error as e:
                self.error_handler.show_error("Ошибка", f"Не удалось изменить телефон:\n{str(e)}")
    def delete_phone(self, phones_listbox, customer_data):
        selection = phones_listbox.curselection()
        if not selection:
            self.error_handler.show_error("Ошибка", "Выберите телефон для удаления")
            return
        if phones_listbox.size() <= 1:
            self.error_handler.show_error("Ошибка", "Нельзя удалить последний номер телефона")
            return
        phone = phones_listbox.get(selection[0])
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                           DELETE
                           FROM customer_phone_view
                           WHERE Phone = %s
                             AND Customer_ID = %s
                           """, (phone, customer_data['ID']))
            self.connection.commit()
            cursor.close()
            self.update_phone_list(phones_listbox, customer_data)
        except Error as e:
            self.error_handler.show_error("Ошибка", f"Не удалось удалить телефон:\n{str(e)}")
    def show_profile(self):
        try:
            user_data, customer_data, phone_data = self.load_data()
            if not user_data:
                self.error_handler.show_error("Ошибка", "Не удалось загрузить данные профиля")
                return
            profile_window = tk.Toplevel(self.parent_window)
            profile_window.title("Мой профиль")
            profile_window.geometry("700x700")
            profile_window.resizable(False, False)
            main_frame = ttk.Frame(profile_window, padding=20)
            main_frame.pack(fill='both', expand=True)
            ttk.Label(main_frame, text="Мой профиль", font=('Arial', 16, 'bold')).pack(pady=10)
            # Информация о пользователе
            user_frame = ttk.Frame(main_frame)
            user_frame.pack(fill='x', pady=10)
            ttk.Label(user_frame, text="Логин:", font=('Arial', 11, 'bold')).pack(anchor='w')
            ttk.Label(user_frame, text=user_data.get('Username', 'N/A')).pack(anchor='w')
            ttk.Label(user_frame, text="Дата регистрации:", font=('Arial', 11, 'bold')).pack(anchor='w')
            ttk.Label(user_frame, text=str(user_data.get('Created_At', 'N/A'))).pack(anchor='w')
            ttk.Label(user_frame, text="Пароль:", font=('Arial', 11, 'bold')).pack(anchor='w')
            ttk.Label(user_frame, text=str(user_data.get('Password', 'N/A'))).pack(anchor='w')
            # Редактируемые данные
            edit_frame = ttk.Frame(main_frame)
            edit_frame.pack(fill='x', pady=10)
            first_name_var = tk.StringVar(value=customer_data.get('First_Name', ''))
            last_name_var = tk.StringVar(value=customer_data.get('Last_Name', ''))
            middle_name_var = tk.StringVar(value=customer_data.get('Middle_Name', ''))
            organization_var = tk.StringVar(value=customer_data.get('Organization', ''))
            email_var = tk.StringVar(value=customer_data.get('Email', ''))
            new_phone_var = tk.StringVar()
            fields = [
                ("Имя:", first_name_var),
                ("Фамилия:", last_name_var),
                ("Отчество:", middle_name_var),
                ("Организация:", organization_var),
                ("Email:", email_var)
            ]
            for i, (label, var) in enumerate(fields):
                ttk.Label(edit_frame, text=label, font=('Arial', 11)).grid(row=i, column=0, sticky='w', pady=5)
                ttk.Entry(edit_frame, textvariable=var).grid(row=i, column=1, sticky='ew', padx=5, pady=5)
            phone_frame = ttk.Frame(main_frame)
            phone_frame.pack(fill='x', pady=10)
            ttk.Label(phone_frame, text="Телефоны:", font=('Arial', 11, 'bold')).pack(anchor='w')
            list_buttons_frame = ttk.Frame(phone_frame)
            list_buttons_frame.pack(fill='x')
            phones_listbox = tk.Listbox(list_buttons_frame, height=4, width=30)
            phones_listbox.pack(side='left')
            button_frame = ttk.Frame(list_buttons_frame)
            button_frame.pack(side='left', padx=10)
            ttk.Button(button_frame, text="Изменить",
                       command=lambda: self.edit_phone(phones_listbox, customer_data)).pack(pady=2)
            ttk.Button(button_frame, text="Удалить",
                       command=lambda: self.delete_phone(phones_listbox, customer_data)).pack(pady=2)
            for phone in phone_data:
                phones_listbox.insert(tk.END, phone['Phone'])
            add_frame = ttk.Frame(phone_frame)
            add_frame.pack(fill='x', pady=5)
            ttk.Label(add_frame, text="Добавить телефон:").pack(side='left')
            ttk.Entry(add_frame, textvariable=new_phone_var, width=25).pack(side='left', padx=5)
            ttk.Button(add_frame, text="Добавить",
                       command=lambda: self.add_phone(new_phone_var, phones_listbox, customer_data)).pack(side='left')
            ttk.Button(main_frame, text="Сохранить изменения",
                       command=lambda: self.save_customer_changes(
                           customer_data, first_name_var, last_name_var, middle_name_var,
                           organization_var, email_var)).pack(pady=10)
        except Error as e:
            self.error_handler.show_error("Ошибка", f"Не удалось загрузить профиль:\n{str(e)}")