# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _


class HrPayslipPFT(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be
        applied for the given contract between date_from and date_to
        """
        # TODO  for contract in self.env['hr.contract'].browse(contract_ids)
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('user_id', '=', self.employee_id.user_id.id),
            ('sheet_state', '=', 'draft'),  # TODO change to 'done'
            ('company_id', '=', self.company_id.id),
        ]
        analytic_lines = self.env['account.analytic.line'].search(domain)

        # same query using SQL but with grouping already done:
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
            self.date_from,
            self.date_to,
            self.employee_id.user_id.id,
            self.company_id.id,
            'draft')    # FIXME 'done'
        self.env.cr.execute(query)
        for row in self.env.cr.dictfetchall():
            print row
    # returns list of dicts
    # {'date': '2016-12-01', 'salary_code': None, 'account_id': 1, 'amt': 4.0}

        res = []
        attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 1,
                 'code': 'WORK100',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract_ids[0],    # FIXME
            }
        leaves = {}

        for l in analytic_lines:
            # should be grouped by (day, account_id) but sql will do it for us
            print '{} {} {}'.format(l.date, l.unit_amount, l.account_id)
            if not l.account_id.salary_code:
                attendances['number_of_days'] += 1
                attendances['number_of_hours'] += l.unit_amount
            else:
                found = False
                for el in res:
                    if not found and el['code'] == l.account_id.salary_code:
                        found = True
                        el['number_of_days'] += 1
                        el['number_of_hours'] += l.unit_amount
                if not found:
                    res.append({
                        'name': l.account_id.name,
                        'sequence': 2,
                        'code': l.account_id.salary_code,
                        'number_of_days': 1,
                        'number_of_hours': l.unit_amount,
                        'contract_id': contract_ids[0],    # FIXME
                    })
                pass
        res.append(attendances)
        return res
