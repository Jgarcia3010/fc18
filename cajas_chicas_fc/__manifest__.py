# -*- coding: utf-8 -*-
{
    'name': 'Cajas Chicas (FC)',
    'version': '1.2.1',
    'category': 'Accounting',
    'summary': 'Cajas chicas',
    'description': """ Cajas chicas para FC """,
    'website': '',
    'depends': ['account', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'auto_install': False,
}