import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from mysql.connector import Error
from PIL import Image, ImageTk
from profile import ProfileManager
from datetime import datetime
from receipt_generator import ReceiptGenerator
import traceback
from period_report import generate_period_report
from transaction_report import TransactionReportGenerator
from registration_window import open_registration_window
class ErrorWindow:
    def __init__(self, parent):
        self.parent = parent
    def show_error(self, title, message):
        error_window = tk.Toplevel(self.parent)
        error_window.title(title)
        error_window.geometry("400x200")
        error_window.resizable(False, False)
        error_window.grab_set()
        try:
            icon = Image.open("error_icon.png").resize((50, 50), Image.LANCZOS)
            icon_img = ImageTk.PhotoImage(icon)
            icon_label = ttk.Label(error_window, image=icon_img)
            icon_label.image = icon_img
            icon_label.pack(pady=(20, 10))
        except:
            icon_label = ttk.Label(error_window, text="⚠", font=('Arial', 24))
            icon_label.pack(pady=(20, 10))
        ttk.Label(error_window, text=title, font=('Arial', 12, 'bold')).pack()
        ttk.Label(error_window, text=message, wraplength=350, justify='center').pack(pady=10)
        self.center_window(error_window)
    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')
receipt_gen = ReceiptGenerator()
def run_login_window():
    root = tk.Tk()
    root.title("Электронные компоненты - Вход")
    root.geometry("400x550")
    root.resizable(False, False)
    def on_closing():
        root.quit()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    error_handler = ErrorWindow(root)
    style = ttk.Style()
    style.configure('TLabel', font=('Arial', 11))
    style.configure('TEntry', font=('Arial', 11), padding=5)
    style.configure('TButton', font=('Arial', 11), padding=5)
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(expand=True)
    try:
        logo = Image.open("logo2.png")
        logo = logo.resize((150, 150), Image.LANCZOS)
        logo_img = ImageTk.PhotoImage(logo)
        logo_label = ttk.Label(main_frame, image=logo_img)
        logo_label.image = logo_img
        logo_label.pack(pady=(0, 20))
    except FileNotFoundError:
        logo_label = ttk.Label(main_frame, text="Логотип", font=('Arial', 16, 'bold'))
        logo_label.pack(pady=(0, 20))
    login_frame = ttk.Frame(main_frame)
    login_frame.pack(pady=10)
    ttk.Label(login_frame, text="Имя пользователя:").pack(anchor='w')
    username_entry = ttk.Entry(login_frame, width=40)
    username_entry.pack(pady=(0, 10))
    ttk.Label(login_frame, text="Пароль:").pack(anchor='w')
    password_entry = ttk.Entry(login_frame, show="*", width=40)
    password_entry.pack(pady=(0, 20))
    def connect_to_db():
        username = username_entry.get()
        password = password_entry.get()
        if not username or not password:
            error_handler.show_error("Ошибка ввода", "Введите имя пользователя и пароль")
            return
        try:
            admin_connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='12345',
                database='mysql',
                charset='utf8mb4',
                use_unicode=True
            )
            if admin_connection.is_connected():
                cursor = admin_connection.cursor()
                cursor.execute("SELECT DEFAULT_ROLE_USER FROM mysql.default_roles WHERE USER = %s", (username,))
                role_result = cursor.fetchone()
                default_role = role_result[0] if role_result else None
                cursor.close()
                admin_connection.close()
                connection = mysql.connector.connect(
                    host='localhost',
                    user=username,
                    password=password,
                    database='elchain',
                    charset='utf8mb4',
                    use_unicode=True
                )
                if connection.is_connected():
                    cursor = connection.cursor()
                    if default_role:
                        cursor.execute(f"SET ROLE {default_role}")
                    cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE();")
                    user_info = cursor.fetchone()
                    current_user = user_info[0]
                    current_role = user_info[1] if user_info[1] else "нет роли"
                    cursor.execute("SHOW GRANTS")
                    grants = cursor.fetchall()
                    available_roles = []
                    for grant in grants:
                        if "GRANT `" in grant[0]:
                            role = grant[0].split("`")[1]
                            available_roles.append(role)
                    cursor.close()
                    root.withdraw()
                    if default_role == 'Customer':
                        show_customer_window(connection, error_handler, root, current_user, current_role)
                    else:
                        if default_role != 'Customer':
                            show_role_selection_for_employee(connection, error_handler, root, current_user,
                                                             default_role, available_roles)
                        else:
                            show_employee_window(connection, error_handler, root, current_user, default_role)
        except Error as e:
            error_handler.show_error("Ошибка подключения", f"Не удалось подключиться к базе:\n{str(e)}")
    login_button = ttk.Button(main_frame, text="Войти", command=connect_to_db, width=20)
    login_button.pack(pady=10)
    register_button = ttk.Button(main_frame, text="Регистрация", command=open_registration_window, width=20)
    register_button.pack(pady=10)
    root.mainloop()
def show_role_selection_for_employee(connection, error_handler, login_window, current_user, default_role,
                                     available_roles):
    role_window = tk.Toplevel()
    role_window.title("Выбор режима входа")
    role_window.geometry("400x300")
    role_window.resizable(False, False)
    def on_role_window_closing():
        try:
            if connection.is_connected():
                connection.close()
        except:
            pass
        try:
            if login_window.winfo_exists():
                login_window.destroy()
        except:
            pass
    role_window.protocol("WM_DELETE_WINDOW", on_role_window_closing)
    main_frame = ttk.Frame(role_window, padding=20)
    main_frame.pack(expand=True)
    ttk.Label(main_frame, text="Выберите режим входа:", font=('Arial', 14)).pack(pady=20)
    def select_customer_role():
        cursor = connection.cursor()
        try:
            cursor.execute("SET ROLE Customer")
            cursor.execute("SELECT CURRENT_ROLE();")
            new_role = cursor.fetchone()[0]
            role_window.destroy()
            show_customer_window(connection, error_handler, login_window, current_user, new_role)
        except Error as e:
            error_handler.show_error("Ошибка", f"Не удалось установить роль:\n{str(e)}")
        finally:
            cursor.close()
    def select_default_role():
        cursor = connection.cursor()
        try:
            cursor.execute(f"SET ROLE {default_role}")
            cursor.execute("SELECT CURRENT_ROLE();")
            new_role = cursor.fetchone()[0]
            role_window.destroy()
            show_employee_window(connection, error_handler, login_window, current_user, new_role)
        except Error as e:
            error_handler.show_error("Ошибка", f"Не удалось установить роль:\n{str(e)}")
        finally:
            cursor.close()
    ttk.Button(main_frame, text="Обычный покупатель", command=select_customer_role, width=20).pack(pady=5)
    ttk.Button(main_frame, text="Сотрудник", command=select_default_role, width=20).pack(pady=5)
