#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os
from tkinter import Tk, filedialog, messagebox
from datetime import datetime
import mysql.connector
from mysql.connector import Error
class ReceiptGenerator:
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
    def get_transaction_data(self, transaction_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            # Получаем основную информацию о транзакции
            cursor.execute("""
                           SELECT ctb.ID,
                                  ctb.Total_Cost,
                                  c.Last_Name          AS Customer_Last_Name ,
                               c.First_Name          AS Customer_First_Name ,
                               c.Middle_Name          AS Customer_Middle_Name ,
                                  c.Email           AS Customer_Email,
                                  d.Discount_Percent,
                                  MAX(ctd.DateTime) AS Transaction_Date
                           FROM Transaction ctb
                                    LEFT JOIN
                                customer c ON ctb.Customer_ID = c.ID
                                    LEFT JOIN
                                Transaction_date ctd ON ctb.ID = ctd.Transaction_ID
                                    LEFT JOIN
                                discount d ON ctb.Discount_ID = d.ID
                           WHERE ctb.ID = %s

                           """, (transaction_id,))
            transaction = cursor.fetchone()
            if not transaction:
                return None
            # Получаем товары в транзакции
            cursor.execute("""
                           SELECT p.Name                AS Product_Name,
                                  ctd.Price,
                                  ctd.Qty,
                                  (ctd.Price * ctd.Qty) AS Total
                           FROM Transaction_details ctd
                                    JOIN
                                product p ON ctd.Product_ID = p.ID
                           WHERE ctd.Transaction_ID = %s
                           """, (transaction_id,))
            products = cursor.fetchall()
            shop_info = 'Магазин Elchain'
            cursor.close()
            return {
                'transaction': transaction,
                'products': products,
                'shop_info': shop_info
            }
        except Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении данных транзакции: {str(e)}")
            return None
    def generate_receipt(self, transaction_id, parent_window=None):
        transaction_data = self.get_transaction_data(transaction_id)
        if not transaction_data:
            messagebox.showerror("Ошибка", "Не удалось получить данные транзакции")
            return
        fonts_folder = "Shrifts"
        if not self.register_fonts(fonts_folder):
            return
        root = Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Сохранить чек как",
            initialfile=f"чек_{transaction_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        if not file_path:
            return
        styles = getSampleStyleSheet()
        styles['Normal'].fontSize = 10
        styles['Heading1'].fontSize = 14
        styles['Heading1'].alignment = 0
        styles.add(ParagraphStyle(name='Right', parent=styles['Normal'], alignment=2))
        available_fonts = pdfmetrics.getRegisteredFontNames()
        if 'DejaVuSerif' in available_fonts:
            styles['Normal'].fontName = 'DejaVuSerif'
            styles['Heading1'].fontName = 'DejaVuSerif'
        elif available_fonts:
            styles['Normal'].fontName = available_fonts[0]
            styles['Heading1'].fontName = available_fonts[0]
        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            title='Кассовый чек',
            author='Кассовая система',
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=5 * mm,
            bottomMargin=5 * mm
        )
        story = []
        story.append(Paragraph('КАССОВЫЙ ЧЕК', styles['Heading1']))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("_" * 42, styles['Normal']))
        story.append(Spacer(1, 3 * mm))
        transaction = transaction_data['transaction']
        # Информация о клиенте
        customer_info = []
        if transaction['Customer_First_Name'] or transaction['Customer_Last_Name']:
            full_name = f"{transaction.get('Customer_Last_Name', '')} {transaction.get('Customer_First_Name', '')} {transaction.get('Customer_Middle_Name', '')}".strip()
            customer_info.append(f"Клиент: {full_name}")
        if transaction.get('Customer_Email'):
            customer_info.append(f"Email: {transaction['Customer_Email']}")
        shop_info = [
                        f"Магазин электронных компонентов Elchain",
                        f"Адрес: г. Москва, пр-т. Ленина, д.1",
                        f"Кассир: Администратор",
                        f"Чек №: {transaction['ID']}",
                        f"Дата: {transaction['Transaction_Date'].strftime('%d.%m.%Y %H:%M:%S')}"
                    ] + customer_info
        for line in shop_info:
            story.append(Paragraph(line, styles['Normal']))
            story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("-" * 42, styles['Normal']))
        story.append(Spacer(1, 3 * mm))
        # Таблица товаров
        table_data = [["№", "Наименование", "Кол-во", "Цена", "Сумма"]]
        for idx, product in enumerate(transaction_data['products'], 1):
            table_data.append((
                str(idx),
                product['Product_Name'],
                str(product['Qty']),
                f"{product['Price']:.2f}",
                f"{product['Total']:.2f}"
            ))
        # Автоматический расчёт ширины колонок
        total_width = doc.width
        col_widths = [total_width * w for w in (0.01, 0.1, 0.1, 0.1, 0.1)]
        table = Table(table_data, colWidths=col_widths, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0, colors.white),  # Убираем сетку
            ('FONTNAME', (0, 0), (-1, -1), styles['Normal'].fontName),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ]))
        story.append(table)
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("-" * 42, styles['Normal']))
        story.append(Spacer(1, 3 * mm))
        # Итоговая информация
        total_cost = float(transaction_data['transaction']['Total_Cost'])
        if transaction_data['transaction']['Discount_Percent']:
            discount_percent = float(transaction_data['transaction']['Discount_Percent'])
            original_total = total_cost / (1 - discount_percent / 100)
            total = [
                ("Сумма без скидки:", f"{original_total:.2f}"),
                (f"Скидка {discount_percent}%:", f"-{original_total - total_cost:.2f}"),
                ("ИТОГО:", f"{total_cost:.2f}"),
                ("БЕЗНАЛИЧНЫМИ:", f"{total_cost:.2f}")
            ]
        else:
            total = [
                ("ИТОГО:", f"{total_cost:.2f}"),
                ("БЕЗНАЛИЧНЫМИ:", f"{total_cost:.2f}")
            ]
        for item in total:
            line = f"{item[0]:<12} {item[1]:>10}"
            p_style = styles['Normal']
            if item[0] == "ИТОГО:":
                p_style = ParagraphStyle(
                    name='Total',
                    parent=styles['Normal'],
                    fontSize=12,
                    fontName=styles['Normal'].fontName + '-Bold' if hasattr(styles['Normal'].fontName, 'split') else
                    styles['Normal'].fontName
                )
            story.append(Paragraph(line, p_style))
            story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("_" * 42, styles['Normal']))
        story.append(Spacer(1, 5 * mm))
        footer = [
            "СПАСИБО ЗА ПОКУПКУ!"
        ]
        for line in footer:
            story.append(Paragraph(line, styles['Normal']))
            story.append(Spacer(1, 2 * mm))
        doc.build(story)
        messagebox.showinfo("Успех", f"Чек успешно сохранен:\n{file_path}")
    def register_fonts(self, fonts_folder):
        if not os.path.exists(fonts_folder):
            messagebox.showerror("Ошибка", f"Папка со шрифтами '{fonts_folder}' не найдена!")
            return False
        for font_file in os.listdir(fonts_folder):
            if font_file.endswith('.ttf'):
                font_name = os.path.splitext(font_file)[0]
                try:
                    pdfmetrics.registerFont(TTFont(font_name, os.path.join(fonts_folder, font_file)))
                except:
                    messagebox.showwarning("Предупреждение", f"Не удалось зарегистрировать шрифт {font_file}")
        return True
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        try:
            transaction_id = int(sys.argv[1])
            receipt_gen = ReceiptGenerator()
            receipt_gen.generate_receipt(transaction_id)
        except ValueError:
            print("Ошибка: ID транзакции должен быть числом")