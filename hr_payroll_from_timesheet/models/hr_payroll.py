# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _


class HrPayslipPFT(models.Model):
    _inherit = 'hr.payslip'

    # def _default_date_from(self):
    #     user = self.env['res.users'].browse(self.env.uid)
    #     r = user.company_id and user.company_id.timesheet_range or 'month'
    #     if r == 'month':
    #         return time.strftime('%Y-%m-01')
    #     elif r == 'week':
    #         return (datetime.today() + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
    #     elif r == 'year':
    #         return time.strftime('%Y-01-01')
    #     return fields.date.context_today(self)
    #
    # def _default_date_to(self):
    #     user = self.env['res.users'].browse(self.env.uid)
    #     r = user.company_id and user.company_id.timesheet_range or 'month'
    #     if r == 'month':
    #         return (datetime.today() + relativedelta(months=+1, day=1, days=-1)).strftime('%Y-%m-%d')
    #     elif r == 'week':
    #         return (datetime.today() + relativedelta(weekday=6)).strftime('%Y-%m-%d')
    #     elif r == 'year':
    #         return time.strftime('%Y-12-31')
    #     return fields.date.context_today(self)

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """

        # An example of dict
        #     'name': _("Normal Working Days paid at 100%"),
        #     'sequence': 1,
        #     'code': 'WORK100',
        #     'number_of_days': 0.0,
        #     'number_of_hours': 0.0,
        #     'contract_id': contract.id,
        domain = [
            ('use_tasks', '=', True),
            ('use_leaves', '=', True),
            ('active', '=', True),
            ('leave_type', '!=', False),
        ]
