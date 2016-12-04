# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.exceptions import UserError

DBG = True


class HrPayslipPFT(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """
        res = []
        for contract in self.env['hr.contract'].browse(contract_ids):
            if not contract.employee_id.user_id:
                empl_name = contract.employee_id.name_related
                raise UserError(
                    'No User related with Employee: {}'.format(empl_name))
            attendances = {
                     'name': _("Normal Working Days paid at 100%"),
                     'sequence': 1,
                     'code': 'WORK100',
                     'number_of_days': 0.0,
                     'number_of_hours': 0.0,
                     'contract_id': contract.id,
                }
            leaves = {}
            query = """
            SELECT
                l.date, l.account_id, a.salary_code, SUM(l.unit_amount) AS amt
            FROM
                account_analytic_line l
                INNER JOIN account_analytic_account a
                    ON a.id = l.account_id
                INNER JOIN hr_timesheet_sheet_sheet s
                    ON l.sheet_id = s.id
            WHERE
                l.date >= '{}'
                AND l.date <= '{}'
                AND l.user_id = {}
                AND l.company_id = {}
                AND s.state = '{}'
            GROUP BY
                l.date, l.account_id, a.salary_code
            ORDER BY
                l.date;
            """.format(
                date_from,
                date_to,
                contract.employee_id.user_id.id,
                contract.employee_id.user_id.company_id.id,
                'draft' if DBG else 'done')
            self.env.cr.execute(query)
            analytic_lines_grouped = self.env.cr.dictfetchall()
            # analytic_lines_grouped is a list of dicts
            # [{
            #     'date': '2016-12-01',
            #     'salary_code': None,
            #     'account_id': 1,
            #     'amt': 4.0
            # },
            # {...}, ...]

            for l in analytic_lines_grouped:
                print '{} {} {} {}'.format(
                    l['date'], l['amt'], l['account_id'], l['salary_code'])
                if not l['salary_code']:
                    attendances['number_of_days'] += 1
                    attendances['number_of_hours'] += l['amt']
                else:
                    found = False
                    for el in res:
                        if not found and el['code'] == l['salary_code']:
                            found = True
                            el['number_of_days'] += 1
                            el['number_of_hours'] += l['amt']
                    if not found:
                        an_acc = self.env['account.analytic.account'].browse(
                            l['account_id'])
                        if an_acc and an_acc.name:
                            acc_name = an_acc.name
                        else:
                            acc_name = l['salary_code']
                        res.append({
                            'name': acc_name,
                            'sequence': 2,
                            'code': l['salary_code'],
                            'number_of_days': 1,
                            'number_of_hours': l['amt'],
                            'contract_id': contract.id,
                        })
            res.append(attendances)
        return res
