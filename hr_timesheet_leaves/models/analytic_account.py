# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _


class HTLAccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    use_leaves = fields.Boolean(
        string='Use Leaves',
        default=False)

    leave_type = fields.Many2one(
        comodel_name="hr.holidays.status",
        string='Leave Type',
        domain="[('active', '=', True)]")


class HTLAccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.multi
    def write(self, vals):
        return super(HTLAccountAnalyticLine, self).write(vals)

    @api.model
    def create(self, vals):
        return super(HTLAccountAnalyticLine, self).create(vals)
