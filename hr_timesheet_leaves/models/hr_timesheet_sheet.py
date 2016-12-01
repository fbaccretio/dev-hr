# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _


class HrTimesheetSheetHTL(models.Model):
    _inherit = 'hr_timesheet_sheet.sheet'

    @api.onchange('state')
    def onchange_state(self):
        if self.state == 'new':
            # self.env['hr_timesheet_sheet.sheet.account'].create({
            #     'name': 1,
            #     'sheet_id': self.id,
            #     'total': 0,
            # })
            domain = [
                ('use_tasks', '=', True),
                ('use_leaves', '=', True),
                ('active', '=', True),   # and leave_type not false
            ]
            an_accounts = self.env['account.analytic.account'].search(domain)
            for acc in an_accounts:
                proj_id = self.env['project.project'].search(
                    [('analytic_account_id', '=', acc.id)], limit=1)
                self.env['account.analytic.line'].create({
                    'name': '/',
                    'date': self.date_from,
                    'amount': 0.0,
                    'account_id': acc.id,
                    'partner_id': self.user_id.partner_id.id,
                    'user_id': self.user_id.id,
                    'sheet_id': self.id,
                    'project_id': proj_id.id,
                })
