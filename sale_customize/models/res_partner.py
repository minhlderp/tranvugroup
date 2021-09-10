from odoo import fields, models, api
from odoo.exceptions import ValidationError


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

    is_duplicate_phone = fields.Boolean(default=False, compute='_get_is_duplicate_phone', search='_search_is_duplicate_phone')
    is_duplicate_email = fields.Boolean(default=False, compute='_get_is_duplicate_email', search='_search_is_duplicate_email')

    @api.model
    def _search_is_duplicate_phone(self, operator, value):
        partners = self.search([])
        potential_dupplicates = []
        for partner in partners:
            if partner.is_duplicate_phone:
                potential_dupplicates.append(partner.id)
        return [('id', 'in', potential_dupplicates)]

    @api.model
    def _search_is_duplicate_email(self, operator, value):
        partners = self.search([])
        potential_dupplicates = []
        for partner in partners:
            if partner.is_duplicate_email:
                potential_dupplicates.append(partner.id)
        return [('id', 'in', potential_dupplicates)]

    def _get_is_duplicate_phone(self):
        for partner in self:
            exist_phone = exist_mobile = False
            if partner.phone:
                exist_phone = self.search([('phone', 'in', [partner.phone, partner.phone.strip()]), ('id', '!=', partner.id)], limit=1)
            if partner.mobile:
                exist_mobile = self.search([('phone', 'in', [partner.mobile, partner.mobile.strip()]), ('id', '!=', partner.id)], limit=1)
            if exist_phone or exist_mobile:
                partner.is_duplicate_phone = True
            else:
                partner.is_duplicate_phone = False

    def _get_is_duplicate_email(self):
        for partner in self:
            exist_email = False
            if partner.email:
                exist = self.search([('email', 'in', [partner.email, partner.email.strip()]), ('id', '!=', partner.id)], limit=1)
                if exist:
                    exist_email = True
            partner.is_duplicate_email = exist_email

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

    # @api.constrains('phone', 'mobile')
    # def check_duplicate_phone_mobile(self):
    #     for partner in self:
    #         if partner.phone:
    #             if partner.phone.index('+84') > -1:
    #                 raise ValidationError('Please change phone number from +84 to 0...')
    #             exist = self.search([('phone', 'in', [partner.phone, partner.phone.strip()]), ('id', '!=', partner.id)], limit=1)
    #             if exist:
    #                 raise ValidationError('The phone number already exist in the system')
    #         if partner.mobile:
    #             if partner.mobile.index('+84') > -1:
    #                 raise ValidationError('Please change mobile number from +84 to 0...')
    #             exist = self.search([('phone', 'in', [partner.mobile, partner.mobile.strip()]), ('id', '!=', partner.id)], limit=1)
    #             if exist:
    #                 raise ValidationError('The mobile number already exist in the system')

    @api.constrains('email')
    def check_duplicate_email(self):
        for partner in self:
            if partner.email:
                exist = self.search([('email', 'in', [partner.email, partner.email.strip()]), ('id', '!=', partner.id)], limit=1)
                if exist:
                    raise ValidationError('The email already exist in the system')
