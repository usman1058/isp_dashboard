import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .models import (
    Customer, Expense, ExpenseCategory, Payment, PaymentDue,
    PaymentReminder, Reminder, ReminderSchedule, ServicePlan, WhatsAppMessage,
)


def _collect_section(data, title, headers, rows, filter_row=None):
    """Append a named section (title + headers + rows) to the backup data dict."""
    if filter_row:
        rows = [r for r in rows if filter_row(r)]
    data.append({
        'title': title,
        'headers': headers,
        'rows': rows,
    })


def collect_backup_data():
    """Gather all backup-worthy data from the database. Customers come first."""
    data = []
    today = datetime.now()

    _collect_section(
        data,
        'Customers',
        ['Username', 'First Name', 'Last Name', 'Join Date', 'Phone',
         'Area', 'Street', 'St#', 'House#', 'Modem', 'Plan', 'Install Date',
         'Status', 'Notes', 'Created At', 'Updated At'],
        [
            (c.username, c.first_name, c.last_name, c.join_date.isoformat() if c.join_date else '',
             c.phone, c.address_area or '', c.street_name or '', c.street_num or '',
             c.house_num or '', c.modem_type, c.service_plan.name if c.service_plan else '',
             c.service_installation_date.isoformat() if c.service_installation_date else '',
             c.status, c.notes or '',
             c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else '',
             c.updated_at.strftime('%Y-%m-%d %H:%M') if c.updated_at else '')
            for c in Customer.objects.select_related('service_plan').all()
        ],
    )

    _collect_section(
        data,
        'Service Plans',
        ['Name', 'Speed', 'Price', 'Active'],
        [(p.name, p.speed, float(p.price), 'Yes' if p.is_active else 'No') for p in ServicePlan.objects.all()],
    )

    _collect_section(
        data,
        'Payments',
        ['Invoice', 'Customer', 'Amount', 'Payment Date', 'Month For',
         'Method', 'Received By', 'Notes'],
        [
            (p.invoice_number, p.customer.username, float(p.amount),
             p.payment_date.isoformat(), p.month_for.strftime('%B %Y'),
             p.get_method_display(), p.received_by.username, p.notes or '')
            for p in Payment.objects.select_related('customer', 'received_by').all()
        ],
    )

    _collect_section(
        data,
        'Expense Categories',
        ['Name'],
        [(c.name,) for c in ExpenseCategory.objects.all()],
    )

    _collect_section(
        data,
        'Expenses',
        ['Category', 'Description', 'Amount', 'Date'],
        [
            (e.category.name, e.description or '', float(e.amount),
             e.date.isoformat())
            for e in Expense.objects.select_related('category').all()
        ],
    )

    _collect_section(
        data,
        'Reminders',
        ['Customer', 'Due Date', 'Type', 'Scheduled', 'Status', 'Message'],
        [
            (r.customer.username, r.due_date.isoformat(), r.get_reminder_type_display(),
             r.scheduled_time.isoformat(), r.status, r.message or '')
            for r in Reminder.objects.select_related('customer').all()
        ],
    )

    _collect_section(
        data,
        'Reminder Schedule',
        ['Customer', 'Due Date', 'Send Time', 'Message', 'Sent'],
        [
            (r.customer.username, r.due_date.isoformat(), r.send_time.isoformat(),
             r.message, 'Yes' if r.sent else 'No')
            for r in ReminderSchedule.objects.select_related('customer').all()
        ],
    )

    _collect_section(
        data,
        'WhatsApp Messages',
        ['Customer', 'Message', 'Timestamp', 'Status'],
        [
            (m.customer.username, m.message, m.timestamp.isoformat(), m.status)
            for m in WhatsAppMessage.objects.select_related('customer').all()
        ],
    )

    _collect_section(
        data,
        'Payment Dues',
        ['Customer', 'Due Date', 'Amount', 'Paid'],
        [
            (d.customer.username, d.due_date.isoformat(), float(d.amount),
             'Yes' if d.is_paid else 'No')
            for d in PaymentDue.objects.select_related('customer').all()
        ],
    )

    _collect_section(
        data,
        'Payment Reminders',
        ['Customer', 'Due Date', 'Type', 'Sent At', 'Sent'],
        [
            (r.customer.username, r.due_date.isoformat(), r.get_reminder_type_display(),
             r.sent_at.isoformat() if r.sent_at else '', 'Yes' if r.is_sent else 'No')
            for r in PaymentReminder.objects.select_related('customer').all()
        ],
    )

    return data, today


