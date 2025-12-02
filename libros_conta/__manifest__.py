# -*- coding: utf-8 -*-
{
    'name': "Libros Contabilidad FC",
    'version': '18.1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Libros de contabilidad para FC',
    'author': "Guillermo",
    'description': 'Módulo para reportes de libros de compras y ventas',
    'website': "http://www.guilles.website",
    
    'depends': ['base', 'account', 'purchase', 'product'], 

    'data': [
        'security/ir.model.access.csv',
        'reports/reports_view.xml',
        'views/libros_templates.xml',
        'data/libros.xml',
        'wizards/extractos_de_cuentas.xml',
        'wizards/pagos.xml',
        'views/products.xml',
        'views/partner.xml',
        'views/account_views.xml',
        'views/account_journal_views.xml',
        'views/account_payment_views.xml',
        'views/bank_account.xml',
    ],

    'assets': {
        'web.assets_backend': [
            # NOTA LAS NUEVAS RUTAS CON /src/
            'libros_conta/static/src/xml/libros.xml',
            'libros_conta/static/src/js/libros.js',
        ],
    },

    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}