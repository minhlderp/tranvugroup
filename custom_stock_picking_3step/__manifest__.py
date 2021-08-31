# -*- coding: utf-8 -*-
{
    'name': 'custom_stock_picking_3step',
    'version': '13.0',
    'author': 'Tân lê',
    'company': 'Tân lê',
    'maintainer': 'Tân lê',
    'images': ['static/description/banner.png'],
    'depends': ['stock'],
    'data': [
                'security/step_security.xml',
                'views/stock_picking_views.xml',
            ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

