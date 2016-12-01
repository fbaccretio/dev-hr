# -*- encoding: utf-8 -*-

{
    'name': 'Create leaves based on timesheet',
    'version': '1.0',
    'license': 'OPL-1',
    'category': 'HR',
    'author': 'ERP Ukraine',
    'website': 'http://erp.co.ua',
    'description': """
When user adds new analytic entry to dedicated analytic account
it can be reflected in leaves calendar.
""",
    'depends': [
        'hr_timesheet',
        'hr_timesheet_sheet',
        'hr_holidays',
    ],
    'data': [
        'views/analytic_account_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
