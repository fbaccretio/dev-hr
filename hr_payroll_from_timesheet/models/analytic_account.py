# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _


class AccountAnalyticAccountPFT(models.Model):
    _inherit = 'account.analytic.account'

    use_leaves = fields.Boolean(
        string='Use Leaves',
        default=False)

    salary_code = fields.Char(string='Salary Code')

    @api.onchange('use_leaves')
    def onchange_use_leaves(self):
        self.ensure_one()
        if self.use_leaves and not self.use_tasks:
            self.use_tasks = True
        return

    @api.multi
    def write(self, vals):
        if 'salary_code' in vals and vals['salary_code'] is not False:
            # remove whitespaces
            vals['salary_code'] = vals['salary_code'].replace(" ", "")
        return super(AccountAnalyticAccountPFT, self).write(vals)

    @api.model
    def create(self, vals):
        if 'salary_code' in vals and vals['salary_code'] is not False:
            # remove whitespaces
            vals['salary_code'] = vals['salary_code'].replace(" ", "")
        return super(AccountAnalyticAccountPFT, self).create(vals)


class AccountAnalyticLinePFT(models.Model):
    _inherit = 'account.analytic.line'
    # reference to timesheet state for domain criteria
    sheet_state = fields.Selection(related='sheet_id.state')
