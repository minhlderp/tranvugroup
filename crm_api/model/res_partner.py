from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import requests
import json
import logging
import base64

_logger = logging.getLogger(__name__)

url = 'https://dev.mautic.tranvugroup.com/api/contacts/new?XDEBUG_SESSION_START=session_name'
# user = 'khoazero123@gmail.com'
# pwd = 'khoazero123@gmail.com'
b64Val = base64.b64encode('thecuongreal@gmail.com:thecuongreal@gmail.com@3'.encode()).decode()
headers = {
    'Authorization': "Basic %s" % b64Val,
    'content-type': 'application/x-www-form-urlencoded'
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        record = super(ResPartner, self.with_context(from_create=1)).create(vals)
        if not self.env.context.get('from_dw', False):
            data = record.serialize_to_json()
            result = requests.post(url, data=data.encode('utf-8'), headers=headers)
            if result.status_code in (200, 201) and result.ok:
                _logger.info(">>>>>>>>>>>>>>>>>>>>> CALL DW >>>>>>>>>>>>>>>>>>> %s", result.text)
            else:
                raise ValidationError(
                    'Call api sync record %s to DW have problem: %s - %s' % (
                        record.id, result.status_code, result.text))
        return record

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if not self.env.context.get('from_dw', False) and not self.env.context.get('from_create', False):
            success_id = []
            for record in self:
                data = record.serialize_to_json()
                result = requests.post(url, data=data.encode('utf-8'), headers=headers)
                if result.ok:
                    _logger.info(">>>>>>>>>>>>>>>>>>>>> CALL DW >>>>>>>>>>>>>>>>>>> %s", result.text)
                    success_id.append(record.id)
                else:
                    raise ValidationError(
                        'Call api sync record %s to DW have problem: %s - %s' % (
                            (list(filter(lambda i: i not in success_id, self.ids))), result.status_code, result.text))
        return res

    @api.model
    def sync_contact_to_mautic(self):
        for partner in self.search([('email', '!=', False), ('email', '!=', '')]):
            if not partner.email:
                continue
            if partner.email and partner.email.strip() == '':
                continue
            try:
                data = partner.serialize_to_json()
                result = requests.post(url, data=data.encode('utf-8'), headers=headers)
                if result.status_code in (200, 201) and result.ok:
                    _logger.info(">>>>>>>>>>>>>>>>>>>>> CALL DW >>>>>>>>>>>>>>>>>>> %s", result.text)
                else:
                    _logger.info(
                        'Call api sync record %s to DW have problem: %s - %s' % (
                            partner.id, result.status_code, result.text))
            except Exception as e:
                _logger.info('====error: ' + partner.id + '===' + str(e))

    def serialize_to_json(self):
        # data = []
        map_fields = {'id': 'odoo_id', 'name': 'firstname', 'user_id': 'odoo_salesperson',
                      'tag': 'odoo_tag', 'function': 'position', 'create_date': 'odoo_create_on',
                      'create_uid': 'odoo_create_by', 'sale_order_count': 'odoo_sales_order',
                      'total_invoiced': 'odoo_total_invoiced', 'country_id': 'odoo_total_invoiced'}
        map_fields_key = map_fields.keys()
        self = self.sudo()
        # for record in self.sudo():
        vals = {}
        for key in self._fields:
            field_type = self._fields[key].type
            if field_type == 'binary' or key == 'email_formatted':
                continue
            if field_type == 'many2one':
                if key in map_fields_key:
                    if key == 'create_uid':
                        vals[map_fields[key]] = self[key].name
                    else:
                        vals[map_fields[key]] = self[key].id or False
                else:
                    vals[key] = self[key].id or False
            elif field_type == 'many2many' or field_type == 'one2many':
                if key in map_fields_key:
                    vals[map_fields[key]] = self[key].ids or False
                else:
                    vals[key] = self[key].ids or False
            elif field_type == 'datetime':
                if key in map_fields_key:
                    vals[map_fields[key]] = self[key] and self[key].strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False
                else:
                    vals[key] = self[key] and self[key].strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False
            elif field_type == 'date':
                if key in map_fields_key:
                    vals[map_fields[key]] = self[key] and self[key].strftime(DEFAULT_SERVER_DATE_FORMAT) or False
                else:
                    vals[key] = self[key] and self[key].strftime(DEFAULT_SERVER_DATE_FORMAT) or False
            elif field_type == 'integer' or field_type == 'monetary' or field_type == 'float':
                if key in map_fields_key:
                    vals[map_fields[key]] = self[key] or 0
                else:
                    vals[key] = self[key] or 0
            else:
                if key in map_fields_key:
                    vals[map_fields[key]] = self[key] or False
                else:
                    vals[key] = self[key] or False
        # data.append(vals)
        result = '&'.join(f'{k}={val}' for k, val in vals.items())
        return result
