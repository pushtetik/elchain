import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

def generate_period_report(connection):
    try:
        period_window = tk.Toplevel()
        period_window.title("Выберите параметры отчета")
        period_window.geometry("400x550")
        date_frame = ttk.Frame(period_window)
        date_frame.pack(pady=10)
        report_type_frame = ttk.LabelFrame(period_window, text="Тип отчета")
        report_type_frame.pack(pady=10, padx=10, fill='x')
        report_type = tk.StringVar(value="all")  # По умолчанию "Все"
        ttk.Radiobutton(report_type_frame, text="Все данные", variable=report_type, value="all").pack(anchor='w',
                                                                                                      padx=5, pady=2)
        ttk.Radiobutton(report_type_frame, text="Только транзакции", variable=report_type,
                        value="transactions").pack(anchor='w', padx=5, pady=2)
        ttk.Radiobutton(report_type_frame, text="Только поступления", variable=report_type, value="supplies").pack(
            anchor='w', padx=5, pady=2)
        filter_type_frame = ttk.LabelFrame(period_window, text="Фильтровать по")
        filter_type_frame.pack(pady=10, padx=10, fill='x')
        filter_type = tk.StringVar(value="cells")  # По умолчанию "По ячейкам"
        ttk.Radiobutton(filter_type_frame, text="По ячейкам", variable=filter_type, value="cells",
                        command=lambda: toggle_filter_controls("cells")).pack(anchor='w', padx=5, pady=2)
        ttk.Radiobutton(filter_type_frame, text="По товарам", variable=filter_type, value="products",
                        command=lambda: toggle_filter_controls("products")).pack(anchor='w', padx=5, pady=2)
        start_label = ttk.Label(date_frame, text="Начальная дата (ДД.ММ.ГГГГ):")
        start_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')
        start_date_entry = ttk.Entry(date_frame, width=15)
        start_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        now = datetime.now()
        start_of_month = now.replace(day=1).strftime("%d.%m.%Y")
        start_date_entry.insert(0, start_of_month)
        end_label = ttk.Label(date_frame, text="Конечная дата (ДД.ММ.ГГГГ):")
        end_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        end_date_entry = ttk.Entry(date_frame, width=15)
        end_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        end_date_entry.insert(0, now.strftime("%d.%m.%Y"))
        warehouse_label = ttk.Label(date_frame, text="ID ячейки (оставить пустым для всех):")
        warehouse_label.grid(row=2, column=0, padx=5, pady=5, sticky='e')
        warehouse_entry = ttk.Entry(date_frame, width=15)
        warehouse_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        product_label = ttk.Label(date_frame, text="ID товара (оставить пустым для всех):")
        product_entry = ttk.Entry(date_frame, width=15)
        def toggle_filter_controls(filter_type):
            if filter_type == "cells":
                # Показываем ячейки, скрываем товары
                warehouse_label.grid()
                warehouse_entry.grid()
                product_label.grid_remove()
                product_entry.grid_remove()
            else:
                # Показываем товары, скрываем ячейки
                product_label.grid(row=2, column=0, padx=5, pady=5, sticky='e')
                product_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
                warehouse_label.grid_remove()
                warehouse_entry.grid_remove()
        # Инициализация - показываем только ячейки
        toggle_filter_controls("cells")
        def register_fonts():
            fonts_folder = "Shrifts"
            if not os.path.exists(fonts_folder):
                messagebox.showwarning("Предупреждение", f"Папка со шрифтами '{fonts_folder}' не найдена!")
                return False
            for font_file in os.listdir(fonts_folder):
                if font_file.endswith('.ttf'):
                    font_name = os.path.splitext(font_file)[0]
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, os.path.join(fonts_folder, font_file)))
                    except:
                        messagebox.showwarning("Предупреждение", f"Не удалось зарегистрировать шрифт {font_file}")
            return True
        def generate_pdf_report(report_content, start_date, end_date, selected_filter, report_type_name,
                                filter_type_name):
            if not register_fonts():
                return False
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Сохранить отчет как",
                initialfile=f"report_{start_date}_to_{end_date}.pdf"
            )
            if not file_path:
                return False
            styles = getSampleStyleSheet()
            styles['Normal'].fontSize = 10
            styles['Heading1'].fontSize = 14
            styles['Heading1'].alignment = 1
            styles['Heading2'].fontSize = 12
            styles['Heading2'].alignment = 0
            styles.add(ParagraphStyle(name='Right', parent=styles['Normal'], alignment=2))
            styles.add(ParagraphStyle(name='Center', parent=styles['Normal'], alignment=1))
            available_fonts = pdfmetrics.getRegisteredFontNames()
            if 'DejaVuSerif' in available_fonts:
                base_font = 'DejaVuSerif'
            elif available_fonts:
                base_font = available_fonts[0]
            else:
                base_font = 'Helvetica'
            styles['Normal'].fontName = base_font
            styles['Heading1'].fontName = base_font + '-Bold' if f'{base_font}-Bold' in available_fonts else base_font
            styles['Heading2'].fontName = base_font + '-Bold' if f'{base_font}-Bold' in available_fonts else base_font
            doc = SimpleDocTemplate(
                file_path,
                pagesize=A4,
                title=f'Отчет с {start_date} по {end_date}',
                author='Система учета',
                leftMargin=15 * mm,
                rightMargin=15 * mm,
                topMargin=10 * mm,
                bottomMargin=10 * mm
            )
            story = []
            story.append(Paragraph(f"ОТЧЕТ", styles['Heading1']))
            story.append(Spacer(1, 5 * mm))
            # Добавляем содержимое отчета
            current_section = None
            for line in report_content:
                if line.startswith('=' * 50):
                    section_name = line.strip('= ')
                    if section_name:
                        story.append(Spacer(1, 5 * mm))
                        story.append(Paragraph(section_name, styles['Heading2']))
                        story.append(Spacer(1, 3 * mm))
                elif line.startswith('ИТОГО') or line.startswith('Общее количество') or line.startswith('Общая сумма'):
                    story.append(Paragraph(line, ParagraphStyle(
                        name='TotalLine',
                        parent=styles['Normal'],
                        fontSize=11,
                        fontName=base_font + '-Bold' if f'{base_font}-Bold' in available_fonts else base_font
                    )))
                elif line.strip() and not line.startswith(('-', '_')):
                    story.append(Paragraph(line, styles['Normal']))
                elif line.startswith(('-', '_')):
                    story.append(Spacer(1, 3 * mm))
                    story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 3 * mm))
                else:
                    story.append(Spacer(1, 3 * mm))
            try:
                doc.build(story)
                messagebox.showinfo("Успех", f"Отчет успешно сохранен:\n{file_path}")
                return True
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать PDF:\n{str(e)}")
                return False
        def generate_report():
            try:
                start_date_str = start_date_entry.get()
                end_date_str = end_date_entry.get()
                selected_report_type = report_type.get()
                selected_filter_type = filter_type.get()
                try:
                    start_date_dt = datetime.strptime(start_date_str, "%d.%m.%Y")
                    end_date_dt = datetime.strptime(end_date_str, "%d.%m.%Y")
                    start_date = datetime.strptime(start_date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
                    end_date = datetime.strptime(end_date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Ошибка", "Неправильный формат даты. Используйте ДД.ММ.ГГГГ")
                    return
                if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(end_date, "%Y-%m-%d"):
                    messagebox.showerror("Ошибка", "Начальная дата не может быть позже конечной")
                    return
                delta = end_date_dt - start_date_dt
                if delta.days > 32:
                    messagebox.showerror("Ошибка", "Максимальный период для отчета - месяц (31 день)")
                    return
                report_type_name = {
                    'all': 'Все данные',
                    'transactions': 'Только транзакции',
                    'supplies': 'Только поступления'
                }.get(selected_report_type, 'Неизвестный тип')
                filter_type_name = {
                    'cells': 'По ячейкам',
                    'products': 'По товарам'
                }.get(selected_filter_type, 'Неизвестный тип')
                cursor = connection.cursor(dictionary=True)
                report_content = []
                # Получаем выбранный фильтр
                if selected_filter_type == "cells":
                    selected_filter = warehouse_entry.get().strip()
                    filter_text = f"Ячейка: {selected_filter if selected_filter else 'Все ячейки'}"
                else:
                    selected_filter = product_entry.get().strip()
                    filter_text = f"Товар: {selected_filter if selected_filter else 'Все товары'}"
                # Добавляем заголовок отчета
                report_content.append(f"{'=' * 50}")
                report_content.append(f"ОТЧЕТ С {start_date} ПО {end_date}")
                report_content.append(filter_text)
                report_content.append(f"Тип отчета: {report_type_name}")
                report_content.append(f"Тип фильтра: {filter_type_name}")
                report_content.append(f"{'=' * 50}\n")
                # Подготовка параметров запроса в зависимости от типа фильтра
                params_transactions = [start_date, end_date]
                params_products = [start_date, end_date]
                params_supplies = [start_date, end_date]
                filter_condition = ""
                if selected_filter_type == "cells":
                    if selected_filter:
                        try:
                            warehouse_id = int(selected_filter)
                            filter_condition = " AND pc.Cell_ID = %s"
                            params_products.append(warehouse_id)
                            params_supplies.append(warehouse_id)
                        except ValueError:
                            messagebox.showerror("Ошибка", "ID ячейки должен быть числом")
                            return
                else:
                    if selected_filter:
                        try:
                            product_id = int(selected_filter)
                            filter_condition = " AND p.ID = %s"
                            params_products.append(product_id)
                            params_supplies.append(product_id)
                        except ValueError:
                            messagebox.showerror("Ошибка", "ID товара должен быть числом")
                            return
                if selected_report_type in ["all", "transactions"]:
                    # запрос для получения Status_ID
                    cursor.execute(f"""
                        SELECT t.ID,
                               td.DateTime AS Date,
                               t.Total_Cost,
                               c.Last_Name,
                               c.First_Name,
                               c.Middle_Name,
                               s.ID AS Status_ID,
                               s.Name AS Status_Name
                        FROM transaction t
                        JOIN (
                            SELECT Transaction_ID, MAX(Status_ID) as MaxStatus
                            FROM transaction_date
                            GROUP BY Transaction_ID
                        ) max_status ON t.ID = max_status.Transaction_ID
                        JOIN transaction_date td ON t.ID = td.Transaction_ID AND td.Status_ID = max_status.MaxStatus
                        JOIN customer c ON t.Customer_ID = c.ID
                        JOIN status s ON td.Status_ID = s.ID
                        WHERE td.DateTime >= %s
                          AND td.DateTime <= %s
                          AND td.Status_ID > 1
                        ORDER BY td.DateTime
                    """, params_transactions[:2])
                    transactions = cursor.fetchall()
                    # Разделение транзакций на обычные и возвраты
                    regular_transactions = [t for t in transactions if t['Status_ID'] != 7]
                    refund_transactions = [t for t in transactions if t['Status_ID'] == 7]
                    # Товары в транзакциях
                    cursor.execute(f"""
                        SELECT DISTINCT td.Transaction_ID,
                               p.ID AS Product_ID,
                               p.Name,
                               td.Qty AS Qty,
                               td.Price,
                               pc.Cell_ID
                        FROM transaction_details td
                        JOIN product p ON td.Product_ID = p.ID
                        LEFT JOIN product_cell pc ON td.Product_ID = pc.Product_ID
                        JOIN transaction t ON td.Transaction_ID = t.ID
                        JOIN transaction_date td2 ON t.ID = td2.Transaction_ID
                        WHERE td2.DateTime >= %s AND td2.DateTime <= %s
                          AND td2.Status_ID > 1
                          {filter_condition}
                        GROUP BY td.Transaction_ID, p.ID, p.Name, td.Price, pc.Cell_ID
                        ORDER BY td.Transaction_ID
                    """, params_products)
                    transaction_products = cursor.fetchall()
                    # Обработка обычных транзакций
                    report_content.append(f"{'=' * 50}")
                    report_content.append("ТРАНЗАКЦИИ:")
                    report_content.append(f"{'=' * 50}\n")
                    total_sold_qty = 0
                    total_transaction_amount = 0
                    for transaction in regular_transactions:
                        related_products = [p for p in transaction_products if
                                            p['Transaction_ID'] == transaction['ID']]
                        if not related_products:
                            continue
                        customer_name = f"{transaction['Last_Name']} {transaction['First_Name']} {transaction['Middle_Name'] or ''}".strip()
                        report_content.append(f"ID: {transaction['ID']} | Дата: {transaction['Date']}")
                        report_content.append(f"Покупатель: {customer_name} | Статус: {transaction['Status_Name']}")
                        report_content.append(f"Сумма сделки: {transaction['Total_Cost']:.2f} руб.")
                        report_content.append(f"Товары:")
                        for prod in related_products:
                            line = f"  - {prod['Name']:30} | Кол-во: {prod['Qty']:4} | Цена: {prod['Price']:7.2f} | Сумма: {prod['Qty'] * prod['Price']:8.2f} руб."
                            if prod['Cell_ID']:
                                line += f" | Ячейка: {prod['Cell_ID']}"
                            report_content.append(line)
                            total_sold_qty += prod['Qty']
                            total_transaction_amount += prod['Qty'] * prod['Price']
                        report_content.append("")
                    report_content.append(f"{'-' * 50}")
                    report_content.append(f"ИТОГО ПО ПРОДАЖАМ:")
                    report_content.append(f"Общее количество товаров продано: {total_sold_qty}")
                    report_content.append(f"Общая сумма продаж по товарам: {total_transaction_amount:.2f} руб.")
                    report_content.append(f"{'-' * 50}\n")
                    # Обработка возвратов
                    report_content.append(f"\n{'=' * 50}")
                    report_content.append("ВОЗВРАТЫ:")
                    report_content.append(f"{'=' * 50}\n")
                    total_refund_qty = 0
                    total_refund_amount = 0
                    for refund in refund_transactions:
                        related_products = [p for p in transaction_products if p['Transaction_ID'] == refund['ID']]
                        if not related_products:
                            continue
                        customer_name = f"{refund['Last_Name']} {refund['First_Name']} {refund['Middle_Name'] or ''}".strip()
                        report_content.append(f"ID: {refund['ID']} | Дата: {refund['Date']}")
                        report_content.append(f"Покупатель: {customer_name} | Статус: {refund['Status_Name']}")
                        report_content.append(f"Сумма возврата: {refund['Total_Cost']:.2f} руб.")
                        report_content.append(f"Товары:")
                        for prod in related_products:
                            line = f"  - {prod['Name']:30} | Кол-во: {prod['Qty']:4} | Цена: {prod['Price']:7.2f} | Сумма: {prod['Qty'] * prod['Price']:8.2f} руб."
                            if prod['Cell_ID']:
                                line += f" | Ячейка: {prod['Cell_ID']}"
                            report_content.append(line)
                            total_refund_qty += prod['Qty']
                            total_refund_amount += prod['Qty'] * prod['Price']
                        report_content.append("")
                    report_content.append(f"{'-' * 50}")
                    report_content.append(f"ИТОГО ПО ВОЗВРАТАМ:")
                    report_content.append(f"Общее количество возвращенных товаров: {total_refund_qty}")
                    report_content.append(f"Общая сумма возвратов: {total_refund_amount:.2f} руб.")
                    report_content.append(f"{'-' * 50}\n")
                # Обработка поставок (если нужно)
                if selected_report_type in ["all", "supplies"]:
                    # Поставки с информацией о товарах/ячейках
                    if selected_filter_type == "cells":
                        cursor.execute(f"""
                            SELECT s.ID, s.DateTime, s.Invoice_Number,
                                   pc.Cell_ID,
                                   SUM(sd.Qty) AS Total_Qty,
                                   SUM(sd.Qty * sd.Purchase_Price) AS Total_Amount
                            FROM supply s
                            JOIN supply_detail sd ON s.ID = sd.Supply_ID
                            JOIN product_cell pc ON sd.Product_ID = pc.Product_ID
                            WHERE s.DateTime >= %s AND s.DateTime <= %s
                              {filter_condition}
                            GROUP BY s.ID, pc.Cell_ID
                            ORDER BY s.DateTime
                        """, params_supplies)
                    else:
                        cursor.execute(f"""
                            SELECT s.ID, s.DateTime, s.Invoice_Number,
                                   SUM(sd.Qty) AS Total_Qty,
                                   SUM(sd.Qty * sd.Purchase_Price) AS Total_Amount
                            FROM supply s
                            JOIN supply_detail sd ON s.ID = sd.Supply_ID
                            JOIN product p ON sd.Product_ID = p.ID
                            WHERE s.DateTime >= %s AND s.DateTime <= %s
                              {filter_condition}
                            GROUP BY s.ID
                            ORDER BY s.DateTime
                        """, params_supplies)
                    supplies = cursor.fetchall()
                    if selected_filter_type == "cells":
                        cursor.execute(f"""
                            SELECT sd.Supply_ID, 
                                   p.ID AS Product_ID, 
                                   p.Name AS Product_Name,
                                   pc.Cell_ID,
                                   sd.Qty, 
                                   sd.Purchase_Price,
                                   (sd.Qty * sd.Purchase_Price) AS Total_Price
                            FROM supply_detail sd
                            JOIN product p ON sd.Product_ID = p.ID
                            JOIN product_cell pc ON sd.Product_ID = pc.Product_ID
                            JOIN supply s ON sd.Supply_ID = s.ID
                            WHERE s.DateTime >= %s AND s.DateTime <= %s
                              {filter_condition}
                            ORDER BY sd.Supply_ID
                        """, params_supplies)
                    else:
                        cursor.execute(f"""
                            SELECT sd.Supply_ID, 
                                   p.ID AS Product_ID, 
                                   p.Name AS Product_Name,
                                   sd.Qty, 
                                   sd.Purchase_Price,
                                   (sd.Qty * sd.Purchase_Price) AS Total_Price
                            FROM supply_detail sd
                            JOIN product p ON sd.Product_ID = p.ID
                            JOIN supply s ON sd.Supply_ID = s.ID
                            WHERE s.DateTime >= %s AND s.DateTime <= %s
                              {filter_condition}
                            ORDER BY sd.Supply_ID
                        """, params_supplies)
                    supply_details = cursor.fetchall()
                    # Поставки
                    report_content.append(f"{'=' * 50}")
                    report_content.append("ПОСТУПЛЕНИЯ:")
                    report_content.append(f"{'=' * 50}\n")

                    total_supply_qty = 0
                    total_supply_amount = 0

                    for supply in supplies:
                        related_details = [d for d in supply_details if d['Supply_ID'] == supply['ID']]
                        if not related_details:
                            continue
                        report_content.append(f"ID: {supply['ID']}")
                        report_content.append(f"Дата: {supply['DateTime']}")
                        report_content.append(f"Накладная: {supply['Invoice_Number']}")
                        if selected_filter_type == "cells":
                            report_content.append(f"Ячейка: {supply['Cell_ID']}")
                        report_content.append("Товары:")
                        for detail in related_details:
                            line = f"  - {detail['Product_Name']:30} | Кол-во: {detail['Qty']:4} | Цена: {detail['Purchase_Price']:7.2f} | Сумма: {detail['Total_Price']:8.2f} руб."
                            if selected_filter_type == "cells":
                                line += f" | Ячейка: {detail['Cell_ID']}"
                            report_content.append(line)
                            total_supply_qty += detail['Qty']
                            total_supply_amount += detail['Total_Price']
                        report_content.append("")
                    report_content.append(f"{'-' * 50}")
                    report_content.append(f"ИТОГО ПО ПОСТУПЛЕНИЯМ:")
                    report_content.append(f"Общее количество товаров: {total_supply_qty}")
                    report_content.append(f"Общая сумма поступлений: {total_supply_amount:.2f} руб.")
                    report_content.append(f"{'-' * 50}\n")
                # Итоги (только если выбран полный отчет)
                if selected_report_type == "all":
                    report_content.append(f"{'=' * 50}")
                    report_content.append(f"ИТОГО:")
                    if 'total_transaction_amount' in locals():
                        report_content.append(f"Выручка: {total_transaction_amount:.2f} руб.")
                    if 'total_supply_amount' in locals():
                        report_content.append(f"Закупка: {total_supply_amount:.2f} руб.")
                    if 'total_refund_amount' in locals():
                        report_content.append(f"Затраты на возвраты: {total_refund_amount:.2f} руб.")
                    if 'total_transaction_amount' in locals() and 'total_supply_amount' in locals() and 'total_refund_amount' in locals():
                        profit = total_transaction_amount - (total_supply_amount + total_refund_amount)
                        report_content.append(f"Прибыль: {profit:.2f} руб.")
                    report_content.append(f"{'=' * 50}")
                # Предлагаем выбор: просмотреть или сохранить в PDF
                choice_window = tk.Toplevel()
                choice_window.title("Выберите действие")
                choice_window.geometry("300x150")
                def view_report():
                    report_window = tk.Toplevel()
                    report_window.title(f"Отчет с {start_date} по {end_date}")
                    report_window.geometry("1200x800")
                    text_frame = ttk.Frame(report_window)
                    text_frame.pack(fill='both', expand=True, padx=10, pady=10)
                    scrollbar = ttk.Scrollbar(text_frame)
                    scrollbar.pack(side='right', fill='y')
                    report_text = tk.Text(
                        text_frame,
                        wrap='word',
                        font=('Courier New', 11),
                        yscrollcommand=scrollbar.set,
                        relief='flat'
                    )
                    report_text.pack(fill='both', expand=True)
                    scrollbar.config(command=report_text.yview)
                    report_text.insert('1.0', '\n'.join(report_content))
                    report_text.config(state='disabled')
                    choice_window.destroy()
                def save_to_pdf():
                    if generate_pdf_report(report_content, start_date, end_date, selected_filter, report_type_name,
                                           filter_type_name):
                        choice_window.destroy()
                        period_window.destroy()
                ttk.Label(choice_window, text="Как вы хотите сохранить отчет?").pack(pady=10)
                ttk.Button(choice_window, text="Просмотреть в окне", command=view_report).pack(pady=5, fill='x',padx=20)
                ttk.Button(choice_window, text="Сохранить в PDF", command=save_to_pdf).pack(pady=5, fill='x', padx=20)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при создании отчета:\n{str(e)}")
            finally:
                cursor.close()
        ttk.Button(period_window, text="Сформировать отчет", command=generate_report).pack(pady=20)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Ошибка при создании отчета:\n{str(e)}")