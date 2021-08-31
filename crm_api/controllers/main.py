import json
from odoo import http
from odoo.http import request


class Main(http.Controller):
    @http.route('/web/contact/sync', type='json', methods=['POST'], auth="user", csrf=False)
    def contact_sync(self, data):
        """
        kwargs: dictionary contains key:value (key is res.partner field name)
        """
        list_id = []
        for vals in data:
            email = vals.get('email', False)
            if email:
                res_partner_obj = request.env['res.partner']
                partner = res_partner_obj.search([('email', '=', email)], limit=1)
                if partner:
                    partner.with_context(from_dw=True).write(vals)
                else:
                    partner = res_partner_obj.with_context(from_dw=True).create(vals)
                list_id.append(partner.id)
        return json.dumps({'ids': list_id})

    @http.route('/web/crm/create', type='json', methods=['POST'], auth="user", csrf=False)
    def crm_create(self, data):
        """
        kwargs: dictionary contains key:value (key is crm.lead field name)
        """
        list_id = []
        for vals in data:
            record = request.env['crm.lead'].with_context(from_dw=True).create(vals)
            list_id.append(record.id)
        return json.dumps({'ids': list_id})

    @http.route('/web/crm/update', type='json', methods=['POST'], auth="user", csrf=False)
    def crm_update(self, crm_ids, **kwargs):
        """
        crm_ids: list id crm to update data
        kwargs: dictionary contains key:value (key is crm.lead field name)
        """
        res = request.env['crm.lead'].browse(crm_ids).with_context(from_dw=True).write(kwargs)
        return res

    @http.route('/web/crm/list', type='json', methods=['POST'], auth="user", csrf=False)
    def crm_list(self, domain=None, fields=None, offset=0, limit=None, order=None):
        """
        crm_ids: list id crm to update data
        kwargs: dictionary contains key:value (key is crm.lead field name)
        """
        res = request.env['crm.lead'].search_read(domain, fields, offset=offset, limit=limit, order=order)
        return res
