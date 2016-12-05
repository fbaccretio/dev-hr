# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import math
from datetime import timedelta

HOURS_PER_DAY = 8


class HolidaysTypePFT(models.Model):

    _inherit = 'hr.holidays.status'

    holidays_analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Holidays Account',
        help='Post entry here when leaves are approved')


class HolidaysPFT(models.Model):

    _inherit = 'hr.holidays'

    @api.model
    def _get_number_of_hours(self, date_from, date_to, employee_id):
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)

        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            resource = employee.resource_id
            if resource and resource.calendar_id:
                hours = resource.calendar_id.get_working_hours(
                    from_dt,
                    to_dt,
                    resource_id=resource.id,
                    compute_leaves=True)

        time_delta = to_dt - from_dt
        return math.ceil(time_delta.days + float(time_delta.seconds) / 3600)

    @api.multi
    def action_validate(self):
        res = super(HolidaysPFT, self).action_validate()
        if self.type == 'add':
            # allocation request
            return True
        if not self.state == 'validate':
            print 'leave is not validated'
            return True
        if not self.holiday_status_id.holidays_analytic_id:
            print 'no analytic account on leaves type'
            return True
        a_acc = self.holiday_status_id.holidays_analytic_id
        project = self.env['project.project'].search(
                [('analytic_account_id', '=', a_acc.id)], limit=1)
        if not project:
            print 'No project linked to overtime analytic account!'
            return True
        hours_numb = self._get_number_of_hours(
            self.date_from,
            self.date_to,
            self.employee_id.id)
        date = fields.Datetime.from_string(self.date_from)
        count = 0
        while hours_numb > 0:
            hrs = hours_numb if hours_numb <= HOURS_PER_DAY else HOURS_PER_DAY
            print hrs
            date += timedelta(days=count)
            date_entry = date.strftime('%Y-%m-%d')
            a_entry = self.env['account.analytic.line'].create({
                'account_id': a_acc.id,
                'user_id': self.user_id.id,
                'company_id': self.user_id.company_id.id,
                'unit_amount': hrs,
                'date': date_entry,
                'name': self.name + '/' + str(count),
                'project_id': project.id,
            })
            sheets = self.env['hr_timesheet_sheet.sheet'].search(
                [('date_to', '>=', date_entry),
                 ('date_from', '<=', date_entry),
                 ('employee_id.user_id.id', '=', self.user_id.id)])
            if sheets:
                a_entry.sheet_id_computed = sheets[0]
                a_entry.sheet_id = sheets[0]
            count += 1
            hours_numb -= HOURS_PER_DAY
