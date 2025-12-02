# -*- coding: utf-8 -*-
{
    'name': "Libros Contabilidad FC",
    'version': '18.1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Libros de contabilidad para FC',
    'author': "Guillermo",
    'description': 'Módulo para reportes de libros de compras y ventas',
    'website': "http://www.guilles.website",
    
   
    'depends': ['base', 'account', 'purchase', 'product', 'odoo-payment-journal'], 

    'data': [
        'security/ir.model.access.csv',
        'views/libros_templates.xml',
        'data/libros.xml',
        'wizards/extractos_de_cuentas.xml',
        'wizards/pagos.xml',
        'views/forms.xml',
        'views/products.xml',
        'views/partner.xml',
        'views/account_views.xml',
        'views/account_journal_views.xml',
        'views/account_payment_views.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'libros_conta/static/libros.xml',
        ],
    },

    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}