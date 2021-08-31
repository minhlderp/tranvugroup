# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'CRM adjust addon',
    'version': '1.1',
    'description': 'Add date win, date lost',
    'summary': 'CRM',
    'sequence': 15,
    'category': 'CRM',
    'website': '',
    'depends': [
        'base',
        'crm',
        'sale',
    ],
    'data': [
        'data/data.xml',
        'views/crm_lead.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