def collect_monthly_report_data(year, month):
    """Collect detailed client payment data for a specific month."""
    data = []
    today = datetime.now()

    # Full address string helper
    def build_area(c):
        parts = []
        if c.address_area:
            parts.append(c.address_area)
        if c.street_name:
            parts.append(c.street_name)
        if c.street_num:
            parts.append(f'St#{c.street_num}')
        if c.house_num:
            parts.append(f'House#{c.house_num}')
        return ', '.join(parts) if parts else '—'

    # All payments for the selected month (billed month = month_for)
    payments = Payment.objects.filter(
        month_for__year=year,
        month_for__month=month
    ).select_related('customer', 'received_by').order_by('customer__first_name')

    if not payments.exists():
        # Still create an empty section so the file has the header row
        _collect_section(
            data,
            'Monthly Payment Report',
            ['Client Name', 'Username', 'Billing Date',
             'Amount', 'Area', 'Payment Method', 'Payment Date', 'Received By'],
            [],
        )
        return data, today

    _collect_section(
        data,
        'Monthly Payment Report',
        ['Client Name', 'Username', 'Billing Date',
         'Amount', 'Area', 'Payment Method', 'Payment Date', 'Received By'],
        [
            (
                f'{p.customer.first_name} {p.customer.last_name}',
                p.customer.username,
                p.month_for.strftime('%d %b %Y'),
                float(p.amount),
                build_area(p.customer),
                p.get_method_display(),
                p.payment_date.strftime('%d %b %Y') if p.payment_date else '—',
                p.received_by.username if p.received_by else '—'
            )
            for p in payments
        ],
    )

    # Also add unpaid customers for that month (customers with plan but no payment for the month)
    paid_cust_ids = set(payments.values_list('customer_id', flat=True))
    unpaid_customers = Customer.objects.filter(
        service_plan__isnull=False
    ).exclude(id__in=paid_cust_ids).select_related('service_plan')

    if unpaid_customers.exists():
        _collect_section(
            data,
            'Unpaid Customers (for the month)',
            ['Client Name', 'Username',
             'Billing Date', 'Expected Amount', 'Area', 'Plan', 'Status'],
            [
                (
                    f'{c.first_name} {c.last_name}',
                    c.username,
                    f'01 {datetime(year, month, 1).strftime("%b %Y")}',
                    float(c.service_plan.price) if c.service_plan else 0,
                    build_area(c),
                    c.service_plan.name if c.service_plan else '—',
                    c.status
                )
                for c in unpaid_customers
            ],
        )

    return data, today


def generate_monthly_report_excel(year, month):
    data, now = collect_monthly_report_data(year, month)
    wb = Workbook()
    wb.remove(wb.active)
    stamp = now.strftime('%Y%m%d_%H%M%S')

    for section in data:
        headers = section['headers']
        ws = wb.create_sheet(title=section['title'][:31])
        ws.append(headers)
        for row in section['rows']:
            ws.append([str(x) if x is not None else '' for x in row])
        _excel_style(ws, headers, len(headers))

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer, f'monthly_report_{year}_{month:02d}_{stamp}.xlsx', now