def show_customer_window(connection, error_handler, login_window, current_user, current_role):
    customer_window = tk.Toplevel()
    customer_window.title("Электронные компоненты - Покупатель")
    customer_window.geometry("1200x800")
    customer_window.minsize(800, 600)
    def logout():
        try:
            if connection.is_connected():
                connection.close()
        except:
            pass
        customer_window.destroy()
        login_window.deiconify()
    def on_customer_window_closing():
        logout()
    customer_window.protocol("WM_DELETE_WINDOW", on_customer_window_closing)
    style = ttk.Style()
    style.configure('Customer.TFrame', background='#f0f0f0')
    style.configure('Menu.TButton', font=('Arial', 11, 'bold'), padding=10,
                    foreground='#333333', background='#e6e6e6', bordercolor='#cccccc')
    style.map('Menu.TButton',
              background=[('active', '#d9d9d9'), ('pressed', '#bfbfbf')],
              foreground=[('active', '#000000')])
    style.configure('Product.TFrame', background='white', borderwidth=1, relief='solid')
    style.configure('ProductName.TLabel', font=('Arial', 12, 'bold'), background='white')
    style.configure('ProductPrice.TLabel', font=('Arial', 11), background='white', foreground='#e74c3c')
    style.configure('ProductDesc.TLabel', font=('Arial', 10), background='white', foreground='#555555')
    style.configure('LoadMore.TButton', font=('Arial', 10), padding=5)
    main_container = ttk.Frame(customer_window)
    main_container.pack(fill='both', expand=True)
    top_panel = ttk.Frame(main_container, padding=(15, 5), style='Customer.TFrame')
    top_panel.pack(fill='x', side='top')
    ttk.Label(top_panel, text=f"Добро пожаловать, {current_user.split('@')[0]}!",
              font=('Arial', 12, 'bold')).pack(side='left')
    menu_frame = ttk.Frame(main_container, padding=(10, 5), style='Customer.TFrame')
    menu_frame.pack(fill='x', pady=(0, 10))
    def show_promotions():
        try:
            promo_window = tk.Toplevel()
            promo_window.title("Текущие акции и скидки")
            promo_window.geometry("800x600")
            promo_window.resizable(False, False)
            style = ttk.Style()
            style.configure('Promo.TFrame', background='#f9f9f9', borderwidth=1, relief='solid')
            style.configure('PromoHeader.TLabel', font=('Arial', 14, 'bold'), foreground='#e74c3c')
            style.configure('PromoText.TLabel', font=('Arial', 11), wraplength=700)
            style.configure('PromoDate.TLabel', font=('Arial', 10, 'italic'), foreground='#7f8c8d')
            style.configure('PromoPercent.TLabel', font=('Arial', 24, 'bold'), foreground='#27ae60')
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM activediscounts ORDER BY Discount_Percent DESC")
            discounts = cursor.fetchall()
            cursor.execute("""
                           SELECT d.ID   as Discount_ID,
                                  p.ID   as Product_ID,
                                  p.Name as Product_Name,
                                  c.Name as Category_Name,
                                  p.Price_Retail,
                                  p.Price_Wholesale,
                                  p.Qty_for_Wholesale,
                                  p.Description,
                                  c.Name as Category
                           FROM activediscounts d
                                    JOIN discount_product dp ON d.ID = dp.Discount_ID
                                    JOIN product p ON dp.Product_ID = p.ID
                                    JOIN category c ON p.Category_ID = c.ID
                           """)
            discount_products = cursor.fetchall()
            cursor.close()
            products_by_discount = {}
            full_product_info = {}
            categories_by_discount = {}
            for dp in discount_products:
                products_by_discount.setdefault(dp['Discount_ID'], []).append(dp['Product_Name'])
                categories_by_discount.setdefault(dp['Discount_ID'], set()).add(dp['Category_Name'])
                # Сохраняем полную информацию о товаре
                if dp['Discount_ID'] not in full_product_info:
                    full_product_info[dp['Discount_ID']] = []
                full_product_info[dp['Discount_ID']].append({
                    'ID': dp['Product_ID'],
                    'Name': dp['Product_Name'],
                    'Category': dp['Category_Name'],
                    'Price_Retail': dp['Price_Retail'],
                    'Price_Wholesale': dp['Price_Wholesale'],
                    'Qty_for_Wholesale': dp['Qty_for_Wholesale'],
                    'Description': dp['Description']
                })
            main_frame = ttk.Frame(promo_window)
            main_frame.pack(fill='both', expand=True)
            canvas = tk.Canvas(main_frame)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            scrollable_frame = ttk.Frame(canvas)
            scrollable_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            def on_frame_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
            scrollable_frame.bind("<Configure>", on_frame_configure)
            def resize_canvas(event):
                canvas.itemconfig(scrollable_window, width=event.width)
            canvas.bind("<Configure>", resize_canvas)
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta // 120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            ttk.Label(scrollable_frame,
                      text="Текущие акции и специальные предложения",
                      font=('Arial', 16, 'bold')).pack(pady=(20, 5))
            # Строка поиска
            search_var = tk.StringVar()
            search_entry = ttk.Entry(scrollable_frame, textvariable=search_var, width=40)
            search_entry.pack(pady=(0, 10))
            control_frame = ttk.Frame(scrollable_frame)
            control_frame.pack(fill='x', padx=10, pady=5)
            sort_var = tk.StringVar(value='Discount_Percent')
            sort_options = {
                'Discount_Percent': 'Проценту скидки',
                'Qty_Required': 'Количеству для скидки',
                'Min_Amount': 'Сумме для скидки'
            }
            ttk.Label(control_frame, text="Сортировать по:").pack(side='left', padx=(0, 5))
            sort_combobox = ttk.Combobox(
                control_frame,
                textvariable=sort_var,
                values=list(sort_options.values()),
                state='readonly',
                width=25
            )
            sort_combobox.pack(side='left')
            sort_combobox.current(0)
            order_var = tk.StringVar(value='DESC')
            order_frame = ttk.Frame(control_frame)
            order_frame.pack(side='left', padx=10)
            ttk.Label(order_frame, text="Порядок:").pack(side='left')
            ttk.Radiobutton(order_frame, text="По убыванию", variable=order_var, value='DESC').pack(side='left', padx=5)
            ttk.Radiobutton(order_frame, text="По возрастанию", variable=order_var, value='ASC').pack(side='left')
            shown_count = tk.IntVar(value=0)
            chunk_size = 15
            promo_frames = []
            def clear_promo_frames():
                for frame in promo_frames:
                    frame.destroy()
                promo_frames.clear()
                shown_count.set(0)
            def apply_sorting(discounts_list):
                sort_key = sort_var.get()
                reverse = order_var.get() == 'DESC'
                db_sort_field = next((k for k, v in sort_options.items() if v == sort_key), 'Discount_Percent')
                return sorted(
                    discounts_list,
                    key=lambda x: x[db_sort_field] if x[db_sort_field] is not None else 0,
                    reverse=reverse
                )
            def show_next_chunk(filtered_discounts):
                start = shown_count.get()
                end = min(start + chunk_size, len(filtered_discounts))
                for discount in filtered_discounts[start:end]:
                    frame = ttk.Frame(scrollable_frame, style='Promo.TFrame', padding=15)
                    frame.pack(fill='x', padx=20, pady=10)
                    promo_frames.append(frame)
                    top_frame = ttk.Frame(frame)
                    top_frame.pack(fill='x')
                    percent_frame = ttk.Frame(top_frame)
                    percent_frame.pack(side='left')
                    ttk.Label(percent_frame, text=f"-{discount['Discount_Percent']}%",
                              style='PromoPercent.TLabel').pack()
                    desc_frame = ttk.Frame(top_frame)
                    desc_frame.pack(side='left', padx=15, fill='x', expand=True)
                    ttk.Label(desc_frame,
                              text=f"Скидка {discount['Discount_Percent']}%",
                              style='PromoHeader.TLabel').pack(anchor='w')
                    conditions = []
                    if discount['Qty_Required'] is not None and int(discount['Qty_Required']) >= 1:
                        conditions.append(f"при покупке от {discount['Qty_Required']} шт.")
                    if discount['Min_Amount'] is not None and float(discount['Min_Amount']) > 0:
                        conditions.append(f"на сумму от {discount['Min_Amount']} руб.")
                    if conditions:
                        ttk.Label(desc_frame,
                                  text=", ".join(conditions),
                                  style='PromoText.TLabel').pack(anchor='w')
                    date_frame = ttk.Frame(frame)
                    date_frame.pack(fill='x', pady=(5, 0))
                    start_date = discount['Start_Date'].strftime('%d.%m.%Y') if discount[
                        'Start_Date'] else "дата не указана"
                    end_date = discount['End_Date'].strftime('%d.%m.%Y') if discount['End_Date'] else "дата не указана"
                    ttk.Label(date_frame,
                              text=f"Акция действует с {start_date} по {end_date}",
                              style='PromoDate.TLabel').pack(anchor='w')
                    if discount['ID'] in products_by_discount:
                        products_frame = ttk.Frame(frame)
                        products_frame.pack(fill='x', pady=(10, 0))
                        ttk.Label(products_frame,
                                  text="Товары, участвующие в акции:",
                                  font=('Arial', 10, 'bold')).pack(anchor='w')
                        products_list_frame = ttk.Frame(products_frame)
                        products_list_frame.pack(fill='x', padx=10)
                        for product in full_product_info[discount['ID']]:
                            product_label = ttk.Label(
                                products_list_frame,
                                text=f"• {product['Name']}",
                                font=('Arial', 10),
                                cursor="hand2"
                            )
                            product_label.pack(anchor='w')
                            product_label.bind("<Button-1>",
                                               lambda e, p=product: show_product_details(p))
                shown_count.set(end)
                if shown_count.get() >= len(filtered_discounts):
                    load_more_btn.pack_forget()
                else:
                    load_more_btn.pack_forget()
                    load_more_btn.pack(pady=20)
            def perform_search(*args):
                query = search_var.get().strip().lower()
                clear_promo_frames()
                for widget in scrollable_frame.winfo_children():
                    if isinstance(widget, ttk.Label) and widget.cget("text") == "Ничего не найдено по вашему запросу.":
                        widget.destroy()
                selected_sort_display = sort_var.get()
                selected_db_field = [k for k, v in sort_options.items() if v == selected_sort_display]
                selected_db_field = selected_db_field[0] if selected_db_field else 'Discount_Percent'
                filtered = []
                for d in discounts:
                    if selected_db_field == 'Qty_Required' and (
                            d['Qty_Required'] is None or int(d['Qty_Required']) < 1):
                        continue
                    if selected_db_field == 'Min_Amount' and (d['Min_Amount'] is None or float(d['Min_Amount']) <= 0):
                        continue
                    if not query:
                        filtered.append(d)
                    elif d['ID'] in products_by_discount:
                        product_match = any(query in product.lower() for product in products_by_discount[d['ID']])
                        category_match = any(query in category.lower() for category in categories_by_discount[d['ID']])
                        if product_match or category_match:
                            filtered.append(d)
                if not filtered:
                    ttk.Label(scrollable_frame,
                              text="Ничего не найдено по вашему запросу.",
                              font=('Arial', 12),
                              foreground='#7f8c8d').pack(pady=50)
                    load_more_btn.pack_forget()
                else:
                    filtered = apply_sorting(filtered)
                    current_filtered[:] = filtered
                    show_next_chunk(filtered)
            def on_sort_change(*args):
                perform_search()
            sort_var.trace_add('write', on_sort_change)
            order_var.trace_add('write', on_sort_change)
            search_var.trace_add("write", lambda *_: perform_search())
            current_filtered = discounts[:]
            load_more_btn = ttk.Button(scrollable_frame, text="Загрузить еще",
                                       command=lambda: show_next_chunk(current_filtered))
            perform_search()
            def on_close():
                canvas.unbind_all("<MouseWheel>")
                promo_window.destroy()
            promo_window.protocol("WM_DELETE_WINDOW", on_close)
        except Error as e:
            error_handler.show_error("Ошибка", f"Не удалось загрузить информацию об акциях:\n{str(e)}")
    def show_orders():
        orders_window = tk.Toplevel()
        orders_window.title("Мои заказы")
        orders_window.geometry("1200x800")
        orders_window.minsize(800, 600)
        style = ttk.Style()
        style.configure('Order.TFrame', borderwidth=1, relief='solid', padding=10)
        style.configure('OrderHeader.TLabel', font=('Arial', 12, 'bold'))
        style.configure('OrderTable.Treeview', font=('Arial', 10), rowheight=25)
        style.configure('OrderTable.Treeview.Heading', font=('Arial', 10, 'bold'))
        style.configure('Total.TLabel', font=('Arial', 11, 'bold'), foreground='#e74c3c')
        style.configure('Discount.TLabel', font=('Arial', 10), foreground='#27ae60')
        style.configure('DeleteBtn.TButton', foreground='red')
        main_frame = ttk.Frame(orders_window)
        main_frame.pack(fill='both', expand=True)
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        center_frame = ttk.Frame(canvas)
        scrollable_frame = ttk.Frame(center_frame)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        center_frame.bind(
            "<Configure>",
            lambda e: canvas.itemconfig("window", width=canvas.winfo_width()))
        canvas.create_window((0, 0), window=center_frame, anchor="n", tags="window")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        scrollable_frame.pack(side="top", anchor="n")
        title_frame = ttk.Frame(scrollable_frame)
        title_frame.pack(fill='x', pady=10)
        ttk.Label(title_frame, text="История моих заказов", font=('Arial', 16, 'bold')).pack()
        notebook = ttk.Notebook(scrollable_frame)
        notebook.pack(fill='both', expand=True, padx=20, pady=10)
        cart_frame = ttk.Frame(notebook)
        processing_frame = ttk.Frame(notebook)
        purchases_frame = ttk.Frame(notebook)
        notebook.add(cart_frame, text="Корзина (ждут оплаты)")
        notebook.add(processing_frame, text="В обработке")
        notebook.add(purchases_frame, text="Мои покупки")
        def show_product_info(product_id, product_name):
            """Показывает информацию о товаре в отдельном окне"""
            info_window = tk.Toplevel(orders_window)
            info_window.title(f"Информация о товаре: {product_name}")
            info_window.geometry("500x300")
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("""
                               SELECT p.ID,
                                      p.Name,
                                      p.Description,
                                      p.Price_Retail,
                                      p.Price_Wholesale,
                                      p.Qty_for_Wholesale,
                                      c.Name as Category,
                                      pcv.Qty_in_Stock
                               FROM product p
                                        JOIN category c ON p.Category_ID = c.ID
                                        LEFT JOIN productcellview pcv ON p.ID = pcv.Product_ID
                               WHERE p.ID = %s
                               """, (product_id,))
                product_info = cursor.fetchone()
                cursor.close()
                if not product_info:
                    ttk.Label(info_window, text="Информация о товаре не найдена").pack(pady=20)
                    return
                main_frame = ttk.Frame(info_window, padding=20)
                main_frame.pack(fill='both', expand=True)
                ttk.Label(main_frame, text=product_info['Name'], font=('Arial', 14, 'bold')).pack(anchor='w')
                # Информация о товаре
                info_text = f"""
    ID товара: {product_info['ID']}
    Категория: {product_info['Category']}
    Количество на складе: {product_info['Qty_in_Stock'] if product_info['Qty_in_Stock'] is not None else 'Нет данных'}
    Розничная цена: {product_info['Price_Retail']:.2f} ₽
    """
                if product_info['Qty_for_Wholesale'] > 0:
                    info_text += f"Оптовая цена (от {product_info['Qty_for_Wholesale']} шт.): {product_info['Price_Wholesale']:.2f} ₽\n"
                if product_info['Description']:
                    info_text += f"\nОписание:\n{product_info['Description']}"
                ttk.Label(main_frame, text=info_text, justify='left').pack(anchor='w', pady=10)
                ttk.Button(main_frame, text="Закрыть", command=info_window.destroy).pack(pady=(10, 0))
            except Error as e:
                error_handler.show_error("Ошибка базы данных", f"Не удалось загрузить информацию о товаре:\n{str(e)}")
        def clear_frame(frame):
            """Очищает все виджеты из фрейма"""
            for widget in frame.winfo_children():
                widget.destroy()
        def show_status_history(transaction_id):
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                                   SELECT s.Name, ctd.DateTime
                                   FROM customertransactiondates ctd
                                            JOIN status s ON ctd.Status_ID = s.ID
                                   WHERE ctd.Transaction_ID = %s
                                   ORDER BY ctd.DateTime
                                   """, (transaction_id,))
                    history = cursor.fetchall()
                if not history or len(history) <= 1:
                    return  # Не показываем, если история пуста или только один статус
                history_window = tk.Toplevel()
                history_window.title(f"История статусов для заказа №{transaction_id}")
                history_window.geometry("400x300")
                ttk.Label(history_window, text=f"История статусов заказа №{transaction_id}",
                          font=('Arial', 12, 'bold')).pack(pady=10)
                for status_name, dt in history:
                    date_str = dt.strftime('%d.%m.%Y %H:%M')
                    ttk.Label(history_window, text=f"{status_name} — {date_str}", anchor='w').pack(fill='x',padx=20,pady=2)
                ttk.Button(history_window, text="Закрыть", command=history_window.destroy).pack(pady=10)
            except Error as e:
                error_handler.show_error("Ошибка загрузки истории", str(e))
        def delete_product(transaction_id, product_id):
            if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот товар?"):
                return
            try:
                with connection.cursor() as cur:
                    cur.execute(
                        "CALL DeleteTransactionDetail(%s,%s)",
                        (product_id, transaction_id)
                    )
                    try:
                        while True:
                            cur.fetchall()
                            if not cur.nextset():
                                break
                    except mysql.connector.Error:
                        pass
                    connection.commit()
                    update_order_data()
                    messagebox.showinfo("Успех", "Товар успешно удален")
            except Error as e:
                error_handler.show_error("Ошибка удаления", str(e))
        def update_quantity(transaction_id, product_id, new_qty):
            try:
                with connection.cursor() as cur:
                    cur.execute(
                        "CALL UpdateTransactionDetail(%s,%s,%s,%s)",
                        (product_id, transaction_id, new_qty, 1)
                    )
                    try:
                        while True:
                            cur.fetchall()
                            if not cur.nextset():
                                break
                    except mysql.connector.Error:
                        pass
                    connection.commit()
                    update_order_data()
            except Error as e:
                error_handler.show_error("Ошибка обновления", str(e))
        def update_order_data():
            """Обновляет данные во всех вкладках"""
            clear_frame(cart_frame)
            clear_frame(processing_frame)
            clear_frame(purchases_frame)
            create_order_table(cart_frame, "= 1 or status_id=0", include_null=True)
            create_order_table(processing_frame, "BETWEEN 2 AND 5", include_null=False)
            create_order_table(purchases_frame, "BETWEEN 6 AND 7", include_null=False)
        def create_order_table(parent_frame, status_condition, include_null=False):
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT ID, Name FROM status")
                    statuses = {row[0]: row[1] for row in cursor.fetchall()}
                    cursor.execute(f"""
                           SELECT ctb.ID, ctb.Total_Cost, ctd.DateTime, ctd.Status_ID, 
                                  ctb.Discount_ID, d.Discount_Percent
                           FROM customertransactionbase ctb
                           LEFT JOIN (
                               SELECT Transaction_ID, MAX(DateTime) AS MaxDate
                               FROM customertransactiondates
                               GROUP BY Transaction_ID
                           ) latest ON ctb.ID = latest.Transaction_ID
                           LEFT JOIN customertransactiondates ctd 
                                  ON ctd.Transaction_ID = latest.Transaction_ID 
                                  AND ctd.DateTime = latest.MaxDate
                           LEFT JOIN Activediscounts d ON ctb.Discount_ID = d.ID
                           WHERE ctd.Status_ID {status_condition}
                                 {"OR ctd.Status_ID IS NULL" if include_null else ""}
                           ORDER BY ctd.DateTime DESC
                       """)
                    orders = cursor.fetchall()
                    if not orders:
                        ttk.Label(parent_frame, text="Нет заказов в этой категории").pack(pady=50)
                        return
                    for order in orders:
                        order_id, total_cost, datetime, status_id, discount_id, discount_percent = order
                        order_frame = ttk.Frame(parent_frame, style='Order.TFrame')
                        order_frame.pack(fill='x', pady=10, padx=20)
                        header_frame = ttk.Frame(order_frame)
                        header_frame.pack(fill='x', pady=(0, 10))
                        date_str = datetime.strftime('%d.%m.%Y %H:%M') if datetime else "дата не указана"
                        ttk.Label(header_frame,
                                  text=f"Заказ №{order_id} от {date_str}",
                                  style='OrderHeader.TLabel').pack(side='left')
                        if status_id and status_id > 1:
                            ttk.Button(
                                header_frame,
                                text="Чек",
                                command=lambda oid=order_id: receipt_gen.generate_receipt(oid, parent_window=orders_window)
                            ).pack(side='right', padx=5)
                        # Получаем товары заказа
                        with connection.cursor() as products_cursor:
                            products_cursor.execute("""
                                                    SELECT p.ID, p.Name, ctd.Price, ctd.Qty
                                                    FROM customertransactiondetails ctd
                                                             JOIN product p ON ctd.Product_ID = p.ID
                                                    WHERE ctd.Transaction_id = %s
                                                    """, (order_id,))
                            products = products_cursor.fetchall()
                            if status_id == 1 or status_id is None or status_id == 0:
                                if status_id is None or status_id == 0:
                                    ttk.Button(header_frame, text="Удалить заказ",
                                               style='DeleteBtn.TButton',
                                               command=lambda tid=order_id: delete_order(tid)).pack(side='right', padx=5)
                                else:
                                    ttk.Button(header_frame, text="Удалить заказ",
                                               style='DeleteBtn.TButton',
                                               command=lambda tid=order_id: delete_order(tid)).pack(side='right', padx=5)
                                    # Добавляем кнопку оплаты только если есть товары в заказе
                                    if products:
                                        ttk.Button(
                                            header_frame,
                                            text="Оплатить заказ",
                                            command=lambda tid=order_id: pay_order(tid)
                                        ).pack(side='right', padx=5)
                            status_label = ttk.Label(header_frame, text=statuses.get(status_id, "Пусто"),
                                                     font=('Arial', 10), foreground='black', cursor='hand2')
                            status_label.pack(side='right')
                            def bind_status_click(oid):
                                try:
                                    with connection.cursor() as cursor:
                                        cursor.execute(
                                            "SELECT COUNT(*) FROM customertransactiondates WHERE Transaction_ID = %s",
                                            (oid,))
                                        count = cursor.fetchone()[0]
                                        if count > 1:
                                            status_label.bind("<Button-1>", lambda e, tid=oid: show_status_history(tid))
                                except Error as e:
                                    error_handler.show_error("Ошибка базы данных", str(e))
                            def pay_order(transaction_id):
                                try:
                                    with connection.cursor() as cursor:
                                        cursor.execute("SELECT ID FROM customer_view")
                                        current_user_id = cursor.fetchone()
                                    if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите оплатить этот заказ?"):
                                        return
                                    current_user_id=current_user_id[0]
                                    with connection.cursor() as cursor:
                                        args = (transaction_id, current_user_id)
                                        cursor.callproc("TrySetOrderStatusToPaid", args)
                                        connection.commit()
                                        update_order_data()
                                        messagebox.showinfo("Успех", "Заказ успешно оплачен!")
                                except Error as e:
                                    error_handler.show_error("Ошибка оплаты", str(e))
                            bind_status_click(order_id)
                            if products:
                                for idx, (prod_id, name, price, qty) in enumerate(products):
                                    item_frame = ttk.Frame(order_frame)
                                    item_frame.pack(fill='x', pady=2, padx=10)
                                    name_label = ttk.Label(item_frame, text=f"{name}", width=40, cursor="hand2")
                                    name_label.pack(side='left')
                                    name_label.bind("<Button-1>",
                                                    lambda e, pid=prod_id, pname=name: show_product_info(pid, pname))
                                    ttk.Label(item_frame, text=f"{price:.2f} ₽/шт.", width=20).pack(side='left')
                                    if status_id == 1 or status_id == 0:
                                        qty_var = tk.IntVar(value=qty)
                                        spinbox = ttk.Spinbox(item_frame, from_=1, to=100, width=5,
                                                              textvariable=qty_var)
                                        spinbox.pack(side='left', padx=5)
                                        update_btn = ttk.Button(
                                            item_frame, text="✓", width=2,
                                            command=lambda tid=order_id, pid=prod_id, var=qty_var:
                                            update_quantity(tid, pid, var.get())
                                        )
                                        update_btn.pack(side='left', padx=5)
                                        delete_btn = ttk.Button(
                                            item_frame, text="Удалить", style='DeleteBtn.TButton',
                                            command=lambda tid=order_id, pid=prod_id:
                                            delete_product(tid, pid)
                                        )
                                        delete_btn.pack(side='right', padx=5)
                                    else:
                                        ttk.Label(item_frame, text=f"{qty} шт.").pack(side='left', padx=10)
                            else:
                                ttk.Label(order_frame, text="(Нет товаров в заказе)", foreground='gray').pack(pady=5)
                        # Итоги заказа
                        total_frame = ttk.Frame(order_frame)
                        total_frame.pack(fill='x', pady=(10, 0))
                        if discount_id:
                            original = float(total_cost) / (1 - discount_percent / 100)
                            disc_frame = ttk.Frame(total_frame)
                            disc_frame.pack(fill='x')
                            ttk.Label(disc_frame, text="Сумма без скидки:").pack(side='left')
                            ttk.Label(disc_frame, text=f"{original:.2f} ₽").pack(side='left', padx=10)
                            ttk.Label(disc_frame,
                                      text=f"Скидка {discount_percent}%: -{original - float(total_cost):.2f} ₽",
                                      style='Discount.TLabel').pack(side='left', padx=10)
                        ttk.Label(total_frame, text="Итого к оплате:", style='OrderHeader.TLabel').pack(side='left')
                        ttk.Label(total_frame, text=f"{total_cost:.2f} ₽", style='Total.TLabel').pack(side='right')
            except Error as e:
                error_handler.show_error("Ошибка базы данных", f"Не удалось загрузить заказы:\n{str(e)}")
        def delete_order(transaction_id):
            if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот товар?"):
                return
            try:
                with connection.cursor() as cur:
                    cur.execute("DELETE FROM customertransactionbase WHERE ID=%s", (transaction_id,))
                    connection.commit()
                    update_order_data()
            except Error as e:
                error_handler.show_error("Ошибка удаления заказа", str(e))
        def on_close():
            canvas.unbind_all("<MouseWheel>")
            orders_window.destroy()
        orders_window.protocol("WM_DELETE_WINDOW", on_close)
        update_order_data()
        canvas.focus_set()
    def show_profile():
        profile_manager = ProfileManager(connection, error_handler, customer_window)
        profile_manager.show_profile()
    buttons = [("Акции", show_promotions, "🎁"), ("Мои заказы", show_orders, "🛒"), ("Профиль", show_profile, "👤"),
               ("Выход", logout, "")]
    for text, command, icon in buttons:
        btn_frame = ttk.Frame(menu_frame, padding=5)
        btn_frame.pack(side='left', expand=True, fill='both')
        btn = ttk.Button(btn_frame, text=f"{icon} {text}", command=command,
                         style='Menu.TButton', width=15)
        btn.pack(fill='both', expand=True, padx=2)
    content_frame = ttk.Frame(main_container, padding=20)
    content_frame.pack(fill='both', expand=True)
    current_offset = 0
    total_products = 0
    current_search_query = ""
    current_search_mode = "name"
    current_sort_field = "p.ID"
    current_sort_order = "ASC"
    load_more_button = None
    limit_var = tk.IntVar(value=25)  # Переменная для хранения выбранного количества строк
    def setup_catalog_ui():
        nonlocal current_offset, total_products, current_search_query, current_search_mode
        current_offset = 0
        total_products = 0
        current_search_query = ""
        current_search_mode = "name"
        # Добавляем переменную для хранения состояния фильтра по наличию
        global availability_filter
        availability_filter = tk.StringVar(value="all")
        search_frame = ttk.Frame(content_frame)
        search_frame.pack(pady=20, fill='x')
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=50)
        search_entry.pack(side='left', padx=(0, 10), fill='x', expand=True)
        def on_search():
            nonlocal current_offset, current_search_query, current_search_mode
            current_offset = 0
            current_search_query = search_var.get()
            current_search_mode = search_mode.get()
            for widget in products_canvas_frame.winfo_children():
                widget.destroy()
            load_products()
        search_button = ttk.Button(search_frame, text="Поиск", command=on_search)
        search_button.pack(side='left')
        filter_frame = ttk.Frame(content_frame)
        filter_frame.pack(pady=5, fill='x')
        ttk.Label(filter_frame, text="Наличие:", font=('Arial', 9)).pack(side='left', padx=(0, 10))
        ttk.Radiobutton(filter_frame, text="Все", variable=availability_filter, value="all").pack(side='left', padx=5)
        ttk.Radiobutton(filter_frame, text="В наличии", variable=availability_filter, value="in_stock").pack(
            side='left', padx=5)
        ttk.Radiobutton(filter_frame, text="Нет в наличии", variable=availability_filter, value="out_of_stock").pack(
            side='left', padx=5)
        search_mode = tk.StringVar(value="name")
        radio_frame = ttk.Frame(content_frame)
        radio_frame.pack(pady=5, fill='x')
        ttk.Label(radio_frame, text="Искать по:", font=('Arial', 9)).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(radio_frame, text="Названию товара", variable=search_mode, value="name").pack(side="left", padx=5)
        ttk.Radiobutton(radio_frame, text="Категории", variable=search_mode, value="category").pack(side="left", padx=5)
        sort_frame = ttk.Frame(content_frame)
        sort_frame.pack(pady=5, fill='x')
        ttk.Label(sort_frame, text="Сортировать по:", font=('Arial', 9)).pack(side="left", padx=(0, 10))
        sort_field_var = tk.StringVar(value="ID товара")
        sort_fields = {
            "ID товара": "p.ID",
            "Названию": "p.Name",
            "Категории": "c.Name",
            "Оптовой цене": "p.Price_Wholesale",
            "Розничной цене": "p.Price_Retail"
        }
        sort_field_menu = ttk.OptionMenu(sort_frame, sort_field_var, "ID товара", *sort_fields.keys())
        sort_field_menu.pack(side='left', padx=5)
        sort_order_var = tk.StringVar(value="ASC")
        ttk.Radiobutton(sort_frame, text="По возрастанию", variable=sort_order_var, value="ASC").pack(side='left', padx=5)
        ttk.Radiobutton(sort_frame, text="По убыванию", variable=sort_order_var, value="DESC").pack(side='left', padx=5)
        def apply_sort():
            nonlocal current_sort_field, current_sort_order, current_offset
            current_offset = 0
            current_sort_field = sort_fields[sort_field_var.get()]
            current_sort_order = sort_order_var.get()
            for widget in products_canvas_frame.winfo_children():
                widget.destroy()
            load_products()
        ttk.Button(sort_frame, text="Применить", command=apply_sort).pack(side='left', padx=10)
        products_canvas = tk.Canvas(content_frame)
        products_scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=products_canvas.yview)
        products_canvas.configure(yscrollcommand=products_scrollbar.set)
        products_scrollbar.pack(side="right", fill="y")
        products_canvas.pack(side="left", fill="both", expand=True)
        global products_canvas_frame
        products_canvas_frame = ttk.Frame(products_canvas)
        products_canvas.create_window((0, 0), window=products_canvas_frame, anchor="nw")
        products_canvas_frame.bind("<Configure>",
                                   lambda e: products_canvas.configure(scrollregion=products_canvas.bbox("all")))
        products_canvas.bind("<Configure>", lambda e: products_canvas.itemconfig("all", width=e.width))
        def on_mousewheel(event):
            products_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def bind_mousewheel(event):
            products_canvas.bind_all("<MouseWheel>", on_mousewheel)
        def unbind_mousewheel(event):
            products_canvas.unbind_all("<MouseWheel>")
        products_canvas.bind("<Enter>", bind_mousewheel)
        products_canvas.bind("<Leave>", unbind_mousewheel)
        def on_frame_configure(event):
            products_canvas.configure(scrollregion=products_canvas.bbox("all"))
            products_canvas.itemconfig("inner_frame", width=products_canvas.winfo_width())
        products_canvas_frame.bind("<Configure>", on_frame_configure)
        load_products()
        # Функция для обновления конфигурации при изменении содержимого
        def update_scrollregion(event):
            products_canvas.configure(scrollregion=products_canvas.bbox("all"))
        products_canvas_frame.bind("<Configure>", update_scrollregion)
    def load_products():
        nonlocal current_offset, total_products
        try:
            cursor = connection.cursor(dictionary=True)
            # Базовый запрос
            query = """
                    SELECT p.ID,
                           p.Name,
                           p.Description,
                           p.Price_Retail,
                           p.Price_Wholesale,
                           p.Qty_for_Wholesale,
                           c.Name as Category
                    FROM PRODUCT p
                             JOIN CATEGORY c ON p.Category_ID = c.ID
                    """
            params = []
            # Добавляем условие для фильтра по наличию
            if availability_filter.get() == "in_stock":
                query += " JOIN productcellview pcv ON p.ID = pcv.Product_ID WHERE pcv.Qty_in_Stock > 0"
            elif availability_filter.get() == "out_of_stock":
                query += " LEFT JOIN productcellview pcv ON p.ID = pcv.Product_ID WHERE pcv.Qty_in_Stock IS NULL OR pcv.Qty_in_Stock = 0"
            else:
                query += " WHERE 1=1"  # Для удобства добавления других условий
            # Добавляем условие поиска
            if current_search_query:
                if current_search_mode == "name":
                    query += " AND p.Name LIKE %s"
                    params.append(f"%{current_search_query}%")
                elif current_search_mode == "category":
                    query += " AND c.Name LIKE %s"
                    params.append(f"%{current_search_query}%")
            # Добавляем сортировку
            query += f" ORDER BY {current_sort_field} {current_sort_order} LIMIT %s OFFSET %s"
            params.extend([limit_var.get(), current_offset])
            cursor.execute(query, params)
            products = cursor.fetchall()
            # Загружаем общее количество с учетом фильтров
            if current_offset == 0:
                count_query = """
                              SELECT COUNT(*) as total
                              FROM PRODUCT p
                                       JOIN CATEGORY c ON p.Category_ID = c.ID \
                              """
                if availability_filter.get() == "in_stock":
                    count_query += " JOIN productcellview pcv ON p.ID = pcv.Product_ID WHERE pcv.Qty_in_Stock > 0"
                elif availability_filter.get() == "out_of_stock":
                    count_query += " LEFT JOIN productcellview pcv ON p.ID = pcv.Product_ID WHERE pcv.Qty_in_Stock IS NULL OR pcv.Qty_in_Stock = 0"
                else:
                    count_query += " WHERE 1=1"
                if current_search_query:
                    if current_search_mode == "name":
                        count_query += " AND p.Name LIKE %s"
                    elif current_search_mode == "category":
                        count_query += " AND c.Name LIKE %s"
                cursor.execute(count_query, params[:-2] if current_search_query else [])
                total_products = cursor.fetchone()['total']
            if current_offset == 0:
                for widget in products_canvas_frame.winfo_children():
                    widget.destroy()
            for product in products:
                create_product_card(product)
            current_offset += len(products)
            cursor.close()
            update_load_more_button()
        except Error as e:
            error_handler.show_error("Ошибка базы данных", f"Не удалось загрузить товары:\n{str(e)}")
    def update_load_more_button():
        nonlocal load_more_button, current_offset, total_products
        if load_more_button:
            load_more_button.destroy()
        if current_offset < total_products:
            load_more_button = ttk.Button(
                products_canvas_frame,
                text="Загрузить еще",
                command=load_products,
                style='LoadMore.TButton'
            )
            load_more_button.pack(pady=10)
    def create_product_card(product):
        card_frame = ttk.Frame(products_canvas_frame, style='Product.TFrame', padding=10)
        card_frame.pack(fill='x', pady=5, padx=5)
        top_frame = ttk.Frame(card_frame)
        top_frame.pack(fill='x')
        ttk.Label(top_frame, text=f"ID: {product['ID']}",
                  font=('Arial', 9, 'italic'),
                  foreground='#777777',
                  background='white').pack(side='left', padx=(0, 10))
        product_name = ttk.Label(top_frame, text=product['Name'], style='ProductName.TLabel', cursor="hand2")
        product_name.pack(side='left')
        product_name.bind("<Button-1>", lambda e, p=product: show_product_details(p))
        ttk.Label(top_frame, text=product['Category'],
                  font=('Arial', 10, 'italic'),
                  foreground='#3498db',
                  background='white').pack(side='right')
        if product['Description']:
            desc_frame = ttk.Frame(card_frame)
            desc_frame.pack(fill='x', pady=(5, 0))
            ttk.Label(desc_frame, text=product['Description'], style='ProductDesc.TLabel',
                      wraplength=700, justify='left').pack(anchor='w')
        bottom_frame = ttk.Frame(card_frame)
        bottom_frame.pack(fill='x', pady=(10, 0))
        price_text = f"Розница: {product['Price_Retail']} ₽"
        if product['Qty_for_Wholesale'] > 0:
            price_text += f" | Опт ({product['Qty_for_Wholesale']}+): {product['Price_Wholesale']} ₽"
        ttk.Label(bottom_frame, text=price_text, style='ProductPrice.TLabel').pack(side='left')
        ttk.Button(bottom_frame, text="Купить", style='Menu.TButton',
                   command=lambda p=product: add_to_cart(p)).pack(side='right')
    def show_product_details(product):
        """Отображает детальную информацию о товаре"""
        details_window = tk.Toplevel()
        details_window.title(f"Информация о товаре: {product['Name']}")
        details_window.geometry("600x400")
        details_window.resizable(False, False)
        try:
            # Получаем дополнительную информацию о количестве на складе
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT Qty_in_Stock FROM productcellview WHERE Product_ID = %s", (product['ID'],))
            stock_info = cursor.fetchone()
            cursor.close()
            qty_in_stock = stock_info['Qty_in_Stock'] if stock_info else "Нет данных"
        except Error as e:
            qty_in_stock = f"Ошибка: {str(e)}"
        main_frame = ttk.Frame(details_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        ttk.Label(main_frame, text=product['Name'], font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        ttk.Label(main_frame, text=f"ID товара: {product['ID']}", font=('Arial', 10)).pack(anchor='w')
        ttk.Label(main_frame, text=f"Категория: {product['Category']}", font=('Arial', 10)).pack(anchor='w')
        ttk.Label(main_frame, text=f"Количество на складе: {qty_in_stock}", font=('Arial', 10)).pack(anchor='w')
        price_frame = ttk.Frame(main_frame)
        price_frame.pack(fill='x', pady=10)
        ttk.Label(price_frame, text="Цены:", font=('Arial', 10, 'bold')).pack(anchor='w')
        ttk.Label(price_frame, text=f"Розничная: {product['Price_Retail']} ₽", font=('Arial', 10)).pack(anchor='w')
        if product['Qty_for_Wholesale'] > 0:
            ttk.Label(price_frame,
                      text=f"Оптовая (от {product['Qty_for_Wholesale']} шт.): {product['Price_Wholesale']} ₽",
                      font=('Arial', 10)).pack(anchor='w')
        if product['Description']:
            desc_frame = ttk.Frame(main_frame)
            desc_frame.pack(fill='x', pady=10)
            ttk.Label(desc_frame, text="Описание:", font=('Arial', 10, 'bold')).pack(anchor='w')
            ttk.Label(desc_frame, text=product['Description'], font=('Arial', 10), wraplength=550).pack(anchor='w')
        ttk.Button(main_frame, text="Закрыть", command=details_window.destroy).pack(pady=(20, 0))
    def add_to_cart(product):
        """Добавляет товар в корзину с запросом количества и выбора транзакции"""
        qty = simpledialog.askinteger("Количество",
                                      f"Введите количество для товара {product['Name']}:",
                                      parent=customer_window,
                                      minvalue=1,
                                      maxvalue=1000)
        if not qty:
            return
        transactions = get_available_transactions()
        if not transactions:
            create_new_transaction(product, qty)
            return
        # Если есть доступные транзакции, предлагаем выбрать
        select_transaction_window(product, qty, transactions)
    def get_available_transactions():
        """Возвращает список доступных транзакций (со статусом 0 или 1)"""
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                           SELECT ctb.ID, ctb.Total_Cost, ctd.DateTime, ctd.Status_ID
                           FROM customertransactionbase ctb
                                    LEFT JOIN (SELECT Transaction_ID, MAX(DateTime) AS MaxDate
                                               FROM customertransactiondates
                                               GROUP BY Transaction_ID) latest ON ctb.ID = latest.Transaction_ID
                                    LEFT JOIN customertransactiondates ctd
                                              ON ctd.Transaction_ID = latest.Transaction_ID
                                                  AND ctd.DateTime = latest.MaxDate
                           WHERE ctd.Status_ID IN (0, 1)
                              OR ctd.Status_ID IS NULL
                           ORDER BY ctd.DateTime DESC
                           """)
            return cursor.fetchall()
        except Error as e:
            error_handler.show_error("Ошибка базы данных", f"Не удалось загрузить транзакции:\n{str(e)}")
            return []
        finally:
            if cursor: cursor.close()
    def select_transaction_window(product, qty, transactions):
        """Окно выбора транзакции для добавления товара"""
        window = tk.Toplevel(customer_window)
        window.title("Выберите транзакцию")
        window.geometry("500x300")
        window.resizable(False, False)
        ttk.Label(window, text="Выберите транзакцию для добавления товара:",
                  font=('Arial', 11)).pack(pady=10)
        columns = ("id", "date", "status", "total")
        tree = ttk.Treeview(window, columns=columns, show="headings", height=5)
        tree.heading("id", text="ID")
        tree.heading("date", text="Дата")
        tree.heading("status", text="Статус")
        tree.heading("total", text="Сумма")
        tree.column("id", width=50, anchor='center')
        tree.column("date", width=150)
        tree.column("status", width=100)
        tree.column("total", width=100, anchor='e')
        for trans in transactions:
            date_str = trans['DateTime'].strftime('%d.%m.%Y %H:%M') if trans['DateTime'] else "Новая"
            # Получаем название статуса напрямую из базы
            cursor = connection.cursor()
            cursor.execute("SELECT Name FROM status WHERE ID = %s", (trans['Status_ID'],))
            status_result = cursor.fetchone()
            status = status_result[0] if status_result else str(trans['Status_ID'])
            cursor.close()
            total = f"{trans['Total_Cost']:.2f} ₽" if trans['Total_Cost'] else "0.00 ₽"
            tree.insert("", "end", values=(
                trans['ID'],
                date_str,
                status,
                total
            ))
        tree.pack(pady=10, padx=10, fill='both', expand=True)
        button_frame = ttk.Frame(window)
        button_frame.pack(pady=10)
        def on_select():
            selected = tree.focus()
            if not selected:
                messagebox.showwarning("Выбор", "Пожалуйста, выберите транзакцию")
                return
            trans_id = tree.item(selected)['values'][0]
            add_product_to_transaction(product, qty, trans_id)
            window.destroy()
        def on_new():
            window.destroy()
            create_new_transaction(product, qty)
        ttk.Button(button_frame, text="Выбрать", command=on_select).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Новая транзакция", command=on_new).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Отмена", command=window.destroy).pack(side='right', padx=5)
    def create_new_transaction(product, qty):
        """Создает новую транзакцию и добавляет в нее товар"""
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO customertransactionbase (Total_Cost, Discount_ID) VALUES (0, NULL)")
            trans_id = cursor.lastrowid
            add_product_to_transaction(product, qty, trans_id)
            connection.commit()
        except Error as e:
            connection.rollback()
            error_handler.show_error("Ошибка", f"Не удалось создать транзакцию:\n{str(e)}")
        finally:
            if cursor: cursor.close()
    def add_product_to_transaction(product, qty, trans_id):
        """Добавляет товар в указанную транзакцию"""
        try:
            cursor = connection.cursor()
            cursor.execute("""
                           SELECT Qty
                           FROM customertransactiondetails
                           WHERE Transaction_ID = %s
                             AND Product_ID = %s
                           """, (trans_id, product['ID']))
            existing = cursor.fetchone()
            if existing:
                new_qty = existing[0] + qty
                try:
                    with connection.cursor() as cur:
                        cur.execute(
                            "CALL UpdateTransactionDetail(%s,%s,%s,%s)",
                            (product['ID'], trans_id, new_qty, 1)
                        )
                        try:
                            while True:
                                cur.fetchall()
                                if not cur.nextset():
                                    break
                        except mysql.connector.Error:
                            pass
                        connection.commit()
                except Error as e:
                    error_handler.show_error("Ошибка обновления", str(e))
            else:
                try:
                    with connection.cursor() as cur:
                        cur.execute("CALL AddTransactionDetail(%s, %s, %s, %s)", (product['ID'], trans_id, qty, 1))
                        try:
                            while True:
                                cur.fetchall()
                                if not cur.nextset():
                                    break
                        except mysql.connector.Error:
                            pass
                        connection.commit()
                except Error as e:
                    error_handler.show_error("Ошибка добавления", str(e))
            messagebox.showinfo("Успех", f"Товар успешно добавлен в транзакцию #{trans_id}")
        except Error as e:
            connection.rollback()
            error_handler.show_error("Ошибка", f"Не удалось добавить товар в транзакцию:\n{str(e)}")
        finally:
            if cursor: cursor.close()
    setup_catalog_ui()
    load_products()
