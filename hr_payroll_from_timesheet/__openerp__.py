# -*- encoding: utf-8 -*-

{
    'name': 'Payroll Customization For Baumann Elektro',
    'version': '1.0',
    'license': 'OPL-1',
    'category': 'HR',
    'author': 'ERP Ukraine',
    'website': 'http://erp.co.ua',
    'description': """
This module enables to enter leaves directly to timesheet application.
When payslip is filled with leaves and worked hours
information from timesheet is taken into account.
""",
    'depends': [
        'hr_timesheet',
        'hr_timesheet_sheet',
        'hr_payroll',
        'hr_holidays',
    ],
    'data': [
        'data/analytic_accounts.xml',
        'views/analytic_account_view.xml',
        'views/hr_payslip_view.xml',
        'views/hr_holidays_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
