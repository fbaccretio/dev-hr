# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
from openerp.exceptions import UserError

from datetime import timedelta

DBG = True


class HrContractL10nPFT(models.Model):
    _inherit = 'hr.contract'

    overtime_analytic = fields.Many2one(
        'account.analytic.account',
        string=u"Overtime Account")


class HrPayslipPFT(models.Model):
    _inherit = 'hr.payslip'

    hours_scheduled = fields.Float(
        string='Scheduled Hours',
        help='Number of Woking Hours scheduled for current month',
        compute='_compute_hours_scheduled',
        store=True)
    hours_worked = fields.Float(
        string='Worked Hours',
        help='Total Woked Hours + Leaves for current month',
        compute='_compute_hours_worked',
        store=True)
    hours_saldo = fields.Float(
        string='Saldo Hours',
        compute='_compute_hours_saldo',
        store=True)

    leaves_allocated = fields.Float(
        string='Leaves Allocated',
        compute='_compute_leaves_allocated',
        store=True)
    leaves_used = fields.Float(
        string='Leaves Used',
        compute='_compute_leaves_used',
        store=True)
    leaves_remaining = fields.Float(
        string='Leaves Remaining',
        compute='_compute_leaves_remaining',
        store=True)

    def _get_leaves_allocated(self):
        user_id = self.contract_id.employee_id.user_id
        if not user_id:
            return
        self.env.cr.execute("""
            SELECT
                sum(h.number_of_days) AS days,
                h.employee_id
            FROM
                hr_holidays h
                join hr_holidays_status s ON (s.id=h.holiday_status_id)
            WHERE
                h.state='validate' AND
                h.type='add' AND
                s.limit=False AND
                h.employee_id in %s
            GROUP BY h.employee_id""", (tuple(user_id.ids),))
        return dict(
            (row['employee_id'],
             row['days']) for row in self.env.cr.dictfetchall())

    @api.depends('contract_id')
    def _compute_leaves_allocated(self):
        for rec in self:
            if not rec.contract_id or not rec.contract_id.employee_id:
                continue
            allocated = rec._get_leaves_allocated()
            user_id = rec.contract_id.employee_id.user_id
            rec.leaves_allocated = allocated.get(user_id.id, 0.0)

    def _get_leaves_used(self):
        user_id = self.contract_id.employee_id.user_id
        if not user_id:
            return
        self.env.cr.execute("""
            SELECT
                sum(h.number_of_days) AS days,
                h.employee_id
            FROM
                hr_holidays h
                join hr_holidays_status s ON (s.id=h.holiday_status_id)
            WHERE
                h.state='validate' AND
                h.type='remove' AND
                s.limit=False AND
                h.employee_id in %s
            GROUP BY h.employee_id""", (tuple(user_id.ids),))
        return dict(
            (row['employee_id'],
             row['days']) for row in self.env.cr.dictfetchall())

    @api.depends('contract_id')
    def _compute_leaves_used(self):
        for rec in self:
            if not rec.contract_id or not rec.contract_id.employee_id:
                continue
            allocated = rec._get_leaves_used()
            user_id = rec.contract_id.employee_id.user_id
            rec.leaves_used = -1 * allocated.get(user_id.id, 0.0)

    @api.depends('leaves_allocated', 'leaves_used')
    def _compute_leaves_remaining(self):
        for rec in self:
            rec.leaves_remaining = rec.leaves_allocated - rec.leaves_used

    @api.depends('date_from', 'date_to', 'contract_id')
    def _compute_hours_scheduled(self):
        for rec in self:
            if not rec.contract_id.working_hours:
                continue
            wrk_hrs = rec.contract_id.working_hours
            day_from = fields.Datetime.from_string(rec.date_from)
            day_to = fields.Datetime.from_string(rec.date_to)
            nb_of_days = (day_to - day_from).days + 1

            for day in range(0, nb_of_days):
                working_hours_on_day = wrk_hrs.working_hours_on_day(
                    day_from + timedelta(days=day))
                if working_hours_on_day:
                    rec.hours_scheduled += working_hours_on_day

    @api.depends('worked_days_line_ids')
    def _compute_hours_worked(self):
        for rec in self:
            total_hrs = 0.0
            for line in rec.worked_days_line_ids:
                total_hrs += line.number_of_hours
            rec.hours_worked = total_hrs

    @api.depends('hours_scheduled', 'hours_worked')
    def _compute_hours_saldo(self):
        for rec in self:
            rec.hours_saldo = rec.hours_worked - rec.hours_scheduled

    @api.multi
    def action_compensateOvetime(self):
        for rec in self:
            a_acc = rec.contract_id.overtime_analytic
            if not a_acc:
                raise UserError(
                    'No overtime analytic account set on contract!')
            if not a_acc.salary_code:
                raise UserError(
                    'No salary code set on overtime analytic account!')

            w_line = self.env['hr.payslip.worked_days'].create({
                'name': 'Overtime Compensation',
                'payslip_id': rec.id,
                'sequence': 100,
                'code': a_acc.salary_code,
                'number_of_days': (-1) * round(rec.hours_saldo/8, 0),
                'number_of_hours': (-1) * rec.hours_saldo,
                'contract_id': rec.contract_id.id,
            })

    @api.multi
    def action_payslip_done(self):
        for rec in self:
            user_id = rec.contract_id.employee_id.user_id

            a_acc = rec.contract_id.overtime_analytic
            if not a_acc:
                raise UserError(
                    'No overtime analytic account set on contract!')
            if not a_acc.salary_code:
                raise UserError(
                    'No salary code set on overtime analytic account!')

            for w_line in rec.worked_days_line_ids:
                # 1. check if there is OVRT_COMP
                # line and make analytic entry
                if w_line.code == a_acc.salary_code:
                    date_curr_month = rec.date_from
                    a_entry = self.env['account.analytic.line'].create({
                        'account_id': a_acc.id,
                        'user_id': user_id.id,
                        'company_id': user_id.company_id.id,
                        'unit_amount': w_line.number_of_hours,
                        'date': date_curr_month,
                        'name': 'Overtime Compensation (Paid)',
                    })

            # 2. check if there is hours_saldo
            # and make analytic entry nexth month
            if rec.hours_saldo > 0:
                month_name = fields.Datetime.from_string(
                    rec.date_from).strftime('%B %Y')
                date_to = fields.Datetime.from_string(rec.date_to)
                date_to += timedelta(days=1)
                date_next_month = date_to.strftime('%Y-%m-%d')
                a_entry = self.env['account.analytic.line'].create({
                    'account_id': a_acc.id,
                    'user_id': user_id.id,
                    'company_id': user_id.company_id.id,
                    'unit_amount': rec.hours_saldo,
                    'date': date_next_month,
                    'name': 'Overtime moved from ' + month_name,
                })

            rec.compute_sheet()
            return rec.write({'state': 'done'})

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
            a_acc = contract.overtime_analytic
            if not a_acc:
                raise UserError(
                    'No overtime analytic account set on contract!')
            if not a_acc.salary_code:
                raise UserError(
                    'No salary code set on overtime analytic account!')
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
                LEFT JOIN hr_timesheet_sheet_sheet s
                    ON l.sheet_id = s.id
            WHERE
                l.date >= '{}'
                AND l.date <= '{}'
                AND l.user_id = {}
                AND l.company_id = {}
                AND (s.state = '{}'
                OR a.salary_code = '{}')
            GROUP BY
                l.date, l.account_id, a.salary_code
            ORDER BY
                l.date;
            """.format(
                date_from,
                date_to,
                contract.employee_id.user_id.id,
                contract.employee_id.user_id.company_id.id,
                'draft' if DBG else 'done',
                a_acc.salary_code)
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
                # print '{} {} {} {}'.format(
                #     l['date'], l['amt'], l['account_id'], l['salary_code'])
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
                            'sequence': l['account_id'],
                            'code': l['salary_code'],
                            'number_of_days': 1,
                            'number_of_hours': l['amt'],
                            'contract_id': contract.id,
                        })
            res.append(attendances)
        return res
