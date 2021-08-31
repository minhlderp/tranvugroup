from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    phone = fields.Char(related='partner_id.phone', store=True, readonly=1)
    email = fields.Char(related='partner_id.email', store=True, readonly=1)
    tag = fields.Char(related='partner_id.tag', string='Tag', store=True, readonly=1)
    partner_create_date = fields.Datetime('Partner Created on', related='partner_id.create_date', store=True,
                                          readonly=1)
    partner_create_uid = fields.Many2one('res.users', 'Partner Created by', related='partner_id.create_uid', store=True,
                                         readonly=1)
    partner_write_date = fields.Datetime('Partner Last Updated on', related='partner_id.write_date', store=True,
                                         readonly=1)
    partner_write_uid = fields.Many2one('res.users', 'Partner Last Contributor', related='partner_id.write_uid',
                                        store=True, readonly=1)
    city = fields.Char(related='partner_id.city', store=True, readonly=1)
    country_id = fields.Many2one(related='partner_id.country_id', store=True, readonly=1, comodel_name='res.country',
                                 string='Country', ondelete='restrict')
    website = fields.Char(related='partner_id.website', store=True, readonly=1, string='Website Link')
    function = fields.Char(related='partner_id.function', store=True, readonly=1, string='Job Position')

    mautic_point = fields.Integer(related='partner_id.mautic_point', string='Mautic Point', store=True, readonly=1)
    mautic_last_active = fields.Datetime(related='partner_id.mautic_last_active', string='Mautic Last Active',
                                        store=True, readonly=1)
    mautic_hot = fields.Char(related='partner_id.mautic_hot', string='Mautic Hot', store=True, readonly=1)
    mautic_stage = fields.Char(related='partner_id.mautic_stage', string='Mautic Stage', store=True, readonly=1)
    mautic_link = fields.Char(related='partner_id.mautic_link', string='Mautic Link', store=True, readonly=1)
    mautic_contact_owner = fields.Char(related='partner_id.mautic_contact_owner', string='Mautic Contact Owner',
                                       store=True, readonly=1)
    mautic_event_name = fields.Char(related='partner_id.mautic_event_name', string='Mautic Event Name', store=True,
                                    readonly=1)
    mautic_event_type = fields.Char(related='partner_id.mautic_event_type', string='Mautic Event Type', store=True,
                                    readonly=1)
    mautic_event_time = fields.Datetime(related='partner_id.mautic_event_time', string='Mautic Event Time', store=True,
                                        readonly=1)
    mautic_last_email_open = fields.Datetime(related='partner_id.mautic_last_email_open',
                                             string='Mautic Last Email Open Event', store=True, readonly=1)
    mautic_last_email = fields.Char(related='partner_id.mautic_last_email', string='Mautic Last Email Name', store=True,
                                    readonly=1)
    mautic_last_form_submit = fields.Datetime(related='partner_id.mautic_last_form_submit',
                                              string='Mautic Last From Submit', store=True, readonly=1)
    mautic_last_form = fields.Char(related='partner_id.mautic_last_form', string='Mautic Last Form Name', store=True,
                                   readonly=1)
    mautic_last_page_hit = fields.Datetime(related='partner_id.mautic_last_page_hit', string='Mautic Last Page Hit',
                                           store=True, readonly=1)
    mautic_last_page = fields.Char(related='partner_id.mautic_last_page', string='Mautic Last Page Name', store=True,
                                   readonly=1)
    mautic_note = fields.Text(related='partner_id.mautic_note', string='Mautic Last Page Name', store=True, readonly=1)
    mautic_id = fields.Integer(related='partner_id.mautic_id', string='Mautic ID', store=True, readonly=1)
    nps_1 = fields.Integer(related='partner_id.nps_1', string='Mautic NPS 1', store=True, readonly=1)
    khao_sat_nps_1 = fields.Char(related='partner_id.khao_sat_nps_1', string='Mautic Khao Sat NPS 1', store=True, readonly=1)
    nps_2 = fields.Integer(related='partner_id.nps_2', string='Mautic NPS 2', store=True, readonly=1)
    khao_sat_nps_2 = fields.Char(related='partner_id.khao_sat_nps_2', string='Mautic Khao Sat NPS 2', store=True, readonly=1)
