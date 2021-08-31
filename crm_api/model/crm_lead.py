from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import requests
import json
import logging
_logger = logging.getLogger(__name__)

url = 'http://area.tranvugroup.com:3005/odoo/hook'
headers = {'content-type': 'application/json', 'services-token': '7crVCZZNCSMZP7YZYxtPJNL9ZqKmR2yP'}


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        record = super(CrmLead, self.with_context(from_create=1)).create(vals)
        if not self.env.context.get('from_dw', False):
            data = record.serialize_to_json()
            payload = {'params': data}
            result = requests.post(url, data=json.dumps(payload), headers=headers)
            is_success = False
            message = ''
            if result.status_code == 200:
                if result.text:
                    result_data = json.loads(result.text)['data']
                    message = result.text
                    _logger.info(">>>>>>>>>>>>>>>>>>>>> CALL DW >>>>>>>>>>>>>>>>>>> %s", message)
                    if result_data['createCount'] > 0:
                        is_success = True
            if not is_success:
                raise ValidationError('Call api sync record %s to DW have problem: %s - %s' % (record.id, result.status_code, message))
        return record

    def write(self, vals):
        res = super(CrmLead, self).write(vals)
        if not self.env.context.get('from_dw', False) and not self.env.context.get('from_create', False):
            data = self.serialize_to_json()
            payload = {'params': data}
            result = requests.post(url, data=json.dumps(payload), headers=headers)
            is_success = False
            message = ''
            if result.status_code == 200:
                if result.text:
                    result_data = json.loads(result.text)['data']
                    message = result.text
                    _logger.info(">>>>>>>>>>>>>>>> CALL DW >>>>>>>>>>>>>>>>> %s", message)
                    if result_data['updateCount'] > 0:
                        is_success = True
            if not is_success:
                raise ValidationError('Call api sync records %s to DW have problem: %s - %s' % (self.ids, result.status_code, message))
        return res

    def serialize_to_json(self):
        data = []
        for record in self:
            vals = {}
            for key in record._fields:
                field_type = record._fields[key].type
                if field_type == 'many2one':
                    vals[key] = record[key].id or False
                elif field_type == 'many2many' or field_type == 'one2many':
                    vals[key] = record[key].ids or False
                elif field_type == 'datetime':
                    vals[key] = record[key] and record[key].strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False
                elif field_type == 'date':
                    vals[key] = record[key] and record[key].strftime(DEFAULT_SERVER_DATE_FORMAT) or False
                else:
                    vals[key] = record[key] or False
            data.append(vals)
        return data
