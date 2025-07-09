#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os
from tkinter import Tk, filedialog, messagebox
from datetime import datetime
import mysql.connector
from mysql.connector import Error


class TransactionReportGenerator:
    def __init__(self):
        self.connection = None
        self.connect_to_db()

    def connect_to_db(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='12345',
                database='elchain'
            )
        except Error as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных: {str(e)}")
            return False
        return True

    def validate_input(self, user_id, organization):
        """Проверяет, что заполнено хотя бы одно из полей (ID или организация) и ID - число"""
        if not user_id and not organization:
            messagebox.showwarning("Ошибка ввода",
                                   "Пожалуйста, заполните поле ID пользователя или название организации")
            return False

        if user_id and not user_id.isdigit():
            messagebox.showwarning("Ошибка ввода", "Поле ID пользователя должно содержать только цифры")
            return False

        return True

    def get_user_transactions(self, user_id=None, organization=None, start_date=None, end_date=None):
        try:
            cursor = self.connection.cursor(dictionary=True)
            # Основной запрос для получения транзакций без подсчета товаров
            query = """
                    SELECT t.ID             as transaction_id,
                           t.Total_Cost,
                           MAX(td.Datetime) as transaction_date,
                           c.ID             as customer_id,
                           c.Last_Name,
                           c.First_Name,
                           c.Middle_Name,
                           c.Organization,
                           c.Email,
                           d.Discount_Percent
                    FROM Transaction t
                             JOIN
                         Customer c ON t.Customer_ID = c.ID
                             LEFT JOIN
                         Discount d ON t.Discount_ID = d.ID
                             LEFT JOIN
                         TRANSACTION_DATE td ON t.ID = td.Transaction_ID
                    WHERE td.Status_id > 1 \
                    """  # Added the status condition here
            params = []
            if user_id:
                query += " AND c.ID = %s"
                params.append(user_id)
            if organization:
                query += " AND c.Organization = %s"
                params.append(organization)
            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                query += " AND (SELECT MAX(td2.Datetime) FROM TRANSACTION_DATE td2 WHERE td2.Transaction_ID = t.ID) >= %s"
                params.append(start_date)
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                query += " AND (SELECT MAX(td2.Datetime) FROM TRANSACTION_DATE td2 WHERE td2.Transaction_ID = t.ID) <= %s"
                params.append(end_date)
            query += """
                GROUP BY 
                    t.ID, t.Total_Cost, c.ID, 
                    c.Last_Name, c.First_Name, c.Middle_Name, 
                    c.Organization, c.Email, d.Discount_Percent
                ORDER BY 
                    MAX(td.Datetime) DESC
            """
            cursor.execute(query, params)
            transactions = cursor.fetchall()

            # Получаем детали и количество товаров для каждой транзакции отдельно
            for transaction in transactions:
                cursor.execute("""
                               SELECT p.Name                  as product_name,
                                      tdet.Price,
                                      tdet.Qty,
                                      (tdet.Price * tdet.Qty) as total
                               FROM Transaction_Details tdet
                                        JOIN Product p ON tdet.Product_ID = p.ID
                               WHERE tdet.Transaction_ID = %s
                               """, (transaction['transaction_id'],))
                items = cursor.fetchall()
                transaction['items'] = items
                # Рассчитываем общую сумму без скидки
                transaction['original_sum'] = sum(item['total'] for item in items)
                # Получаем количество товаров в транзакции отдельным запросом
                cursor.execute("""
                               SELECT SUM(Qty) as items_count
                               FROM Transaction_Details
                               WHERE Transaction_ID = %s
                               """, (transaction['transaction_id'],))
                count_result = cursor.fetchone()
                transaction['items_count'] = count_result['items_count'] if count_result else 0

            cursor.close()
            return transactions
        except Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении данных транзакций: {str(e)}")
            return None

    def generate_report(self, user_id=None, organization=None, start_date=None, end_date=None, parent_window=None):
        # Проверяем введенные данные перед генерацией отчета
        if not self.validate_input(str(user_id) if user_id else "", organization):
            return

        try:
            transactions = self.get_user_transactions(user_id, organization, start_date, end_date)
            if not transactions:
                messagebox.showerror("Ошибка", "Не удалось получить данные транзакций")
                return

            fonts_folder = "Shrifts"
            if not self.register_fonts(fonts_folder):
                return

            # Создаем временное окно Tkinter, если parent_window не указан
            temp_root = None
            if not parent_window:
                temp_root = Tk()
                temp_root.withdraw()

            try:
                # Формируем имя файла
                if user_id:
                    file_name = f"report_user_{user_id}"
                elif organization:
                    file_name = f"report_org_{organization}"
                else:
                    file_name = "report_all_transactions"

                # Обработка дат для имени файла
                if start_date or end_date:
                    start_str = ""
                    end_str = ""
                    if start_date:
                        if isinstance(start_date, str):
                            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                            start_str = start_date_obj.strftime('%Y%m%d')
                        else:
                            start_str = start_date.strftime('%Y%m%d')
                    if end_date:
                        if isinstance(end_date, str):
                            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                            end_str = end_date_obj.strftime('%Y%m%d')
                        else:
                            end_str = end_date.strftime('%Y%m%d')
                    file_name += f"_{start_str}_{end_str}"

                current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
                file_name += f"_{current_time}.pdf"

                root_window = parent_window if parent_window else temp_root
                file_path = filedialog.asksaveasfilename(
                    parent=root_window,
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    title="Сохранить отчет как",
                    initialfile=file_name
                )

                if not file_path:
                    return

                styles = getSampleStyleSheet()
                styles['Normal'].fontSize = 10
                styles['Heading1'].fontSize = 16
                styles['Heading1'].alignment = 1
                styles['Heading2'].fontSize = 12
                styles['Heading2'].alignment = 0
                styles.add(ParagraphStyle(name='Right', parent=styles['Normal'], alignment=2))
                styles.add(ParagraphStyle(name='Center', parent=styles['Normal'], alignment=1))
                styles.add(ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='DejaVuSerif-Bold'))

                try:
                    pdfmetrics.registerFont(TTFont('DejaVuSerif', os.path.join(fonts_folder, 'DejaVuSerif.ttf')))
                    pdfmetrics.registerFont(
                        TTFont('DejaVuSerif-Bold', os.path.join(fonts_folder, 'DejaVuSerif-Bold.ttf')))
                    styles['Normal'].fontName = 'DejaVuSerif'
                    styles['Heading1'].fontName = 'DejaVuSerif-Bold'
                    styles['Heading2'].fontName = 'DejaVuSerif-Bold'
                    styles['Bold'].fontName = 'DejaVuSerif-Bold'
                except Exception as e:
                    messagebox.showerror("Ошибка шрифта", f"Не удалось загрузить шрифт DejaVu: {str(e)}")
                    return

                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=A4,
                    title='Отчет по транзакциям',
                    author='Система учета транзакций',
                    leftMargin=15 * mm,
                    rightMargin=15 * mm,
                    topMargin=10 * mm,
                    bottomMargin=10 * mm
                )

                story = []

                title = "ОТЧЕТ ПО ТРАНЗАКЦИЯМ"
                if user_id and transactions:
                    customer = transactions[0]
                    title += f"<br/>Покупатель: {customer['Last_Name']} {customer['First_Name']} {customer['Middle_Name'] or ''}"
                elif organization:
                    title += f"<br/>Организация: {organization}"

                if start_date or end_date:
                    date_range = []
                    if start_date:
                        if isinstance(start_date, str):
                            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                            date_range.append(f"с {start_date_obj.strftime('%Y-%m-%d')}")
                        else:
                            date_range.append(f"с {start_date.strftime('%Y-%m-%d')}")
                    if end_date:
                        if isinstance(end_date, str):
                            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                            date_range.append(f"по {end_date_obj.strftime('%Y-%m-%d')}")
                        else:
                            date_range.append(f"по {end_date.strftime('%Y-%m-%d')}")
                    title += f"<br/>{' '.join(date_range)}"
                else:
                    title += "<br/>За весь период"

                story.append(Paragraph(title, styles['Heading1']))
                story.append(Spacer(1, 10 * mm))

                # Общая статистика
                total_transactions = len(transactions)
                total_amount = sum(t['Total_Cost'] for t in transactions)
                total_original_sum = sum(t['original_sum'] for t in transactions)
                total_items = sum(t['items_count'] for t in transactions)
                total_discount = total_original_sum - total_amount

                stats = [
                    f"Всего транзакций: {total_transactions}",
                    f"Общая сумма без скидки: {total_original_sum:.2f} руб.",
                    f"Общая сумма скидки: {total_discount:.2f} руб.",
                    f"Итоговая сумма: {total_amount:.2f} руб.",
                    f"Всего товаров: {total_items}",
                    f"Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ]

                for stat in stats:
                    story.append(Paragraph(stat, styles['Normal']))
                    story.append(Spacer(1, 2 * mm))

                story.append(Spacer(1, 10 * mm))

                # Детализация по транзакциям
                for idx, transaction in enumerate(transactions, 1):
                    trans_title = [
                        f"Транзакция №{transaction['transaction_id']}",
                        f"Дата: {transaction['transaction_date'].strftime('%Y-%m-%d %H:%M:%S') if transaction['transaction_date'] else 'Дата не указана'}",
                        f"Сумма без скидки: {transaction['original_sum']:.2f} руб.",
                        f"Сумма с учетом скидки: {transaction['Total_Cost']:.2f} руб."
                    ]

                    if transaction['Discount_Percent']:
                        trans_title.append(f"Скидка: {transaction['Discount_Percent']}%")
                        discount_amount = transaction['original_sum'] - transaction['Total_Cost']
                        trans_title.append(f"Сумма скидки: {discount_amount:.2f} руб.")
                    else:
                        trans_title.append("Скидка: 0%")

                    trans_title.append(
                        f"Клиент: {transaction['Last_Name']} {transaction['First_Name']} {transaction['Middle_Name'] or ''}")
                    if transaction['Organization']:
                        trans_title.append(f"Организация: {transaction['Organization']}")

                    for line in trans_title:
                        story.append(Paragraph(line, styles['Normal']))
                        story.append(Spacer(1, 2 * mm))

                    # Таблица товаров
                    table_data = [
                        ["№", "Наименование", "Кол-во", "Цена", "Сумма"]
                    ]

                    for item_idx, item in enumerate(transaction['items'], 1):
                        table_data.append([
                            str(item_idx),
                            item['product_name'],
                            str(item['Qty']),
                            f"{item['Price']:.2f}",
                            f"{item['total']:.2f}"
                        ])

                    table_data.append([
                        "", "Сумма без скидки:", "", "",
                        f"{transaction['original_sum']:.2f}"
                    ])

                    if transaction['Discount_Percent']:
                        table_data.append([
                            "", f"Скидка ({transaction['Discount_Percent']}%):", "", "",
                            f"-{(transaction['original_sum'] - transaction['Total_Cost']):.2f}"
                        ])

                    table_data.append([
                        "", "ИТОГО:", "", "",
                        f"{transaction['Total_Cost']:.2f}"
                    ])

                    col_widths = [15 * mm, 70 * mm, 20 * mm, 25 * mm, 25 * mm]
                    table = Table(table_data, colWidths=col_widths, hAlign='LEFT')
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                        ('FONTNAME', (0, -1), (-1, -1), 'DejaVuSerif-Bold'),
                        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black)
                    ]))

                    story.append(table)
                    story.append(Spacer(1, 10 * mm))

                doc.build(story)
                messagebox.showinfo("Успех", f"Отчет успешно сохранен:\n{file_path}")
            finally:
                if temp_root:
                    temp_root.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при генерации отчета: {str(e)}")

    def register_fonts(self, fonts_folder):
        if not os.path.exists(fonts_folder):
            messagebox.showerror("Ошибка", f"Папка со шрифтами '{fonts_folder}' не найдена!")
            return False

        deja_vu_fonts = {
            'DejaVuSerif.ttf': 'DejaVuSerif',
            'DejaVuSerif-Bold.ttf': 'DejaVuSerif-Bold'
        }

        for font_file, font_name in deja_vu_fonts.items():
            font_path = os.path.join(fonts_folder, font_file)
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось зарегистрировать шрифт {font_file}: {str(e)}")
                    return False
            else:
                messagebox.showerror("Ошибка", f"Файл шрифта {font_file} не найден в папке {fonts_folder}!")
                return False

        return True