def show_employee_window(connection, error_handler, login_window, current_user, current_role):
    employee_window = tk.Toplevel()
    current_role = current_role.split("@")[0].replace("'", "").replace('"', '').replace('`', '')
    employee_window.title(f"Электронные компоненты - {current_role}")
    employee_window.geometry("1200x800")
    employee_window.minsize(800, 600)
    def logout():
        try:
            if connection.is_connected():
                connection.close()
        except:
            pass
        employee_window.destroy()
        login_window.deiconify()
    def on_employee_window_closing():
        logout()
    def show_profile():
        profile_manager = ProfileManager(connection, error_handler, employee_window)
        profile_manager.show_profile()
    employee_window.protocol("WM_DELETE_WINDOW", on_employee_window_closing)
    menubar = tk.Menu(employee_window)
    employee_window.config(menu=menubar)
    # Меню (только для определенных ролей)
    if current_role in ['Transaction_Manager', 'Admin']:
        transactions_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Транзакции", menu=transactions_menu)
        transactions_menu.add_command(
            label="Добавить транзакцию",
            command=lambda: show_add_transaction_window(connection, load_table_data)
        )
        transactions_menu.add_command(
            label="Распечатать чек",
            command=lambda: show_print_receipt_window(connection, load_table_data)
        )
    if current_role in ['Order_Picker']:
        transactions_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Транзакции", menu=transactions_menu)
        transactions_menu.add_command(
            label="Распечатать чек",
            command=lambda: show_print_receipt_window(connection, load_table_data)
        )
    if current_role in ['Accountant', 'Admin','Sales_Manager']:
        transactions_menu = tk.Menu(menubar, tearoff=0)
        if current_role != 'Admin':
            menubar.add_cascade(label="Транзакции", menu=transactions_menu)
            transactions_menu.add_command(
                label="Распечатать чек",
                command=lambda: show_print_receipt_window(connection, load_table_data)
            )
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Отчеты", menu=reports_menu)
        reports_menu.add_command(
            label="Создать ежемесячный отчет",
            command=lambda: generate_period_report(connection)
        )
        reports_menu.add_command(
            label="Подробный отчет по клиентам",
            command=lambda: show_transaction_report_window(connection, load_table_data)
        )
    if current_role in ['Warehouse_Worker', 'Admin']:
        transactions_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Поступления", menu=transactions_menu)
        transactions_menu.add_command(
            label="Добавить поступление",
            command=lambda: show_add_supply_window(connection, load_table_data)
        )
    top_panel = ttk.Frame(employee_window, padding=10)
    top_panel.pack(fill='x', side='top')
    user_info_frame = ttk.Frame(top_panel)
    user_info_frame.pack(side='left')
    ttk.Label(user_info_frame, text=f"Пользователь: {current_user}", font=('Arial', 10)).pack(anchor='w')
    ttk.Label(user_info_frame, text=f"Роль: {current_role}", font=('Arial', 10)).pack(anchor='w')
    buttons_frame = ttk.Frame(top_panel)
    buttons_frame.pack(side='right')
    profile_button = ttk.Button(buttons_frame, text="Профиль", command=show_profile)
    profile_button.pack(side='left', padx=5)
    logout_button = ttk.Button(buttons_frame, text="Выйти", command=logout)
    logout_button.pack(side='left', padx=5)
    # Основной контент
    main_frame = ttk.Frame(employee_window)
    main_frame.pack(expand=True, fill='both', padx=10, pady=10)
    selection_frame = ttk.Frame(main_frame)
    selection_frame.pack(fill='x', pady=10)
    table_selection_frame = ttk.Frame(selection_frame)
    table_selection_frame.pack(side='left', padx=5)
    ttk.Label(table_selection_frame, text="Выберите таблицу:").pack(side='left', padx=5)
    table_combobox = ttk.Combobox(table_selection_frame, state="readonly")
    table_combobox.pack(side='left', padx=5)
    limit_selection_frame = ttk.Frame(selection_frame)
    limit_selection_frame.pack(side='left', padx=5)
    ttk.Label(limit_selection_frame, text="Лимит записей:").pack(side='left', padx=5)
    limit_combobox = ttk.Combobox(limit_selection_frame, values=[25, 50, 100, 250, 500], state="normal")
    limit_combobox.pack(side='left', padx=5)
    limit_combobox.set(25)
    control_buttons_frame = ttk.Frame(selection_frame)
    control_buttons_frame.pack(side='right', padx=10)
    # Создаем кнопки управления (изначально скрыты)
    add_button = ttk.Button(control_buttons_frame, text="Добавить")
    edit_button = ttk.Button(control_buttons_frame, text="Изменить")
    delete_button = ttk.Button(control_buttons_frame, text="Удалить")
    search_frame = ttk.Frame(main_frame)
    search_frame.pack(fill='x', pady=10)
    search_left_frame = ttk.Frame(search_frame)
    search_left_frame.pack(side='left', fill='x', expand=True)
    ttk.Label(search_left_frame, text="Поиск:").pack(side='left', padx=5)
    search_entry = ttk.Entry(search_left_frame, width=50)
    search_entry.pack(side='left', padx=5, fill='x', expand=True)
    search_right_frame = ttk.Frame(search_frame)
    search_right_frame.pack(side='right')
    ttk.Label(search_right_frame, text="Столбец:").pack(side='left', padx=5)
    column_combobox = ttk.Combobox(search_right_frame, state="readonly", width=15)
    column_combobox.pack(side='left', padx=5)
    search_type = tk.StringVar(value="partial")
    ttk.Radiobutton(search_right_frame, text="Частичное", variable=search_type, value="partial").pack(side='left', padx=2)
    ttk.Radiobutton(search_right_frame, text="Полное", variable=search_type, value="full").pack(side='left', padx=2)
    search_button = ttk.Button(search_right_frame, text="Найти", command=lambda: search_data())
    search_button.pack(side='left', padx=5)
    def on_search_entry_change(event):
        if not search_entry.get():  # Если поле поиска пустое
            load_table_data()  # Загружаем все данные
    search_entry.bind('<KeyRelease>', on_search_entry_change)
    def get_all_tables(cursor):
        """ Функция для получения всех таблиц из базы данных"""
        cursor.execute("""show tables;""")
        return [table[0] for table in cursor.fetchall()]
    try:
        cursor = connection.cursor()
        all_tables = get_all_tables(cursor)
        cursor.close()
    except Exception as e:
        print(f"Ошибка при получении списка таблиц: {e}")
        all_tables = []
    # Определяем доступные таблицы и права для каждой роли
    role_permissions = {
        'Admin': {table: {'view': True, 'add': True, 'edit': True, 'delete': True} for table in all_tables},
        'Warehouse_Worker': {
            'supply': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'supply_detail': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'product_cell': {'view': True, 'add': True, 'edit': True, 'delete': False},
            'category': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'product': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'cell': {'view': True, 'add': True, 'edit': True, 'delete': False},
            'employee': {'view': True, 'add': False, 'edit': False, 'delete': False}
        },
        'Accountant': {
            'supply': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'supply_detail': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'product_cell': {'view': True, 'add': True, 'edit': True, 'delete': False},
            'cell': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'discount': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'discount_product': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'activediscounts': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'transaction': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'transaction_details': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'transaction_date': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'Max_Transaction_Status': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'customer': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'product': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'category': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'employee': {'view': True, 'add': False, 'edit': False, 'delete': False}
        },
        'Sales_Manager': {
            'transaction': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'transaction_details': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'transaction_date': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'Max_Transaction_Status': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'supply': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'supply_detail': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'product_cell': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'discount': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'discount_product': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'activediscounts': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'product': {'view': True, 'add': True, 'edit': True, 'delete': False},
            'category': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'customer': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'employee': {'view': True, 'add': False, 'edit': False, 'delete': False}
        },
        'Transaction_Manager': {
            'transaction': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'transaction_details': {'view': True, 'add':True, 'edit':True, 'delete': True},
            'transaction_date': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'Max_Transaction_Status': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'product_cell': {'view': True, 'add': False, 'edit': True, 'delete': False},
            'product': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'category': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'status': {'view': True, 'add': True, 'edit': True, 'delete': False},
            'discount': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'discount_product': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'activediscounts': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'customer': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'customer_phone': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'employee': {'view': True, 'add': False, 'edit': False, 'delete': False}

        },
        'Order_Picker': {
            'transaction': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'transaction_details': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'transaction_date': {'view': True, 'add': True, 'edit': True, 'delete': True},
            'Max_Transaction_Status': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'product_cell': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'product': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'category': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'status': {'view': True, 'add': True, 'edit': True, 'delete': False},
            'cell': {'view': True, 'add': True, 'edit': True, 'delete': False},
            'customer': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'customer_phone': {'view': True, 'add': False, 'edit': False, 'delete': False},
            'employee': {'view': True, 'add': False, 'edit': False, 'delete': False}
        }
    }
    # Получаем доступные таблицы для текущей роли
    available_tables = list(role_permissions.get(current_role, {}).keys())
    table_combobox['values'] = available_tables
    if available_tables:
        table_combobox.current(0)
    table_frame = ttk.Frame(main_frame)
    table_frame.pack(expand=True, fill='both')
    tree = ttk.Treeview(table_frame)
    tree.pack(expand=True, fill='both', side='left')
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    scrollbar.pack(side='right', fill='y')
    tree.configure(yscrollcommand=scrollbar.set)
    def on_double_click(event, tree=None):
        if tree is None:
            tree = event.widget  # Получаем Treeview из события
        selected_item = tree.focus()
        if not selected_item:
            return
        item_data = tree.item(selected_item)['values']
        if not item_data:
            return
        if current_table == "employee":
            customer_id = item_data[1]
            role_id = item_data[2]
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT Last_Name, First_Name, Middle_Name, Email FROM customer WHERE ID = %s",
                               (customer_id,))
                customer_data = cursor.fetchone()
                cursor.execute("SELECT role_name FROM role WHERE role_id = %s", (role_id,))
                role_data = cursor.fetchone()
                cursor.close()
                if customer_data and role_data:
                    last_name, first_name, middle_name, email = customer_data
                    role_name = role_data[0]
                    message = f"Сотрудник: {last_name} {first_name} {middle_name}\n"
                    message += f"Email: {email}\n"
                    message += f"Должность: {role_name}"
                    messagebox.showinfo("Информация о сотруднике", message)
                else:
                    messagebox.showerror("Ошибка", "Не удалось получить полную информацию о сотруднике")
            except Exception as e:
                error_handler(f"Ошибка при получении данных о сотруднике: {str(e)}")
        elif current_table == "supply" or current_table == "supply_detail":
                supply_id = item_data[0]
                try:
                    cursor = connection.cursor()
                    cursor.execute("""
                                   SELECT s.DateTime, s.Invoice_Number
                                   FROM supply s
                                   WHERE s.ID = %s
                                   """, (supply_id,))
                    supply_data = cursor.fetchone()
                    if not supply_data:
                        messagebox.showerror("Ошибка", "Поступление не найдено")
                        return
                    date_time, invoice_number = supply_data
                    # Получаем детали поступления с информацией о товарах и ячейках из product_cell
                    cursor.execute("""
                                   SELECT p.Name AS product_name,
                                          sd.Qty,
                                          sd.Purchase_Price,
                                          pc.Cell_ID
                                   FROM supply_detail sd
                                            JOIN product p ON sd.Product_ID = p.ID
                                            LEFT JOIN product_cell pc ON sd.Product_ID = pc.Product_ID
                                   WHERE sd.Supply_ID = %s
                                   """, (supply_id,))
                    basic_details = cursor.fetchall()
                    # Пытаемся получить информацию об ответственных (если есть доступ)
                    try:
                        cursor.execute("""
                                       SELECT p.Name AS product_name,
                                              sd.Qty,
                                              sd.Purchase_Price,
                                              pc.Cell_ID,
                                              e.employee_id,
                                              c.Last_Name,
                                              c.First_Name,
                                              c.Middle_Name,
                                              c.Email
                                       FROM supply_detail sd
                                                JOIN product p ON sd.Product_ID = p.ID
                                                LEFT JOIN product_cell pc ON sd.Product_ID = pc.Product_ID
                                                LEFT JOIN cell cl ON pc.Cell_ID = cl.ID
                                                LEFT JOIN employee e ON cl.Employee_id = e.employee_id
                                                LEFT JOIN customer c ON e.customer_id = c.ID
                                       WHERE sd.Supply_ID = %s
                                       """, (supply_id,))
                        details = cursor.fetchall()
                        has_responsible_info = True
                    except Exception as responsible_info_error:
                        # Если нет доступа к информации об ответственных, используем данные только с ячейками
                        details = [(d[0], d[1], d[2], d[3], None, None, None, None, None) for d in basic_details]
                        has_responsible_info = False
                    cursor.close()
                    info_window = tk.Toplevel()
                    info_window.title(f"Поступление №{supply_id}")
                    info_window.geometry("800x600")
                    notebook = ttk.Notebook(info_window)
                    notebook.pack(fill='both', expand=True)
                    main_frame = ttk.Frame(notebook, padding=10)
                    notebook.add(main_frame, text="Основная информация")
                    ttk.Label(main_frame, text=f"Номер накладной: {invoice_number}", font=('Arial', 10, 'bold')).pack(
                        anchor='w', pady=5)
                    ttk.Label(main_frame, text=f"Дата и время: {date_time.strftime('%Y-%m-%d %H:%M:%S')}").pack(
                        anchor='w', pady=5)
                    ttk.Label(main_frame, text="Детали поступления:", font=('Arial', 10, 'bold')).pack(anchor='w',
                                                                                                       pady=10)
                    columns = ("Товар", "Количество", "Цена", "Сумма", "Ячейка")
                    col_widths = [150, 80, 80, 80, 80]
                    if has_responsible_info:
                        columns += ("Ответственный",)
                        col_widths += [150]
                    tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=6)
                    for col, width in zip(columns, col_widths):
                        tree.heading(col, text=col)
                        tree.column(col, width=width, anchor='center')
                    total_sum = 0
                    total_qty = 0
                    for detail in details:
                        product_name, qty, price, cell_id = detail[:4]
                        sum_row = qty * price
                        total_sum += sum_row
                        total_qty += qty  # Суммируем количество
                        if has_responsible_info:
                            emp_id, last_name, first_name, middle_name, email = detail[4:]
                            responsible = ""
                            if last_name:
                                responsible = f"{last_name} {first_name}"
                                if middle_name and middle_name != "не указано":
                                    responsible += f" {middle_name}"
                            display_email = email if email else "не указана"
                            tree.insert("", "end", values=(
                                product_name,
                                qty,
                                f"{price:.2f}",
                                f"{sum_row:.2f}",
                                cell_id if cell_id else "Не указана",
                                responsible if responsible else "Не назначен"
                            ))
                        else:
                            tree.insert("", "end", values=(
                                product_name,
                                qty,
                                f"{price:.2f}",
                                f"{sum_row:.2f}",
                                cell_id if cell_id else "Не указана"
                            ))
                    # Итоговая сумма и количество
                    if has_responsible_info:
                        tree.insert("", "end", values=("ИТОГО:", f"{total_qty}", "", f"{total_sum:.2f}", "", ""),
                                    tags=('total',))
                    else:
                        tree.insert("", "end", values=("ИТОГО:", f"{total_qty}", "", f"{total_sum:.2f}", ""),
                                    tags=('total',))

                    tree.tag_configure('total', background='#f0f0f0', font=('Arial', 10, 'bold'))
                    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
                    tree.configure(yscrollcommand=scrollbar.set)
                    tree.pack(side='left', fill='both', expand=True)
                    scrollbar.pack(side='right', fill='y')
                    # Вкладка с информацией о ячейках и ответственных (только если есть доступ)
                    if has_responsible_info and any(detail[4] for detail in details):
                        employee_frame = ttk.Frame(notebook, padding=10)
                        notebook.add(employee_frame, text="Ответственные за ячейки")
                        ttk.Label(employee_frame, text="Ответственные за ячейки:", font=('Arial', 10, 'bold')).pack(
                            anchor='w', pady=5)
                        container = ttk.Frame(employee_frame)
                        container.pack(fill='both', expand=True)
                        canvas = tk.Canvas(container)
                        canvas.pack(side='left', fill='both', expand=True)
                        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
                        scrollbar.pack(side='right', fill='y')
                        canvas.configure(yscrollcommand=scrollbar.set)
                        scrollable_frame = ttk.Frame(canvas)
                        def on_configure(event):
                            canvas.configure(scrollregion=canvas.bbox("all"))
                        scrollable_frame.bind("<Configure>", on_configure)
                        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                        def on_canvas_configure(event):
                            canvas.itemconfig(window_id, width=event.width)
                        canvas.bind("<Configure>", on_canvas_configure)
                        employees = {}
                        for detail in details:
                            emp_id = detail[4]
                            if emp_id and emp_id not in employees:
                                employees[emp_id] = {
                                    'name': f"{detail[5]} {detail[6]} {detail[7] if detail[7] != 'не указано' else ''}",
                                    'email': detail[8] if detail[8] else "не указана",
                                    'cells': set()
                                }
                            if emp_id:
                                employees[emp_id]['cells'].add(detail[3])
                        for emp_id, emp_data in employees.items():
                            card_frame = ttk.Frame(scrollable_frame, padding=10, relief='ridge', borderwidth=1)
                            card_frame.pack(fill='x', pady=5, expand=True)
                            info_frame = ttk.Frame(card_frame)
                            info_frame.pack(fill='x', expand=True)
                            ttk.Label(info_frame, text=f"Сотрудник: {emp_data['name']}",
                                      font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 5))
                            ttk.Label(info_frame, text=f"Email: {emp_data['email']}").pack(anchor='w')
                            ttk.Label(info_frame, text=f"Ячейки: {', '.join(map(str, emp_data['cells']))}").pack(
                                anchor='w')
                        def _on_mousewheel(event):
                            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                        scrollable_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
                        scrollable_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
                        def on_close():
                            canvas.unbind_all("<MouseWheel>")
                            info_window.destroy()
                        info_window.protocol("WM_DELETE_WINDOW", on_close)
                except Exception as e:
                    error_handler(f"Ошибка при получении данных о поступлении: {str(e)}")
                    traceback.print_exc()
        elif current_table in ["discount","discount_product","activediscounts"]:
            discount_id = item_data[0]
            try:
                cursor = connection.cursor()
                # Получаем основную информацию о скидке
                cursor.execute("""
                               SELECT Start_Date,
                                      End_Date,
                                      Discount_Percent,
                                      Qty_Required,
                                      Min_Amount
                               FROM discount
                               WHERE ID = %s
                               """, (discount_id,))
                discount_data = cursor.fetchone()
                if not discount_data:
                    messagebox.showerror("Ошибка", "Скидка не найдена")
                    return
                start_date, end_date, discount_percent, qty_required, min_amount = discount_data
                # Получаем список товаров с этой скидкой
                cursor.execute("""
                               SELECT p.ID,
                                      p.Name,
                                      c.Name as Category,
                                      p.Price_Wholesale,
                                      p.Price_Retail
                               FROM product p
                                        JOIN discount_product dp ON p.ID = dp.Product_ID
                                        JOIN category c ON p.Category_ID = c.ID
                               WHERE dp.Discount_ID = %s
                               """, (discount_id,))
                products = cursor.fetchall()
                cursor.close()
                info_window = tk.Toplevel()
                info_window.title(f"Скидка ID: {discount_id}")
                info_window.geometry("800x600")
                notebook = ttk.Notebook(info_window)
                notebook.pack(fill='both', expand=True)
                main_frame = ttk.Frame(notebook, padding=10)
                notebook.add(main_frame, text="Основная информация")
                ttk.Label(main_frame, text=f"Скидка ID: {discount_id}",
                          font=('Arial', 12, 'bold')).pack(anchor='w', pady=5)
                info_frame = ttk.Frame(main_frame)
                info_frame.pack(fill='x', padx=10, pady=10)
                def add_info_row(parent, label, value):
                    row = ttk.Frame(parent)
                    row.pack(fill='x', pady=2)
                    ttk.Label(row, text=label + ":", width=20, anchor='w').pack(side='left')
                    ttk.Label(row, text=str(value) if value is not None else "не указано").pack(side='left')
                add_info_row(info_frame, "Дата начала", start_date.strftime('%Y-%m-%d') if start_date else None)
                add_info_row(info_frame, "Дата окончания", end_date.strftime('%Y-%m-%d') if end_date else None)
                add_info_row(info_frame, "Процент скидки", f"{discount_percent}%")
                add_info_row(info_frame, "Мин. количество", qty_required)
                add_info_row(info_frame, "Мин. сумма", min_amount)
                ttk.Label(main_frame, text="Товары с этой скидкой:",
                          font=('Arial', 10, 'bold')).pack(anchor='w', pady=10)
                columns = ("ID", "Наименование", "Категория", "Оптовая цена", "Розничная цена")
                tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=8)
                col_widths = [50, 250, 150, 120, 120]
                for col, width in zip(columns, col_widths):
                    tree.heading(col, text=col)
                    tree.column(col, width=width, anchor='center')
                for product in products:
                    tree.insert("", "end", values=(
                        product[0],
                        product[1],
                        product[2],
                        f"{product[3]:.2f}",
                        f"{product[4]:.2f}"
                    ))
                scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)
                tree.pack(side='left', fill='both', expand=True)
                scrollbar.pack(side='right', fill='y')
            except Exception as e:
                error_handler(f"Ошибка при получении данных о скидке: {str(e)}")
                traceback.print_exc()
        elif current_table in ["transaction", "transaction_date", "transaction_details", "max_transaction_status" ]:
            transaction_id = item_data[0]
            show_transaction_details(connection, transaction_id=transaction_id, parent_window=employee_window)
        elif current_table in ["customer","customer_phone"]:
            customer_id = item_data[0]
            # Запрос основной информации о клиенте
            cursor = connection.cursor()
            cursor.execute("""
                           SELECT ID, Last_Name, First_Name, Middle_Name, Organization, Email
                           FROM customer
                           WHERE ID = %s
                           """, (customer_id,))
            customer_info = cursor.fetchone()
            if customer_info:
                customer_dict = {
                    'ID': customer_info[0],
                    'Last_Name': customer_info[1],
                    'First_Name': customer_info[2],
                    'Middle_Name': customer_info[3],
                    'Organization': customer_info[4],
                    'Email': customer_info[5]
                }
                phones_string = None
                try:
                    # Попытка запроса телефонов клиента
                    cursor.execute("SELECT Phone FROM customer_phone WHERE Customer_ID = %s", (customer_id,))
                    phones = [row[0] for row in cursor.fetchall()]
                    phones_string = ", ".join(phones) if phones else "Нет данных"
                except Exception as e:
                    pass
                # Запрос транзакций клиента
                cursor.execute("""
                               SELECT t.ID, td.DateTime, t.Total_Cost, s.Name
                               FROM transaction t
                                        JOIN transaction_date td ON t.ID = td.Transaction_ID
                                        JOIN status s ON td.Status_ID = s.ID
                               WHERE t.Customer_ID = %s
                                 AND td.DateTime = (SELECT MAX(td2.DateTime)
                                                    FROM transaction_date td2
                                                    WHERE td2.Transaction_ID = t.ID)
                               ORDER BY td.DateTime DESC
                               """, (customer_id,))
                transactions = []
                for row in cursor.fetchall():
                    transactions.append({
                        'ID': row[0],
                        'DateTime': row[1],
                        'Total_Cost': row[2],
                        'Status': row[3]
                    })
                cursor.close()
                detail_window = tk.Toplevel(employee_window)
                detail_window.title(f"Информация о клиенте: {customer_dict['Last_Name']} {customer_dict['First_Name']}")
                detail_window.geometry("800x600")
                notebook = ttk.Notebook(detail_window)
                notebook.pack(expand=True, fill='both', padx=10, pady=10)
                def create_section(parent, title, content):
                    frame = ttk.Frame(parent)
                    frame.pack(fill='x', padx=10, pady=5)
                    title_label = ttk.Label(
                        frame,
                        text=f"{title}",
                        font=('Helvetica', 10, 'bold')
                    )
                    title_label.pack(anchor='w')
                    content_label = ttk.Label(
                        frame,
                        text=content,
                        font=('Helvetica', 9),
                        justify='left'
                    )
                    content_label.pack(anchor='w')
                info_tab = ttk.Frame(notebook)
                notebook.add(info_tab, text="Основная информация")
                customer_content = f"""
                        ID клиента: {customer_dict['ID']}
                        Фамилия: {customer_dict['Last_Name']}
                        Имя: {customer_dict['First_Name']}
                        Отчество: {customer_dict['Middle_Name'] or "Не указано"}
                        Организация: {customer_dict['Organization'] or "Не указана"}
                        Email: {customer_dict['Email'] or "Не указан"}
                        """
                # Добавляем информацию о телефонах, только если она есть
                if phones_string is not None:
                    customer_content += f"Телефоны: {phones_string}\n"
                create_section(info_tab, "Основная информация:", customer_content)
                transactions_tab = ttk.Frame(notebook)
                notebook.add(transactions_tab, text="Транзакции")
                tree = ttk.Treeview(transactions_tab, columns=("ID", "Дата", "Сумма", "Статус"), show="headings")
                tree.heading("ID", text="ID")
                tree.heading("Дата", text="Дата")
                tree.heading("Сумма", text="Сумма")
                tree.heading("Статус", text="Статус")
                tree.column("ID", width=50, anchor="center")
                tree.column("Дата", width=150, anchor="center")
                tree.column("Сумма", width=100, anchor="center")
                tree.column("Статус", width=150, anchor="center")
                for trans in transactions:
                    tree.insert("", "end", values=(
                        trans['ID'],
                        trans['DateTime'],
                        f"{trans['Total_Cost']:.2f}",
                        trans['Status']
                    ))
                def on_transaction_double_click(event):
                    item = tree.selection()[0]
                    transaction_id = tree.item(item, "values")[0]
                    show_transaction_details(connection, transaction_id=transaction_id, parent_window=detail_window)
                tree.bind("<Double-1>", on_transaction_double_click)
                scrollbar = ttk.Scrollbar(transactions_tab, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)
                tree.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
            else:
                messagebox.showerror("Ошибка", "Клиент не найден", parent=employee_window)
                cursor.close()
        elif current_table in ["product","product_cell"]:
                product_id = item_data[0]
                try:
                    cursor = connection.cursor()
                    # Получаем основную информацию о товаре
                    cursor.execute("""
                                   SELECT p.Name,
                                          p.Description,
                                          c.Name as Category,
                                          p.Qty_for_Wholesale,
                                          p.Price_Wholesale,
                                          p.Price_Retail
                                   FROM product p
                                            JOIN category c ON p.Category_ID = c.ID
                                   WHERE p.ID = %s
                                   """, (product_id,))
                    product_data = cursor.fetchone()
                    if not product_data:
                        messagebox.showerror("Ошибка", "Товар не найден")
                        return
                    name, description, category, qty_wholesale, price_wholesale, price_retail = product_data
                    info_window = tk.Toplevel()
                    info_window.title(f"Товар: {name}")
                    info_window.geometry("900x600")
                    notebook = ttk.Notebook(info_window)
                    notebook.pack(fill='both', expand=True)
                    main_frame = ttk.Frame(notebook, padding=10)
                    notebook.add(main_frame, text="Основная информация")
                    ttk.Label(main_frame, text=f"Наименование: {name}", font=('Arial', 10, 'bold')).pack(anchor='w',pady=5)
                    ttk.Label(main_frame, text=f"Описание: {description if description else 'не указано'}").pack(
                        anchor='w', pady=5)
                    ttk.Label(main_frame, text=f"Категория: {category}").pack(anchor='w', pady=5)
                    ttk.Label(main_frame, text=f"Минимальное количество для опта: {qty_wholesale}").pack(anchor='w',pady=5)
                    ttk.Label(main_frame, text=f"Оптовая цена: {price_wholesale:.2f}").pack(anchor='w', pady=5)
                    ttk.Label(main_frame, text=f"Розничная цена: {price_retail:.2f}").pack(anchor='w', pady=5)
                    # Информация о наличии (пробуем получить из product_cell)
                    try:
                        cursor.execute("""
                                       SELECT Qty_in_Stock
                                       FROM product_cell
                                       WHERE Product_ID = %s
                                       """, (product_id,))
                        stock_data = cursor.fetchone()
                        ttk.Label(main_frame, text="Наличие на складе:", font=('Arial', 10, 'bold')).pack(anchor='w',pady=(15, 5))
                        if stock_data:
                            qty_in_stock = stock_data[0]
                            ttk.Label(main_frame, text=f"Количество: {qty_in_stock}").pack(anchor='w', pady=2)
                            # Пробуем получить информацию о ячейке и сотруднике (если есть доступ к cell)
                            try:
                                cursor.execute("""
                                               SELECT pc.Cell_ID, cl.Employee_id
                                               FROM product_cell pc
                                                        LEFT JOIN cell cl ON pc.Cell_ID = cl.ID
                                               WHERE pc.Product_ID = %s
                                               """, (product_id,))
                                cell_data = cursor.fetchone()
                                if cell_data and cell_data[0]:
                                    ttk.Label(main_frame, text=f"Ячейка: {cell_data[0]}").pack(anchor='w', pady=2)
                                    # Если есть employee_id, пробуем получить информацию о сотруднике
                                    if cell_data[1]:
                                        try:
                                            cursor.execute("""
                                                           SELECT c.Last_Name,
                                                                  c.First_Name,
                                                                  c.Middle_Name,
                                                                  c.Email,
                                                                  r.role_name
                                                           FROM employee e
                                                                    JOIN customer c ON e.customer_id = c.ID
                                                                    JOIN role r ON e.role_id = r.role_id
                                                           WHERE e.employee_id = %s
                                                           """, (cell_data[1],))
                                            employee_data = cursor.fetchone()
                                            if employee_data:
                                                employee_frame = ttk.Frame(notebook, padding=10)
                                                notebook.add(employee_frame, text="Ответственный")
                                                last_name, first_name, middle_name, email, role = employee_data
                                                full_name = f"{last_name} {first_name} {middle_name if middle_name and middle_name != 'не указано' else ''}"
                                                ttk.Label(employee_frame,
                                                          text="Информация об ответственном сотруднике:",
                                                          font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
                                                ttk.Label(employee_frame, text=f"ФИО: {full_name}").pack(anchor='w', pady=2)
                                                ttk.Label(employee_frame, text=f"Должность: {role}").pack(anchor='w', pady=2)
                                                ttk.Label(employee_frame,
                                                          text=f"Email: {email if email else 'не указан'}").pack(anchor='w', pady=2)
                                                ttk.Label(employee_frame, text=f"Ячейка: {cell_data[0]}").pack(anchor='w', pady=2)
                                                # Пробуем получить телефоны сотрудника
                                                try:
                                                    cursor.execute("""
                                                                   SELECT Phone
                                                                   FROM customer_phone
                                                                   WHERE Customer_ID = (SELECT customer_id
                                                                                        FROM employee
                                                                                        WHERE employee_id = %s)
                                                                   """, (cell_data[1],))
                                                    phones = cursor.fetchall()
                                                    if phones:
                                                        phone_text = ", ".join([phone[0] for phone in phones])
                                                        ttk.Label(employee_frame, text=f"Телефоны: {phone_text}").pack(
                                                            anchor='w', pady=2)
                                                    else:
                                                        ttk.Label(employee_frame, text="Телефоны: не указаны").pack(
                                                            anchor='w', pady=2)
                                                except:
                                                    pass  # Нет доступа к customer_phone
                                        except:
                                            pass  # Нет доступа к employee или связанным таблицам
                            except:
                                pass  # Нет доступа к cell
                        else:
                            ttk.Label(main_frame, text="Товар отсутствует на складе").pack(anchor='w', pady=2)
                    except:
                        pass  # Нет доступа к product_cell
                    # Вкладка с историей поступлений (если есть доступ к supply и supply_detail)
                    try:
                        cursor.execute("""
                                       SELECT s.ID,
                                              s.DateTime,
                                              s.Invoice_Number,
                                              sd.Qty,
                                              sd.Purchase_Price
                                       FROM supply_detail sd
                                                JOIN supply s ON sd.Supply_ID = s.ID
                                       WHERE sd.Product_ID = %s
                                       ORDER BY s.DateTime DESC
                                       """, (product_id,))
                        supply_data = cursor.fetchall()
                        if supply_data:
                            supply_frame = ttk.Frame(notebook, padding=10)
                            notebook.add(supply_frame, text="Поступления")
                            ttk.Label(supply_frame, text="История поступлений товара:",
                                      font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
                            columns = ("ID", "Дата", "Накладная", "Кол-во", "Цена закупки", "Сумма")
                            tree = ttk.Treeview(supply_frame, columns=columns, show="headings", height=10)
                            for col in columns:
                                tree.heading(col, text=col)
                                tree.column(col, width=100, anchor='center')
                            tree.column("Дата", width=150)
                            total_qty = 0
                            total_sum = 0
                            for supply in supply_data:
                                supply_id, date_time, invoice_number, qty, price = supply
                                sum_row = qty * price
                                total_qty += qty
                                total_sum += sum_row
                                tree.insert("", "end", values=(
                                    supply_id,
                                    date_time.strftime('%Y-%m-%d %H:%M'),
                                    invoice_number,
                                    qty,
                                    f"{price:.2f}",
                                    f"{sum_row:.2f}"
                                ))
                            # Добавляем итоговую строку
                            tree.insert("", "end", values=(
                                "ИТОГО:",
                                "",
                                "",
                                total_qty,
                                "",
                                f"{total_sum:.2f}"
                            ), tags=('total',))
                            tree.tag_configure('total', background='#f0f0f0', font=('Arial', 10, 'bold'))
                            scrollbar = ttk.Scrollbar(supply_frame, orient="vertical", command=tree.yview)
                            tree.configure(yscrollcommand=scrollbar.set)
                            scrollbar.pack(side='right', fill='y')
                            tree.pack(fill='both', expand=True)
                    except:
                        pass  # Нет доступа к supply или supply_detail
                    cursor.close()
                except Exception as e:
                    error_handler(f"Ошибка при получении данных о товаре: {str(e)}")
                    traceback.print_exc()
        elif current_table == "cell":
                    cell_id = item_data[0]
                    try:
                        cursor = connection.cursor()
                        info_window = tk.Toplevel()
                        info_window.title(f"Ячейка: {cell_id}")
                        info_window.geometry("900x600")
                        notebook = ttk.Notebook(info_window)
                        notebook.pack(fill='both', expand=True)
                        main_frame = ttk.Frame(notebook, padding=10)
                        notebook.add(main_frame, text="Основная информация")
                        try:
                            cursor.execute("""
                                           SELECT Employee_id
                                           FROM cell
                                           WHERE ID = %s
                                           """, (cell_id,))
                            employee_result = cursor.fetchone()
                            if employee_result:
                                employee_id = employee_result[0]
                                if employee_id:
                                    try:
                                        cursor.execute("""
                                                       SELECT c.Last_Name,
                                                              c.First_Name,
                                                              c.Middle_Name,
                                                              c.Email,
                                                              r.role_name
                                                       FROM employee e
                                                                JOIN customer c ON e.customer_id = c.ID
                                                                JOIN role r ON e.role_id = r.role_id
                                                       WHERE e.employee_id = %s
                                                       """, (employee_id,))
                                        employee_data = cursor.fetchone()
                                        if employee_data:
                                            last_name, first_name, middle_name, email, role = employee_data
                                            full_name = f"{last_name} {first_name} {middle_name if middle_name and middle_name != 'не указано' else ''}"
                                            ttk.Label(main_frame, text="Ответственный сотрудник:",
                                                      font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
                                            ttk.Label(main_frame, text=f"ФИО: {full_name}").pack(anchor='w', pady=2)
                                            ttk.Label(main_frame, text=f"Должность: {role}").pack(anchor='w', pady=2)
                                            ttk.Label(main_frame,
                                                      text=f"Email: {email if email else 'не указан'}").pack(anchor='w',pady=2)
                                            try:
                                                cursor.execute("""
                                                               SELECT Phone
                                                               FROM customer_phone
                                                               WHERE Customer_ID = (SELECT customer_id
                                                                                    FROM employee
                                                                                    WHERE employee_id = %s)
                                                               """, (employee_id,))
                                                phones = cursor.fetchall()
                                                if phones:
                                                    phone_text = ", ".join([phone[0] for phone in phones])
                                                    ttk.Label(main_frame, text=f"Телефоны: {phone_text}").pack(
                                                        anchor='w', pady=2)
                                                else:
                                                    ttk.Label(main_frame, text="Телефоны: не указаны").pack(anchor='w', pady=2)
                                            except:
                                                pass  # Нет доступа к customer_phone
                                    except:
                                        pass  # Нет доступа к employee или связанным таблицам
                                else:  # Если employee_id NULL
                                    ttk.Label(main_frame, text="Ответственный за ячейку не назначен",
                                              font=('Arial', 10)).pack(anchor='w', pady=5)
                        except:
                            pass  # Нет доступа к cell
                        products_frame = ttk.Frame(notebook, padding=10)
                        notebook.add(products_frame, text="Товары в ячейке")
                        try:
                            cursor.execute("""
                                           SELECT p.ID,
                                                  p.Name,
                                                  pc.Qty_in_Stock,
                                                  p.Price_Retail,
                                                  p.Price_Wholesale
                                           FROM product_cell pc
                                                    JOIN product p ON pc.Product_ID = p.ID
                                           WHERE pc.Cell_ID = %s
                                           ORDER BY p.Name
                                           """, (cell_id,))
                            products_data = cursor.fetchall()
                            if products_data:
                                ttk.Label(products_frame, text=f"Товары в ячейке {cell_id}:",
                                          font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
                                columns = ("ID", "Наименование", "Количество", "Розничная цена", "Оптовая цена")
                                tree = ttk.Treeview(products_frame, columns=columns, show="headings", height=10)
                                for col in columns:
                                    tree.heading(col, text=col)
                                    tree.column(col, width=120, anchor='center')
                                tree.column("Наименование", width=200, anchor='w')
                                for product in products_data:
                                    product_id, product_name, qty, price_retail, price_wholesale = product
                                    tree.insert("", "end", values=(
                                        product_id,
                                        product_name,
                                        qty,
                                        f"{price_retail:.2f}",
                                        f"{price_wholesale:.2f}"
                                    ))
                                scrollbar = ttk.Scrollbar(products_frame, orient="vertical", command=tree.yview)
                                tree.configure(yscrollcommand=scrollbar.set)
                                scrollbar.pack(side='right', fill='y')
                                tree.pack(fill='both', expand=True)
                            else:
                                ttk.Label(products_frame, text="В ячейке нет товаров").pack(anchor='w', pady=5)
                        except:
                            ttk.Label(products_frame, text="Нет доступа к информации о товарах").pack(anchor='w', pady=5)
                        cursor.close()
                    except Exception as e:
                        error_handler(f"Ошибка при получении данных о ячейке: {str(e)}")
                        traceback.print_exc()
    tree.bind("<Double-1>", on_double_click)
    current_columns = []
    current_table = ""
    current_sort_column = None
    current_sort_order = None  # None - нет сортировки, 'asc' - по возрастанию, 'desc' - по убыванию
    def check_permission(table, permission):
        '''Функция для проверки прав доступа'''
        permissions = role_permissions.get(current_role, {}).get(table, {})
        return permissions.get(permission, False)
    def update_control_buttons():
        # Удаляем все кнопки
        for widget in control_buttons_frame.winfo_children():
            widget.destroy()
        if not current_table:
            return
        # Добавляем кнопки в зависимости от прав
        if check_permission(current_table, 'add'):
            add_button = ttk.Button(control_buttons_frame, text="Добавить", command=add_record)
            add_button.pack(side='left', padx=2)
        if check_permission(current_table, 'edit'):
            edit_button = ttk.Button(control_buttons_frame, text="Изменить", command=edit_record)
            edit_button.pack(side='left', padx=2)
        if check_permission(current_table, 'delete'):
            delete_button = ttk.Button(control_buttons_frame, text="Удалить", command=delete_record)
            delete_button.pack(side='left', padx=2)
    def add_record():
        """Добавление новой записи в текущую таблицу"""
        if not check_permission(current_table, 'add'):
            ErrorWindow("У вас нет прав на добавление записей в эту таблицу")
            return
        try:
            add_window = tk.Toplevel()
            add_window.title(f"Добавление записи в таблицу {current_table}")
            add_window.resizable(False, False)
            container = ttk.Frame(add_window)
            container.pack(expand=True, fill='both', padx=20, pady=10)
            header_frame = ttk.Frame(container)
            header_frame.pack(fill='x', pady=(0, 15))
            ttk.Label(
                header_frame,
                text=f"Добавление новой записи в таблицу '{current_table}'",
                font=('Helvetica', 10, 'bold'),
                foreground="#333333"
            ).pack(side='top', anchor='w')
            ttk.Separator(header_frame, orient='horizontal').pack(fill='x', pady=5)
            with connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {current_table}")
                columns_info = cursor.fetchall()
            inputs = {}
            column_types = {}
            max_label_width = max(len(column[0]) for column in columns_info)
            for column in columns_info:
                col_name = column[0]
                col_type = column[1]
                column_types[col_name] = col_type
                row_frame = ttk.Frame(container)
                row_frame.pack(fill='x', pady=5)
                ttk.Label(
                    row_frame,
                    text=col_name + ":",
                    width=max_label_width,
                    anchor='e'
                ).pack(side='left', padx=(0, 12))
                entry = ttk.Entry(row_frame)
                entry.pack(side='left', fill='x', expand=True, ipady=4)
                inputs[col_name] = entry
            def convert_value(val, col_type):
                """Конвертация значения в соответствующий тип данных"""
                if not val or val.strip() == "":
                    return None
                try:
                    if "int" in col_type:
                        return int(val)
                    if "double" in col_type or "float" in col_type or "decimal" in col_type:
                        return float(val)
                    return val
                except ValueError:
                    return None
            def submit():
                """Сохранение данных в базу"""
                try:
                    with connection.cursor() as cursor:
                        data = {
                            col_name: convert_value(entry.get(), column_types[col_name])
                            for col_name, entry in inputs.items()
                        }
                        # Формируем запрос только для заполненных полей
                        columns = [col for col, val in data.items() if val is not None]
                        values = [val for val in data.values() if val is not None]
                        if not columns:
                            messagebox.showwarning("Ошибка", "Не заполнено ни одного поля")
                            return
                        query = f"""
                            INSERT INTO {current_table} ({', '.join(columns)}) 
                            VALUES ({', '.join(['%s'] * len(values))})
                        """
                        cursor.execute(query, values)
                        connection.commit()
                    messagebox.showinfo("Успех", "Запись успешно добавлена")
                    add_window.destroy()
                    load_table_data()  # Обновляем таблицу
                except Exception as e:
                    ErrorWindow(f"Ошибка при добавлении записи: {str(e)}")
            button_frame = ttk.Frame(container)
            button_frame.pack(pady=15)
            ttk.Separator(container, orient='horizontal').pack(fill='x', pady=10)
            ttk.Button(
                button_frame,
                text="Сохранить",
                command=submit,
                style="Accent.TButton"
            ).pack(ipadx=15, ipady=6)
        except Exception as e:
            ErrorWindow(f"Ошибка при подготовке формы добавления: {str(e)}")
    def edit_record():
        """Редактирование выбранной записи в таблице"""
        selected_item = tree.focus()
        if not selected_item:
            ErrorWindow("Выберите запись для редактирования")
            return
        if not check_permission(current_table, 'edit'):
            ErrorWindow("У вас нет прав на редактирование записей в этой таблице")
            return
        if current_table == "transaction":
            transaction_id = tree.item(selected_item)['values'][0]
            show_edit_transaction_window(connection, load_table_data, transaction_id)
            return
        if current_table == "supply":
            transaction_id = tree.item(selected_item)['values'][0]
            show_edit_supply_window(connection, load_table_data, transaction_id)
            return
        try:
            item_data = tree.item(selected_item)['values']
            if not item_data:
                ErrorWindow("Не удалось получить данные выбранной записи")
                return
            edit_window = tk.Toplevel()
            edit_window.title(f"Редактирование записи в таблице {current_table}")
            edit_window.resizable(False, False)
            container = ttk.Frame(edit_window)
            container.pack(expand=True, fill='both', padx=20, pady=10)
            header_frame = ttk.Frame(container)
            header_frame.pack(fill='x', pady=(0, 15))
            ttk.Label(
                header_frame,
                text=f"Редактирование записи в таблице '{current_table}'",
                font=('Helvetica', 10, 'bold'),
                foreground="#333333"
            ).pack(side='top', anchor='w')
            ttk.Separator(header_frame, orient='horizontal').pack(fill='x', pady=5)
            with connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {current_table}")
                columns_info = cursor.fetchall()
            inputs = {}
            column_types = {}
            max_label_width = max(len(column[0]) for column in columns_info)
            for i, column in enumerate(columns_info):
                col_name = column[0]
                col_type = column[1]
                column_types[col_name] = col_type
                row_frame = ttk.Frame(container)
                row_frame.pack(fill='x', pady=5)
                ttk.Label(
                    row_frame,
                    text=col_name + ":",
                    width=max_label_width,
                    anchor='e'
                ).pack(side='left', padx=(0, 12))
                entry = ttk.Entry(row_frame)
                if i < len(item_data):
                    entry.insert(0, str(item_data[i]) if item_data[i] is not None else "")
                entry.pack(side='left', fill='x', expand=True, ipady=4)
                inputs[col_name] = entry
            def convert_value(val, col_type):
                """Конвертация значения в соответствующий тип данных"""
                if not val or val.strip() == "" or val.strip().lower() == "none":
                    return None
                try:
                    if "int" in col_type:
                        return int(val)
                    if "double" in col_type or "float" in col_type or "decimal" in col_type:
                        return float(val)
                    return val
                except ValueError:
                    return None
            def save_changes():
                """Сохранение изменений в базу (с учетом всех старых значений в WHERE)"""
                try:
                    with connection.cursor() as cursor:
                        updated_values = {
                            col_name: convert_value(entry.get(), column_types[col_name])
                            for col_name, entry in inputs.items()
                        }
                        set_parts = [f"`{col}` = %s" for col in updated_values.keys()]
                        set_values = list(updated_values.values())
                        # Условие по всем старым значениям строки
                        where_parts = []
                        where_values = []
                        for (col, old_val) in zip(inputs.keys(), item_data):
                            if old_val is not None and str(old_val).strip().lower() != "none":
                                where_parts.append(f"`{col}` = %s")
                                where_values.append(old_val)
                        if not where_parts:
                            messagebox.showerror("Ошибка", "Не удалось построить WHERE условие для обновления.")
                            return
                        query = f"""
                            UPDATE `{current_table}`
                            SET {', '.join(set_parts)}
                            WHERE {' AND '.join(where_parts)}
                        """
                        cursor.execute(query, set_values + where_values)
                        connection.commit()
                    messagebox.showinfo("Успех", "Запись успешно обновлена")
                    edit_window.destroy()
                    load_table_data()
                except Exception as e:
                    ErrorWindow(f"Ошибка при обновлении записи: {str(e)}")
            button_frame = ttk.Frame(container)
            button_frame.pack(pady=15)
            ttk.Separator(container, orient='horizontal').pack(fill='x', pady=10)
            ttk.Button(
                button_frame,
                text="Сохранить изменения",
                command=save_changes,
                style="Accent.TButton"
            ).pack(ipadx=15, ipady=6)
        except Exception as e:
            ErrorWindow(f"Ошибка при подготовке формы редактирования: {str(e)}")
    def delete_record():
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning("Удаление", "Пожалуйста, выберите строку для удаления.")
            return
        if not check_permission(current_table, 'delete'):
            error_handler("У вас нет прав на удаление записей из этой таблицы")
            return
        confirm = messagebox.askyesno("Подтверждение удаления", "Вы уверены, что хотите удалить выбранную запись?")
        if not confirm:
            return
        try:
            cursor = connection.cursor()
            cursor.execute(f"DESCRIBE {current_table}")
            columns_info = cursor.fetchall()
            column_names = [column[0] for column in columns_info]
            values = tree.item(selected_item, 'values')
            # Создаем условие только для непустых значений
            conditions = []
            params = []
            for col, val in zip(column_names, values):
                if val is not None and val != 'None' and val != '':
                    conditions.append(f"`{col}` = %s")
                    params.append(val)
            if not conditions:
                messagebox.showerror("Ошибка", "Не удалось определить условия для удаления записи.")
                return
            where_clause = " AND ".join(conditions)
            delete_query = f"DELETE FROM `{current_table}` WHERE {where_clause}"
            cursor.execute(delete_query, params)
            connection.commit()
            cursor.close()
            messagebox.showinfo("Успех", "Запись успешно удалена.")
            load_table_data()
        except Exception as e:
            error_handler(f"Ошибка при удалении записи: {str(e)}")
            connection.rollback()
    def sort_data(column):
        '''Функция для сортировки данных'''
        nonlocal current_sort_column, current_sort_order
        if column == current_sort_column:
            # Меняем порядок сортировки
            if current_sort_order == 'asc':
                current_sort_order = 'desc'
            elif current_sort_order == 'desc':
                current_sort_order = None
            else:
                current_sort_order = 'asc'
        else:
            # Новый столбец для сортировки
            current_sort_column = column
            current_sort_order = 'asc'
        load_table_data()
    def show_add_transaction_window(connection, refresh_callback):
        add_window = tk.Toplevel()
        add_window.title("Добавить транзакцию")
        add_window.geometry("900x700")
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10), padding=5)
        style.configure("TEntry", font=('Arial', 10), padding=5)
        style.configure("Treeview", font=('Arial', 10), rowheight=25)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        main_frame = ttk.Frame(add_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        transaction_frame = ttk.LabelFrame(main_frame, text="Информация о транзакции", padding=10)
        transaction_frame.pack(fill='x', pady=5)
        ttk.Label(transaction_frame, text="ID покупателя:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        customer_id_entry = ttk.Entry(transaction_frame)
        customer_id_entry.grid(row=0, column=1, sticky='we', padx=5, pady=5)
        # Скрытые поля с автоматическими значениями
        discount_id_entry = ttk.Entry(transaction_frame)
        discount_id_entry.grid_remove()
        total_cost_entry = ttk.Entry(transaction_frame)
        total_cost_entry.insert(0, "0")
        total_cost_entry.grid_remove()
        details_frame = ttk.LabelFrame(main_frame, text="Детали транзакции", padding=10)
        details_frame.pack(fill='both', expand=True, pady=5)
        columns = ("ID товара", "Количество")
        products_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=5)
        for col in columns:
            products_tree.heading(col, text=col)
            products_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=products_tree.yview)
        products_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        products_tree.pack(fill='both', expand=True, pady=5)
        add_product_frame = ttk.Frame(details_frame)
        add_product_frame.pack(fill='x', pady=5)
        ttk.Label(add_product_frame, text="ID товара:").pack(side='left', padx=5)
        product_id_entry = ttk.Entry(add_product_frame, width=12)
        product_id_entry.pack(side='left', padx=5)
        ttk.Label(add_product_frame, text="Количество:").pack(side='left', padx=5)
        qty_entry = ttk.Entry(add_product_frame, width=12)
        qty_entry.pack(side='left', padx=5)
        # Скрытое поле для цены
        price_entry = ttk.Entry(add_product_frame, width=12)
        price_entry.insert(0, "0")
        price_entry.pack_forget()
        def add_product():
            product_id = product_id_entry.get()
            qty = qty_entry.get()
            if not all([product_id, qty]):
                messagebox.showerror("Ошибка", "Заполните ID товара и количество")
                return
            products_tree.insert("", "end", values=(product_id, qty))
            product_id_entry.delete(0, 'end')
            qty_entry.delete(0, 'end')
            product_id_entry.focus()
        add_button = ttk.Button(add_product_frame, text="Добавить товар", command=add_product)
        add_button.pack(side='left', padx=10)
        def remove_product():
            selected_item = products_tree.selection()
            if selected_item:
                products_tree.delete(selected_item)
        remove_button = ttk.Button(add_product_frame, text="Удалить товар", command=remove_product)
        remove_button.pack(side='left', padx=5)
        def save_transaction():
            cursor = None
            try:
                cursor = connection.cursor()
                customer_id = customer_id_entry.get()
                discount_id = None  # Автоматическое значение
                total_cost = "0"  # Автоматическое значение
                if not customer_id:
                    messagebox.showerror("Ошибка", "Введите ID покупателя")
                    return
                if not products_tree.get_children():
                    messagebox.showerror("Ошибка", "Добавьте хотя бы один товар")
                    return
                if connection.in_transaction:
                    connection.rollback()
                connection.start_transaction()
                # 1. Добавляем запись в transaction
                cursor.execute("""
                               INSERT INTO transaction (Customer_ID, Discount_id, Total_Cost)
                               VALUES (%s, %s, %s)
                               """, (customer_id, discount_id, total_cost))
                transaction_id = cursor.lastrowid
                print(transaction_id )
                # 2. Добавляем детали транзакции
                for item in products_tree.get_children():
                    product_id, qty = products_tree.item(item)['values']
                    cursor.execute("""
                                   INSERT INTO transaction_details (Transaction_ID, Product_ID, Qty, Price)
                                   VALUES (%s, %s, %s, %s)
                                   """, (transaction_id, product_id, qty, "0"))
                    # Фиксируем изменения
                connection.commit()
                messagebox.showinfo("Успех", "Транзакция успешно добавлена")
                add_window.destroy()
                refresh_callback()
            except Exception as e:
                if connection.in_transaction:
                    connection.rollback()
                messagebox.showerror("Ошибка", f"Ошибка при добавлении транзакции:\n{str(e)}")
            finally:
                if cursor:
                    cursor.close()
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=10)
        save_button = ttk.Button(buttons_frame, text="Сохранить транзакцию", command=save_transaction)
        save_button.pack(side='right', padx=5)
        cancel_button = ttk.Button(buttons_frame, text="Отмена", command=add_window.destroy)
        cancel_button.pack(side='right', padx=5)
        customer_id_entry.focus()
    def show_edit_transaction_window(connection, refresh_callback, transaction_id):
        edit_window = tk.Toplevel()
        edit_window.title("Редактировать транзакцию")
        edit_window.geometry("900x700")
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10), padding=5)
        style.configure("TEntry", font=('Arial', 10), padding=5)
        style.configure("Treeview", font=('Arial', 10), rowheight=25)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        main_frame = ttk.Frame(edit_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        transaction_frame = ttk.LabelFrame(main_frame, text="Информация о транзакции", padding=10)
        transaction_frame.pack(fill='x', pady=5)
        ttk.Label(transaction_frame, text="ID покупателя:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        customer_id_entry = ttk.Entry(transaction_frame)
        customer_id_entry.grid(row=0, column=1, sticky='we', padx=5, pady=5)
        try:
            cursor = connection.cursor()
            # Получаем информацию о транзакции
            cursor.execute("SELECT Customer_ID FROM `transaction` WHERE ID = %s", (transaction_id,))
            transaction_data = cursor.fetchone()
            if transaction_data:
                customer_id_entry.insert(0, transaction_data[0])
            # Получаем текущие детали транзакции
            cursor.execute("SELECT Product_ID, Qty FROM transaction_details WHERE Transaction_ID = %s",
                           (transaction_id,))
            current_details = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные транзакции:\n{str(e)}")
            edit_window.destroy()
            return
        finally:
            cursor.close()
        details_frame = ttk.LabelFrame(main_frame, text="Детали транзакции", padding=10)
        details_frame.pack(fill='both', expand=True, pady=5)
        columns = ("ID товара", "Количество")
        products_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=5)
        for col in columns:
            products_tree.heading(col, text=col)
            products_tree.column(col, width=120, anchor='center')
        for detail in current_details:
            products_tree.insert("", "end", values=detail)
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=products_tree.yview)
        products_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        products_tree.pack(fill='both', expand=True, pady=5)
        add_product_frame = ttk.Frame(details_frame)
        add_product_frame.pack(fill='x', pady=5)
        ttk.Label(add_product_frame, text="ID товара:").pack(side='left', padx=5)
        product_id_entry = ttk.Entry(add_product_frame, width=12)
        product_id_entry.pack(side='left', padx=5)
        ttk.Label(add_product_frame, text="Количество:").pack(side='left', padx=5)
        qty_entry = ttk.Entry(add_product_frame, width=12)
        qty_entry.pack(side='left', padx=5)
        def add_product():
            product_id = product_id_entry.get()
            qty = qty_entry.get()
            if not all([product_id, qty]):
                messagebox.showerror("Ошибка", "Заполните ID товара и количество")
                return
            products_tree.insert("", "end", values=(product_id, qty))
            product_id_entry.delete(0, 'end')
            qty_entry.delete(0, 'end')
            product_id_entry.focus()
        add_button = ttk.Button(add_product_frame, text="Добавить товар", command=add_product)
        add_button.pack(side='left', padx=10)
        def remove_product():
            selected_item = products_tree.selection()
            if selected_item:
                products_tree.delete(selected_item)
        remove_button = ttk.Button(add_product_frame, text="Удалить товар", command=remove_product)
        remove_button.pack(side='left', padx=5)
        def save_transaction():
            cursor = None
            try:
                cursor = connection.cursor()
                customer_id = customer_id_entry.get()
                if not customer_id:
                    messagebox.showerror("Ошибка", "Введите ID покупателя")
                    return
                if not products_tree.get_children():
                    messagebox.showerror("Ошибка", "Добавьте хотя бы один товар")
                    return
                if connection.in_transaction:
                    connection.rollback()
                connection.start_transaction()
                # 1. Обновляем основную информацию о транзакции
                cursor.execute("""
                               UPDATE transaction
                               SET Customer_ID = %s
                               WHERE ID = %s
                               """, (customer_id, transaction_id))
                # 2. Удаляем все текущие детали транзакции
                cursor.execute("""
                               DELETE
                               FROM transaction_details
                               WHERE Transaction_ID = %s
                               """, (transaction_id,))
                # 3. Добавляем новые детали транзакции
                for item in products_tree.get_children():
                    product_id, qty = products_tree.item(item)['values']
                    cursor.execute("""
                                   INSERT INTO transaction_details (Transaction_ID, Product_ID, Qty, Price)
                                   VALUES (%s, %s, %s, %s)
                                   """, (transaction_id, product_id, qty, "0"))
                # Фиксируем изменения
                connection.commit()
                messagebox.showinfo("Успех", "Транзакция успешно обновлена")
                edit_window.destroy()
                refresh_callback()
            except Exception as e:
                if connection.in_transaction:
                    connection.rollback()
                messagebox.showerror("Ошибка", f"Ошибка при обновлении транзакции:\n{str(e)}")
            finally:
                if cursor:
                    cursor.close()
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=10)
        save_button = ttk.Button(buttons_frame, text="Сохранить изменения", command=save_transaction)
        save_button.pack(side='right', padx=5)
        cancel_button = ttk.Button(buttons_frame, text="Отмена", command=edit_window.destroy)
        cancel_button.pack(side='right', padx=5)
        customer_id_entry.focus()
    def show_add_supply_window(connection, refresh_callback):
        add_window = tk.Toplevel()
        add_window.title("Добавить поступление")
        add_window.geometry("900x700")
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10), padding=5)
        style.configure("TEntry", font=('Arial', 10), padding=5)
        style.configure("Treeview", font=('Arial', 10), rowheight=25)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        main_frame = ttk.Frame(add_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        supply_frame = ttk.LabelFrame(main_frame, text="Информация о поступлении", padding=10)
        supply_frame.pack(fill='x', pady=5)
        ttk.Label(supply_frame, text="Номер накладной:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        invoice_entry = ttk.Entry(supply_frame)
        invoice_entry.grid(row=0, column=1, sticky='we', padx=5, pady=5)
        ttk.Label(supply_frame, text="Дата и время:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        date_entry = ttk.Entry(supply_frame)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        date_entry.grid(row=1, column=1, sticky='we', padx=5, pady=5)
        details_frame = ttk.LabelFrame(main_frame, text="Детали поступления", padding=10)
        details_frame.pack(fill='both', expand=True, pady=5)
        columns = ("ID товара", "Количество", "Закупочная цена")
        products_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=5)
        for col in columns:
            products_tree.heading(col, text=col)
            products_tree.column(col, width=120, anchor='center')
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=products_tree.yview)
        products_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        products_tree.pack(fill='both', expand=True, pady=5)
        add_product_frame = ttk.Frame(details_frame)
        add_product_frame.pack(fill='x', pady=5)
        ttk.Label(add_product_frame, text="ID товара:").pack(side='left', padx=5)
        product_id_entry = ttk.Entry(add_product_frame, width=12)
        product_id_entry.pack(side='left', padx=5)
        ttk.Label(add_product_frame, text="Количество:").pack(side='left', padx=5)
        qty_entry = ttk.Entry(add_product_frame, width=12)
        qty_entry.pack(side='left', padx=5)
        ttk.Label(add_product_frame, text="Цена:").pack(side='left', padx=5)
        price_entry = ttk.Entry(add_product_frame, width=12)
        price_entry.pack(side='left', padx=5)
        def add_product():
            product_id = product_id_entry.get()
            qty = qty_entry.get()
            price = price_entry.get()
            if not all([product_id, qty, price]):
                messagebox.showerror("Ошибка", "Заполните все поля товара")
                return
            try:
                qty = int(qty)
                price = float(price)
                if qty <= 0 or price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Количество и цена должны быть положительными числами")
                return
            products_tree.insert("", "end", values=(product_id, qty, price))
            product_id_entry.delete(0, 'end')
            qty_entry.delete(0, 'end')
            price_entry.delete(0, 'end')
            product_id_entry.focus()
        add_button = ttk.Button(add_product_frame, text="Добавить товар", command=add_product)
        add_button.pack(side='left', padx=10)
        def remove_product():
            selected_item = products_tree.selection()
            if selected_item:
                products_tree.delete(selected_item)
        remove_button = ttk.Button(add_product_frame, text="Удалить товар", command=remove_product)
        remove_button.pack(side='left', padx=5)
        def save_supply():
            cursor = None
            try:
                cursor = connection.cursor()
                invoice_number = invoice_entry.get()
                date_time = date_entry.get()
                if not invoice_number:
                    messagebox.showerror("Ошибка", "Введите номер накладной")
                    return
                try:
                    datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    messagebox.showerror("Ошибка", "Неправильный формат даты. Используйте YYYY-MM-DD HH:MM:SS")
                    return
                if not products_tree.get_children():
                    messagebox.showerror("Ошибка", "Добавьте хотя бы один товар")
                    return
                if connection.in_transaction:
                    connection.rollback()
                connection.start_transaction()
                # 1. Добавляем запись в SUPPLY
                cursor.execute("""
                               INSERT INTO SUPPLY (DateTime, Invoice_Number)
                               VALUES (%s, %s)
                               """, (date_time, invoice_number))
                supply_id = cursor.lastrowid
                # 2. Добавляем детали поступления
                for item in products_tree.get_children():
                    product_id, qty, price = products_tree.item(item)['values']
                    cursor.execute("""
                                   INSERT INTO SUPPLY_DETAIL (Supply_ID, Product_ID, Qty, Purchase_Price)
                                   VALUES (%s, %s, %s, %s)
                                   """, (supply_id, product_id, qty, price))
                # Фиксируем изменения
                connection.commit()
                messagebox.showinfo("Успех", "Поступление успешно добавлено")
                add_window.destroy()
                refresh_callback()
            except Exception as e:
                if connection.in_transaction:
                    connection.rollback()
                messagebox.showerror("Ошибка", f"Ошибка при добавлении поступления:\n{str(e)}")
            finally:
                if cursor:
                    cursor.close()
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=10)
        save_button = ttk.Button(buttons_frame, text="Сохранить поступление", command=save_supply)
        save_button.pack(side='right', padx=5)
        cancel_button = ttk.Button(buttons_frame, text="Отмена", command=add_window.destroy)
        cancel_button.pack(side='right', padx=5)
        invoice_entry.focus()
    def show_edit_supply_window(connection, refresh_callback, supply_id):
        edit_window = tk.Toplevel()
        edit_window.title("Редактировать поступление")
        edit_window.geometry("900x700")
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10), padding=5)
        style.configure("TEntry", font=('Arial', 10), padding=5)
        style.configure("Treeview", font=('Arial', 10), rowheight=25)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        main_frame = ttk.Frame(edit_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        supply_frame = ttk.LabelFrame(main_frame, text="Информация о поступлении", padding=10)
        supply_frame.pack(fill='x', pady=5)
        ttk.Label(supply_frame, text="Номер накладной:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        invoice_entry = ttk.Entry(supply_frame)
        invoice_entry.grid(row=0, column=1, sticky='we', padx=5, pady=5)
        ttk.Label(supply_frame, text="Дата и время:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        date_entry = ttk.Entry(supply_frame)
        date_entry.grid(row=1, column=1, sticky='we', padx=5, pady=5)
        try:
            cursor = connection.cursor()
            # Получаем информацию о поступлении
            cursor.execute("SELECT DateTime, Invoice_Number FROM SUPPLY WHERE ID = %s", (supply_id,))
            supply_data = cursor.fetchone()
            if supply_data:
                date_entry.insert(0, supply_data[0].strftime("%Y-%m-%d %H:%M:%S"))
                invoice_entry.insert(0, supply_data[1])
            # Получаем текущие детали поступления
            cursor.execute("SELECT Product_ID, Qty, Purchase_Price FROM SUPPLY_DETAIL WHERE Supply_ID = %s",
                           (supply_id,))
            current_details = cursor.fetchall()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные поступления:\n{str(e)}")
            edit_window.destroy()
            return
        finally:
            cursor.close()
        details_frame = ttk.LabelFrame(main_frame, text="Детали поступления", padding=10)
        details_frame.pack(fill='both', expand=True, pady=5)
        columns = ("ID товара", "Количество", "Закупочная цена")
        products_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=5)
        for col in columns:
            products_tree.heading(col, text=col)
            products_tree.column(col, width=120, anchor='center')
        for detail in current_details:
            products_tree.insert("", "end", values=detail)
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=products_tree.yview)
        products_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        products_tree.pack(fill='both', expand=True, pady=5)
        add_product_frame = ttk.Frame(details_frame)
        add_product_frame.pack(fill='x', pady=5)
        ttk.Label(add_product_frame, text="ID товара:").pack(side='left', padx=5)
        product_id_entry = ttk.Entry(add_product_frame, width=12)
        product_id_entry.pack(side='left', padx=5)
        ttk.Label(add_product_frame, text="Количество:").pack(side='left', padx=5)
        qty_entry = ttk.Entry(add_product_frame, width=12)
        qty_entry.pack(side='left', padx=5)
        ttk.Label(add_product_frame, text="Цена:").pack(side='left', padx=5)
        price_entry = ttk.Entry(add_product_frame, width=12)
        price_entry.pack(side='left', padx=5)
        def add_product():
            product_id = product_id_entry.get()
            qty = qty_entry.get()
            price = price_entry.get()
            if not all([product_id, qty, price]):
                messagebox.showerror("Ошибка", "Заполните все поля товара")
                return
            products_tree.insert("", "end", values=(product_id, qty, price))
            product_id_entry.delete(0, 'end')
            qty_entry.delete(0, 'end')
            price_entry.delete(0, 'end')
            product_id_entry.focus()
        add_button = ttk.Button(add_product_frame, text="Добавить товар", command=add_product)
        add_button.pack(side='left', padx=10)
        def remove_product():
            selected_item = products_tree.selection()
            if selected_item:
                products_tree.delete(selected_item)
        remove_button = ttk.Button(add_product_frame, text="Удалить товар", command=remove_product)
        remove_button.pack(side='left', padx=5)
        def save_supply():
            cursor = None
            try:
                cursor = connection.cursor()
                invoice_number = invoice_entry.get()
                date_time = date_entry.get()
                if not invoice_number:
                    messagebox.showerror("Ошибка", "Введите номер накладной")
                    return
                try:
                    datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    messagebox.showerror("Ошибка", "Неправильный формат даты. Используйте YYYY-MM-DD HH:MM:SS")
                    return
                if not products_tree.get_children():
                    messagebox.showerror("Ошибка", "Добавьте хотя бы один товар")
                    return
                if connection.in_transaction:
                    connection.rollback()
                connection.start_transaction()
                # 1. Обновляем основную информацию о поступлении
                cursor.execute("""
                               UPDATE SUPPLY
                               SET DateTime       = %s,
                                   Invoice_Number = %s
                               WHERE ID = %s
                               """, (date_time, invoice_number, supply_id))
                # 2. Удаляем все текущие детали поступления
                cursor.execute("""
                               DELETE
                               FROM SUPPLY_DETAIL
                               WHERE Supply_ID = %s
                               """, (supply_id,))
                # 3. Добавляем новые детали поступления
                for item in products_tree.get_children():
                    product_id, qty, price = products_tree.item(item)['values']
                    cursor.execute("""
                                   INSERT INTO SUPPLY_DETAIL (Supply_ID, Product_ID, Qty, Purchase_Price)
                                   VALUES (%s, %s, %s, %s)
                                   """, (supply_id, product_id, qty, price))
                # Фиксируем изменения
                connection.commit()
                messagebox.showinfo("Успех", "Поступление успешно обновлено")
                edit_window.destroy()
                refresh_callback()
            except Exception as e:
                if connection.in_transaction:
                    connection.rollback()
                messagebox.showerror("Ошибка", f"Ошибка при обновлении поступления:\n{str(e)}")
            finally:
                if cursor:
                    cursor.close()
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=10)
        save_button = ttk.Button(buttons_frame, text="Сохранить изменения", command=save_supply)
        save_button.pack(side='right', padx=5)
        cancel_button = ttk.Button(buttons_frame, text="Отмена", command=edit_window.destroy)
        cancel_button.pack(side='right', padx=5)
        invoice_entry.focus()

    def show_transaction_details(connection, transaction_id, parent_window=None):
        """Отображает детали транзакции в отдельном окне"""
        try:
            cursor = connection.cursor(dictionary=True)
            # Получаем основную информацию о транзакции
            cursor.execute("""
                           SELECT t.ID,
                                  t.Total_Cost,
                                  c.ID as customer_id,
                                  c.Last_Name,
                                  c.First_Name,
                                  c.Middle_Name,
                                  c.Organization,
                                  c.Email
                           FROM transaction t
                                    JOIN customer c ON t.Customer_ID = c.ID
                           WHERE t.ID = %s
                           """, (transaction_id,))
            transaction_info = cursor.fetchone()
            if not transaction_info:
                messagebox.showerror("Ошибка", "Транзакция не найдена", parent=parent_window)
                return
            # Пытаемся получить информацию о скидке (если есть доступ)
            discount_info = None
            try:
                cursor.execute("""
                               SELECT d.Discount_Percent
                               FROM transaction t
                                        LEFT JOIN discount d ON t.Discount_ID = d.ID
                               WHERE t.ID = %s
                               """, (transaction_id,))
                discount_info = cursor.fetchone()
            except Exception:
                pass  # Просто игнорируем, если нет доступа
            # Получаем историю статусов
            cursor.execute("""
                           SELECT s.Name as Status_Name, td.DateTime
                           FROM transaction_date td
                                    JOIN status s ON td.Status_ID = s.ID
                           WHERE td.Transaction_ID = %s
                           ORDER BY td.DateTime
                           """, (transaction_id,))
            status_history = cursor.fetchall()
            # Пытаемся получить телефоны покупателя (если есть доступ)
            phones = None
            try:
                cursor.execute("""
                               SELECT Phone
                               FROM customer_phone
                               WHERE Customer_ID = %s
                               """, (transaction_info['customer_id'],))
                phones = [phone['Phone'] for phone in cursor.fetchall()]
            except Exception:
                pass  # Просто игнорируем, если нет доступа
            # Получаем детали транзакции (товары)
            cursor.execute("""
                           SELECT td.Product_ID,
                                  p.Name     as Product_Name,
                                  cat.Name   as Category_Name,
                                  td.Qty,
                                  td.Price,
                                  pc.Cell_ID as cell_id
                           FROM transaction_details td
                                    JOIN product p ON td.Product_ID = p.ID
                                    JOIN category cat ON p.Category_ID = cat.ID
                                    LEFT JOIN product_cell pc ON td.Product_ID = pc.Product_ID
                           WHERE td.Transaction_id = %s
                           """, (transaction_id,))
            product_details = cursor.fetchall()
            cursor.close()
            info_window = tk.Toplevel(parent_window)
            info_window.title(f"Транзакция ID: {transaction_id}")
            info_window.geometry("1200x800")
            notebook = ttk.Notebook(info_window)
            notebook.pack(fill='both', expand=True)
            main_frame = ttk.Frame(notebook, padding=10)
            notebook.add(main_frame, text="Основная информация")
            ttk.Label(main_frame, text=f"Транзакция ID: {transaction_id}",
                      font=('Arial', 12, 'bold')).pack(anchor='w', pady=5)
            info_frame = ttk.Frame(main_frame)
            info_frame.pack(fill='x', padx=10, pady=10)
            def add_info_row(parent, label, value):
                row = ttk.Frame(parent)
                row.pack(fill='x', pady=2)
                ttk.Label(row, text=label + ":", width=20, anchor='w').pack(side='left')
                ttk.Label(row, text=str(value) if value is not None else "не указано").pack(side='left')
            total_cost = float(transaction_info['Total_Cost'])
            add_info_row(info_frame, "Общая сумма", f"{total_cost:.2f} руб.")
            if discount_info is not None and discount_info.get('Discount_Percent'):
                discount_percent = float(discount_info['Discount_Percent'])
                total_without_discount = total_cost / (1 - discount_percent / 100)
                discount_amount = total_without_discount - total_cost
                add_info_row(info_frame, "Сумма без скидки", f"{total_without_discount:.2f} руб.")
                add_info_row(info_frame, "Скидка", f"{discount_percent}% (-{discount_amount:.2f} руб.)")
            ttk.Label(main_frame, text="История статусов:",
                      font=('Arial', 10, 'bold')).pack(anchor='w', pady=10)
            status_frame = ttk.Frame(main_frame)
            status_frame.pack(fill='x', padx=10, pady=5)
            status_tree = ttk.Treeview(status_frame, columns=("Дата", "Статус"), show="headings", height=5)
            status_tree.heading("Дата", text="Дата изменения")
            status_tree.heading("Статус", text="Статус")
            status_tree.column("Дата", width=200, anchor='center')
            status_tree.column("Статус", width=300, anchor='center')
            for status in status_history:
                status_tree.insert("", "end", values=(
                    status['DateTime'].strftime('%Y-%m-%d %H:%M:%S'),
                    status['Status_Name']
                ))
            if status_history:
                status_tree.selection_set(status_tree.get_children()[-1])
                status_tree.focus(status_tree.get_children()[-1])
            status_scroll = ttk.Scrollbar(status_frame, orient="vertical", command=status_tree.yview)
            status_tree.configure(yscrollcommand=status_scroll.set)
            status_tree.pack(side='left', fill='both', expand=True)
            status_scroll.pack(side='right', fill='y')
            ttk.Label(main_frame, text="Товары в транзакции:",
                      font=('Arial', 10, 'bold')).pack(anchor='w', pady=10)
            columns = ("ID", "Название", "Категория", "Кол-во", "Цена", "Сумма", "Ячейка")
            tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=8)
            col_widths = [50, 200, 150, 80, 100, 120, 150]
            for col, width in zip(columns, col_widths):
                tree.heading(col, text=col)
                tree.column(col, width=width, anchor='center')
            total_sum = 0
            for product in product_details:
                price = float(product['Price'])
                qty = float(product['Qty'])
                total = price * qty
                total_sum += total
                tree.insert("", "end", values=(
                    product['Product_ID'],
                    product['Product_Name'],
                    product['Category_Name'],
                    product['Qty'],
                    f"{price:.2f} руб.",
                    f"{total:.2f} руб.",
                    product['cell_id'] if product['cell_id'] else "Не указана"
                ))
            tree.insert("", "end", values=("ИТОГО:", "", "", "", "", f"{total_sum:.2f} руб.", ""), tags=('total',))
            tree.tag_configure('total', background='#f0f0f0', font=('Arial', 10, 'bold'))
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(fill='both', expand=True, padx=10, pady=5)
            scrollbar.pack(side='right', fill='y')
            customer_frame = ttk.Frame(notebook, padding=10)
            notebook.add(customer_frame, text="Покупатель")
            ttk.Label(customer_frame, text="Информация о покупателе:",
                      font=('Arial', 12, 'bold')).pack(anchor='w', pady=5)
            customer_info_frame = ttk.Frame(customer_frame)
            customer_info_frame.pack(fill='x', padx=10, pady=10)
            add_info_row(customer_info_frame, "ID покупателя", transaction_info['customer_id'])
            add_info_row(customer_info_frame, "ФИО",
                         f"{transaction_info['Last_Name']} {transaction_info['First_Name']} {transaction_info['Middle_Name'] or ''}")
            add_info_row(customer_info_frame, "Организация", transaction_info['Organization'])
            add_info_row(customer_info_frame, "Email", transaction_info['Email'])
            # Добавляем телефоны только если они есть и есть доступ
            if phones is not None:
                add_info_row(customer_info_frame, "Телефоны", ", ".join(phones) if phones else "не указаны")
        except Exception as e:
            error_handler(f"Ошибка при получении данных о транзакции: {str(e)}", parent=parent_window)
            traceback.print_exc()
    def show_transaction_report_window(connection, load_table_data=None):
        """Окно для генерации отчета по транзакциям"""
        report_window = tk.Toplevel()
        report_window.title("Генерация отчета по транзакциям")
        report_window.geometry("400x400")
        report_window.resizable(False, False)
        input_frame = ttk.Frame(report_window, padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(input_frame, text="Тип отчета:").grid(row=0, column=0, sticky=tk.W, pady=5)
        report_type = tk.StringVar(value="user")
        def toggle_report_type():
            if report_type.get() == "user":
                user_id_entry.config(state=tk.NORMAL)
                org_entry.config(state=tk.DISABLED)
            else:
                user_id_entry.config(state=tk.DISABLED)
                org_entry.config(state=tk.NORMAL)
        ttk.Radiobutton(input_frame, text="По пользователю", variable=report_type, value="user",
                        command=toggle_report_type).grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(input_frame, text="По организации", variable=report_type, value="org",
                        command=toggle_report_type).grid(row=2, column=0, sticky=tk.W)
        ttk.Label(input_frame, text="ID пользователя:").grid(row=3, column=0, sticky=tk.W, pady=5)
        user_id_entry = ttk.Entry(input_frame)
        user_id_entry.grid(row=3, column=1, sticky=tk.EW, pady=5)
        ttk.Label(input_frame, text="Название организации:").grid(row=4, column=0, sticky=tk.W, pady=5)
        org_entry = ttk.Entry(input_frame, state=tk.DISABLED)
        org_entry.grid(row=4, column=1, sticky=tk.EW, pady=5)
        ttk.Label(input_frame, text="Период:").grid(row=5, column=0, sticky=tk.W, pady=5)
        period_frame = ttk.Frame(input_frame)
        period_frame.grid(row=5, column=1, sticky=tk.EW, pady=5)
        ttk.Label(period_frame, text="с:").pack(side=tk.LEFT)
        start_date_entry = ttk.Entry(period_frame, width=10)
        start_date_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(period_frame, text="по:").pack(side=tk.LEFT)
        end_date_entry = ttk.Entry(period_frame, width=10)
        end_date_entry.pack(side=tk.LEFT, padx=5)
        button_frame = ttk.Frame(report_window, padding="10")
        button_frame.pack(fill=tk.X)
        def generate_report():
            try:
                report_gen = TransactionReportGenerator()
                user_id = None
                organization = None
                if report_type.get() == "user":
                    user_id = int(user_id_entry.get()) if user_id_entry.get() else None
                else:
                    organization = org_entry.get() if org_entry.get() else None
                start_date = start_date_entry.get() or None
                end_date = end_date_entry.get() or None
                report_gen.generate_report(
                    user_id=user_id,
                    organization=organization,
                    start_date=start_date,
                    end_date=end_date,
                    parent_window=report_window
                )
                if load_table_data:
                    load_table_data()
            except ValueError:
                messagebox.showerror("Ошибка", "ID пользователя должен быть числом")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при генерации отчета: {str(e)}")
        cancel_button = ttk.Button(button_frame, text="Отмена", command=report_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        generate_button = ttk.Button(button_frame, text="Сформировать", command=generate_report)
        generate_button.pack(side=tk.RIGHT, padx=5)
        toggle_report_type()
        report_window.update_idletasks()
        width = report_window.winfo_width()
        height = report_window.winfo_height()
        x = (report_window.winfo_screenwidth() // 2) - (width // 2)
        y = (report_window.winfo_screenheight() // 2) - (height // 2)
        report_window.geometry(f'+{x}+{y}')
    def show_print_receipt_window(connection, callback=None):
        """Окно для печати чека по транзакции (фиксированного размера)"""
        receipt_window = tk.Toplevel()
        receipt_window.title("Печать чека")
        receipt_window.geometry("300x200")
        receipt_window.resizable(False, False)
        input_frame = ttk.Frame(receipt_window, padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(input_frame, text="ID транзакции:").grid(row=0, column=0, sticky=tk.W, pady=5)
        transaction_id_entry = ttk.Entry(input_frame)
        transaction_id_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        button_frame = ttk.Frame(receipt_window, padding="10")
        button_frame.pack(fill=tk.X)
        def print_receipt():
            try:
                transaction_id = int(transaction_id_entry.get())
                # Проверяем существование транзакции
                cursor = connection.cursor()
                cursor.execute("SELECT ID FROM transaction WHERE ID = %s", (transaction_id,))
                if not cursor.fetchone():
                    messagebox.showerror("Ошибка", f"Транзакция с ID {transaction_id} не найдена")
                    return
                # Генерируем чек
                receipt_gen.generate_receipt(transaction_id, parent_window=receipt_window)
                if callback:
                    callback()
            except ValueError:
                messagebox.showerror("Ошибка", "ID транзакции должен быть числом")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при печати чека: {str(e)}")
        cancel_button = ttk.Button(button_frame, text="Отмена", command=receipt_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        print_button = ttk.Button(button_frame, text="Печать", command=print_receipt)
        print_button.pack(side=tk.RIGHT, padx=5)
        receipt_window.update_idletasks()
        width = receipt_window.winfo_width()
        height = receipt_window.winfo_height()
        x = (receipt_window.winfo_screenwidth() // 2) - (width // 2)
        y = (receipt_window.winfo_screenheight() // 2) - (height // 2)
        receipt_window.geometry(f'+{x}+{y}')
    def load_table_data(event=None):
        nonlocal current_columns, current_table, current_sort_column, current_sort_order
        if event and event.type == tk.EventType.VirtualEvent:
            current_sort_column = None
            current_sort_order = None
            search_entry.delete(0, tk.END)
        selected_table = table_combobox.get()
        if not selected_table:
            return
        try:
            try:
                limit = int(limit_combobox.get())
            except ValueError:
                limit = 100
            if not check_permission(selected_table, 'view'):
                error_handler(f"У вас нет прав на просмотр таблицы {selected_table}")
                return
            # Очищаем предыдущие данные
            tree.delete(*tree.get_children())
            query = f"SELECT * FROM {selected_table}"
            # Добавляем сортировку, если есть
            if current_sort_column and current_sort_order:
                query += f" ORDER BY {current_sort_column} {current_sort_order.upper()}"
            # Добавляем лимит
            query += f" LIMIT {limit}"
            # Получаем данные из базы данных
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            # Получаем названия столбцов
            current_columns = [desc[0] for desc in cursor.description]
            current_table = selected_table
            cursor.close()
            # Обновляем выпадающий список столбцов для поиска
            column_combobox['values'] = current_columns
            if current_columns:
                column_combobox.current(0)
            tree['columns'] = current_columns
            tree.heading('#0', text='')
            tree.column('#0', width=0, stretch=False)
            for col in current_columns:
                tree.heading(col, text=col, anchor='center',
                             command=lambda c=col: sort_data(c))
                # Подсвечиваем текущий столбец сортировки
                if col == current_sort_column:
                    if current_sort_order == 'asc':
                        tree.heading(col, text=f"{col} ▲")
                    elif current_sort_order == 'desc':
                        tree.heading(col, text=f"{col} ▼")
                tree.column(col, width=100, stretch=True, anchor='center')  # Центрируем данные
            for i, row in enumerate(rows):
                tree.insert('', 'end', text=str(i + 1), values=row)
            # Обновляем кнопки управления в соответствии с правами
            update_control_buttons()
        except Exception as e:
            error_handler(f"Ошибка при загрузке таблицы {selected_table}: {str(e)}")
    def search_data():
        """Функция для поиска данных"""
        search_text = search_entry.get()
        selected_column = column_combobox.get()
        if not search_text or not current_table or not current_columns or not selected_column:
            return
        try:
            try:
                limit = int(limit_combobox.get())
            except ValueError:
                limit = 100
            # Формируем базовый запрос
            if search_type.get() == "partial":
                query = f"SELECT * FROM {current_table} WHERE {selected_column} LIKE %s"
                params = (f"%{search_text}%",)
            else:
                query = f"SELECT * FROM {current_table} WHERE {selected_column} = %s"
                params = (search_text,)
            # Добавляем сортировку, если есть
            if current_sort_column and current_sort_order:
                query += f" ORDER BY {current_sort_column} {current_sort_order.upper()}"
            # Добавляем лимит
            query += f" LIMIT {limit}"
            cursor = connection.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            tree.delete(*tree.get_children())
            for i, row in enumerate(rows):
                tree.insert('', 'end', text=str(i + 1), values=row)
        except Exception as e:
            error_handler(f"Ошибка при поиске: {str(e)}")
    table_combobox.bind('<<ComboboxSelected>>', load_table_data)
    limit_combobox.bind('<<ComboboxSelected>>', load_table_data)
    limit_combobox.bind('<Return>', load_table_data)
    if available_tables:
        load_table_data()
if __name__ == "__main__":
    run_login_window()