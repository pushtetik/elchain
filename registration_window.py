import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
def open_registration_window():
    registration_window = tk.Toplevel()
    registration_window.title("Регистрация нового пользователя")
    registration_window.geometry("500x700")
    registration_window.resizable(False, False)
    registration_window.grab_set()
    main_frame = ttk.Frame(registration_window)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    credentials_frame = ttk.LabelFrame(scrollable_frame, text="Учетные данные", padding=10)
    credentials_frame.pack(fill='x', pady=5)
    ttk.Label(credentials_frame, text="Логин*:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
    username_entry = ttk.Entry(credentials_frame)
    username_entry.grid(row=0, column=1, sticky='we', padx=5, pady=5)
    ttk.Label(credentials_frame, text="Пароль*:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
    password_entry = ttk.Entry(credentials_frame, show="*")
    password_entry.grid(row=1, column=1, sticky='we', padx=5, pady=5)
    ttk.Label(credentials_frame, text="Повторите пароль*:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
    confirm_password_entry = ttk.Entry(credentials_frame, show="*")
    confirm_password_entry.grid(row=2, column=1, sticky='we', padx=5, pady=5)
    info_frame = ttk.LabelFrame(scrollable_frame, text="Персональная информация", padding=10)
    info_frame.pack(fill='x', pady=5)
    fields = [
        ("Фамилия*:", "last_name"),
        ("Имя*:", "first_name"),
        ("Отчество:", "middle_name"),
        ("Организация:", "organization"),
        ("Email:", "email")
    ]
    entries = {}
    for i, (label, field) in enumerate(fields):
        ttk.Label(info_frame, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=5)
        entry = ttk.Entry(info_frame)
        entry.grid(row=i, column=1, sticky='we', padx=5, pady=5)
        entries[field] = entry
    phones_frame = ttk.LabelFrame(scrollable_frame, text="Телефоны* (минимум один)", padding=10)
    phones_frame.pack(fill='x', pady=5)
    phone_columns = ("Телефон", "Действия")
    phones_tree = ttk.Treeview(phones_frame, columns=phone_columns, show="headings", height=3)
    for col in phone_columns:
        phones_tree.heading(col, text=col)
        phones_tree.column(col, width=120 if col == "Действия" else 200, anchor='center')
    phones_tree.pack(fill='x', pady=5)
    add_phone_frame = ttk.Frame(phones_frame)
    add_phone_frame.pack(fill='x', pady=5)
    ttk.Label(add_phone_frame, text="Новый телефон:").pack(side='left', padx=5)
    phone_entry = ttk.Entry(add_phone_frame)
    phone_entry.pack(side='left', expand=True, fill='x', padx=5)
    def add_phone():
        phone = phone_entry.get().strip()
        if not phone:
            messagebox.showerror("Ошибка", "Введите номер телефона")
            return
        if not phone.replace('+', '').isdigit():
            messagebox.showerror("Ошибка", "Телефон должен содержать только цифры")
            return
        # Проверка длины телефона (11 символов без +, или 12 с +)
        clean_phone = phone.replace('+', '')
        if len(clean_phone) != 11:
            messagebox.showerror("Ошибка", "Телефон должен содержать 11 цифр")
            return
        phone_id = phones_tree.insert("", "end", values=(phone, "Удалить"))
        phone_entry.delete(0, 'end')
    def remove_phone(event):
        selected_items = phones_tree.selection()
        if not selected_items:
            return
        item = selected_items[0]
        phones_tree.delete(item)
    phones_tree.bind("<Double-1>", remove_phone)
    add_button = ttk.Button(add_phone_frame, text="Добавить", command=add_phone)
    add_button.pack(side='left', padx=5)
    def is_valid_username(username):
        import re
        pattern = r'^[a-z0-9]+$'
        return re.match(pattern, username) is not None
    def is_valid_email(email):
        import re
        if not email:
            return True
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    def is_valid_russian_name(name):
        import re
        if not name:  # Пропускаем пустые строки (для необязательных полей)
            return True
        pattern = r'^[а-яА-ЯёЁ\s-]+$'
        return re.match(pattern, name) is not None
    def register_user():
        username = username_entry.get().strip()
        password = password_entry.get()
        confirm_password = confirm_password_entry.get()
        last_name = entries['last_name'].get().strip()
        first_name = entries['first_name'].get().strip()
        middle_name = entries['middle_name'].get().strip() or None
        organization = entries['organization'].get().strip() or None
        email = entries['email'].get().strip() or None
        phones = [phones_tree.item(item)['values'][0] for item in phones_tree.get_children()]
        if not all([username, password, confirm_password, last_name, first_name]):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля (помечены *)")
            return
        if not is_valid_username(username):
            messagebox.showerror("Ошибка", "Логин должен содержать только латинские буквы в нижнем регистре и цифры")
            return
        if password != confirm_password:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        if len(password) < 6:
            messagebox.showerror("Ошибка", "Пароль должен содержать минимум 6 символов")
            return
        if not is_valid_russian_name(last_name):
            messagebox.showerror("Ошибка", "Фамилия должна содержать только русские буквы")
            return
        if not is_valid_russian_name(first_name):
            messagebox.showerror("Ошибка", "Имя должно содержать только русские буквы")
            return
        if middle_name and not is_valid_russian_name(middle_name):
            messagebox.showerror("Ошибка", "Отчество должно содержать только русские буквы")
            return
        if not phones:
            messagebox.showerror("Ошибка", "Добавьте хотя бы один телефон")
            return
        if not is_valid_email(email):
            messagebox.showerror("Ошибка", "Указан невалидный email")
            return
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='pushtetik',
                password='12345678',
                database='elchain',
                charset='utf8mb4',
                use_unicode=True
            )
            cursor = conn.cursor(dictionary=True)
            normalized_username = username.lower()
            query = """
                    SELECT Username \
                    FROM User \
                    WHERE LOWER(Username) = %s
                    UNION
                    SELECT User AS role_name \
                    FROM mysql.user \
                    WHERE LOWER(User) = %s \
                    """
            cursor.execute(query, (normalized_username, normalized_username))
            existing_entry = cursor.fetchone()
            if existing_entry:
                messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")
                return
            if email:
                query_email = """SELECT Email 
                                 FROM Customer 
                                 WHERE LOWER(Email) = %s"""
                cursor.execute(query_email, (email.lower(),))
                if cursor.fetchone():
                    messagebox.showerror("Ошибка", "Пользователь с таким Email уже существует")
                    return
            for phone in phones:
                query_phone = """SELECT Phone 
                                 FROM CUSTOMER_PHONE 
                                 WHERE Phone = %s """
                cursor.execute(query_phone, (phone,))
                if cursor.fetchone():
                    messagebox.showerror("Ошибка", "Пользователь с таким телефоном уже существует")
                    return
            insert_customer = """INSERT INTO Customer
                                     (Last_Name, First_Name, Middle_Name, Organization, Email)
                                 VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(insert_customer,
                           (last_name, first_name, middle_name, organization, email))
            conn.commit()
            customer_id = cursor.lastrowid
            insert_user = """INSERT INTO User
                                 (ID, Username, Password, Created_At)
                             VALUES (%s, %s, %s, NOW())"""
            cursor.execute(insert_user,
                           (customer_id, username, password))
            conn.commit()
            for phone in phones:
                insert_phone = """INSERT INTO CUSTOMER_PHONE
                                      (Customer_ID, Phone)
                                  VALUES (%s, %s)"""
                cursor.execute(insert_phone,
                               (customer_id, phone))
                conn.commit()
            create_user_sql = f"CREATE USER IF NOT EXISTS '{username}'@'localhost' IDENTIFIED BY %s"
            grant_role_sql = f"GRANT 'Customer' TO '{username}'@'localhost'"
            set_default_role_sql = f"SET DEFAULT ROLE 'Customer' TO '{username}'@'localhost'"
            flush_privileges_sql = "FLUSH PRIVILEGES"
            cursor.execute(create_user_sql, (password,))
            cursor.execute(grant_role_sql)
            cursor.execute(set_default_role_sql)
            cursor.execute(flush_privileges_sql)
            conn.commit()
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован")
            registration_window.destroy()
        except mysql.connector.Error as err:
            messagebox.showerror("Ошибка базы данных", f"Ошибка при создании пользователя: {err}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
    button_frame = ttk.Frame(scrollable_frame)
    button_frame.pack(fill='x', pady=10)
    register_button = ttk.Button(button_frame, text="Зарегистрироваться", command=register_user, style='Accent.TButton')
    register_button.pack(pady=10, ipadx=10, ipady=5)