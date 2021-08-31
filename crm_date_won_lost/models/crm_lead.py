from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    date_won = fields.Datetime(string='Date Won')
    date_lost = fields.Datetime(string='Date Lost')

    def action_set_won(self):
        res = super(CrmLead, self).action_set_won()
        self.write({'date_won': fields.Datetime.now()})
        return res

    def action_set_lost(self, **additional_values):
        res = super(CrmLead, self).action_set_lost(**additional_values)
        self.write({'date_lost': fields.Datetime.now()})
        return res

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        """
        override function to do not change phone format
        """
        pass
        # if self.phone:
        #     self.phone = self.phone_format(self.phone)