def generate_monthly_report_pdf(year, month):
    data, now = collect_monthly_report_data(year, month)
    buffer = io.BytesIO()
    stamp = now.strftime('%Y%m%d_%H%M%S')

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f'Monthly Report {year}-{month:02d}',
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Title'], fontSize=18, spaceAfter=4)
    subtitle_style = ParagraphStyle(
        'ReportSub', parent=styles['Normal'], fontSize=10,
        textColor=colors.grey, spaceAfter=14)
    heading_style = ParagraphStyle(
        'ReportHeading', parent=styles['Heading2'], fontSize=13,
        textColor=colors.HexColor('#4E73DF'), spaceBefore=12, spaceAfter=6)
    cell_style = ParagraphStyle(
        'ReportCell', fontSize=7, leading=8)
    header_cell_style = ParagraphStyle(
        'ReportHeaderCell', fontSize=7, leading=8,
        textColor=colors.white, fontName='Helvetica-Bold')

    elements = [
        Paragraph(f'Monthly Payment Report — {datetime(year, month, 1).strftime("%B %Y")}', title_style),
        Paragraph(f'Generated on {now.strftime("%d %b %Y at %H:%M:%S")}', subtitle_style),
    ]

    for section in data:
        elements.append(Paragraph(section['title'], heading_style))
        headers = [Paragraph(h, header_cell_style) for h in section['headers']]
        body = []
        for row in section['rows']:
            body.append([Paragraph(str(x) if x is not None else '', cell_style) for x in row])

        if not body:
            elements.append(Paragraph('No records for this period.', cell_style))
            continue

        table = Table([headers] + body, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4E73DF')),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#D1D4D9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F8')]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 8))

    doc.build(elements)
    buffer.seek(0)
    return buffer, f'monthly_report_{year}_{month:02d}_{stamp}.pdf', now


def _excel_style(ws, header, ncols):
    ws.freeze_panes = 'A2'
    for col in range(1, ncols + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='4E73DF', end_color='4E73DF', fill_type='solid')
        cell.alignment = Alignment(horizontal='center')
    ws.row_dimensions[1].height = 20
    for col in range(1, ncols + 1):
        ws.column_dimensions[get_column_letter(col)].width = max(
            12, min(40, len(str(header[col - 1])) + 4))


def generate_excel_backup():
    data, now = collect_backup_data()
    wb = Workbook()
    wb.remove(wb.active)
    stamp = now.strftime('%Y%m%d_%H%M%S')

    for section in data:
        headers = section['headers']
        ws = wb.create_sheet(title=section['title'][:31])
        ws.append(headers)
        for row in section['rows']:
            ws.append([str(x) if x is not None else '' for x in row])
        _excel_style(ws, headers, len(headers))

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer, f'backup_{stamp}.xlsx', now


def generate_pdf_backup():
    data, now = collect_backup_data()
    buffer = io.BytesIO()
    stamp = now.strftime('%Y%m%d_%H%M%S')

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f'SSISP Backup {stamp}',
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'BackupTitle', parent=styles['Title'], fontSize=18, spaceAfter=4)
    subtitle_style = ParagraphStyle(
        'BackupSub', parent=styles['Normal'], fontSize=10,
        textColor=colors.grey, spaceAfter=14)
    heading_style = ParagraphStyle(
        'BackupHeading', parent=styles['Heading2'], fontSize=13,
        textColor=colors.HexColor('#4E73DF'), spaceBefore=12, spaceAfter=6)
    cell_style = ParagraphStyle(
        'BackupCell', fontSize=7, leading=8)
    header_cell_style = ParagraphStyle(
        'BackupHeaderCell', fontSize=7, leading=8,
        textColor=colors.white, fontName='Helvetica-Bold')

    elements = [Paragraph('SSISP Data Backup', title_style),
                Paragraph(
                    f'Generated on {now.strftime("%d %b %Y at %H:%M:%S")} — '
                    f'customer, billing and expense records', subtitle_style)]

    for section in data:
        elements.append(Paragraph(section['title'], heading_style))
        headers = [Paragraph(h, header_cell_style) for h in section['headers']]
        body = []
        for row in section['rows']:
            body.append([Paragraph(str(x) if x is not None else '', cell_style) for x in row])

        if not body:
            elements.append(Paragraph('No records.', cell_style))
            continue

        table = Table([headers] + body, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4E73DF')),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#D1D4D9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F8')]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 8))

    doc.build(elements)
    buffer.seek(0)
    return buffer, f'backup_{stamp}.pdf', now