# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'CRM api addon',
    'version': '1.1',
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
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
