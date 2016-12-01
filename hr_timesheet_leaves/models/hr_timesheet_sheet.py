# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _


class HrTimesheetSheetHTL(models.Model):
    _inherit = 'hr_timesheet_sheet.sheet'

    @api.onchange('state')
    def onchange_state(self):
        self.ensure_one()

        if self.state == 'new':
            domain = [
                ('use_tasks', '=', True),
                ('use_leaves', '=', True),
                ('active', '=', True),
                ('leave_type', '!=', False),
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

        # if self.state == 'done':
        #     # Approved by manager.
        #     # It's safe to create leaves
        #     days_grouped = {}
        #     for t in self.timesheet_ids:
        #         if t.date not in days_grouped:
        #             days_grouped[t.date] = [{
        #                 'name': t.name,
        #                 'holiday_status_id': t.leave_type.id,
        #                 'unit_amount': t.unit_amount,
        #                 'employee_id': self.employee_id.id,
        #             }]
        #         else:
        #             for el in days_grouped[t.date]:
        #                 if el['holiday_status_id'] == t.leave_type.id:
        #                     el['unit_amount'] += t.unit_amount
        #                 else:
        #                     el.append()

    @api.multi
    def write(self, vals):
        print 'write'
        # for t in self.timesheet_ids:
        #     print 'ts-----'
        #     print t.name
        #     print t.unit_amount
        #     print t.date
        #     print t.project_id.name
        #     print t.user_id.name
        return super(HrTimesheetSheetHTL, self).write(vals)

    @api.model
    def create(self, vals):
        print 'create'
        for t in self.timesheet_ids:
            print 'ts-----'
            print t.name
            print t.unit_amount
            print t.date
            print t.project_id.name
            print t.user_id.name
        return super(HrTimesheetSheetHTL, self).create(vals)
