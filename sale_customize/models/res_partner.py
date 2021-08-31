from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tag = fields.Char(string='Tag')
    odoo_contact_link = fields.Char(string='Odoo Contact Link', compute='_get_odoo_contact_link')

    mautic_point = fields.Integer(string='Mautic Point')
    mautic_last_active = fields.Datetime(string='Mautic Last Active')
    mautic_hot = fields.Char(string='Mautic Hot')
    mautic_stage = fields.Char(string='Mautic Stage')
    mautic_link = fields.Char(string='Mautic Link')
    mautic_contact_owner = fields.Char(string='Mautic Contact Owner')
    mautic_event_name = fields.Char(string='Mautic Event Name')
    mautic_event_type = fields.Char(string='Mautic Event Type')
    mautic_event_time = fields.Datetime(string='Mautic Event Time')
    mautic_last_email_open = fields.Datetime(string='Mautic Last Email Open Event')
    mautic_last_email = fields.Char(string='Mautic Last Email Name')
    mautic_last_form_submit = fields.Datetime(string='Mautic Last From Submit')
    mautic_last_form = fields.Char(string='Mautic Last Form Name')
    mautic_last_page_hit = fields.Datetime(string='Mautic Last Page Hit')
    mautic_last_page = fields.Char(string='Mautic Last Page Name')
    mautic_note = fields.Text(string='Mautic Note')
    mautic_id = fields.Integer(string='Mautic ID')
    nps_1 = fields.Integer(string='Mautic NPS 1')
    khao_sat_nps_1 = fields.Char(string='Mautic Khao Sat NPS 1')
    nps_2 = fields.Integer(string='Mautic NPS 2')
    khao_sat_nps_2 = fields.Char(string='Mautic Khao Sat NPS 2')

    def _get_odoo_contact_link(self):
        for partner in self:
            action_id = self.env.ref('account.res_partner_action_customer').id
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            partner_id = partner.id
            partner.odoo_contact_link = f'{base_url}/web#action={action_id}&id={partner_id}&model=res.partner&view_type=form'

    @api.model
    def convert_phone(self):
        res_partners = self.env['res.partner'].search([
            '|', ('phone', 'like', '+84'),
            ('mobile', 'like', '+84')
        ])
        for partner in res_partners:
            vals = {}
            if partner.phone:
                vals['phone'] = partner.phone.replace('+84', '0')
            if partner.mobile:
                vals['mobile'] = partner.mobile.replace('+84', '0')
            partner.with_context(from_dw=True).write(vals)
