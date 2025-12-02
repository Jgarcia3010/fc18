# -*- coding: utf-8 -*-
{
    'name': "Libros Contabilidad FC",
    'version': '18.1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Libros de contabilidad para FC',
    'author': "Guillermo",
    'description': '',
    'website': "http://www.guilles.website",
    'depends': ['account', 'purchase', 'odoo-payment-journal'],
    'data': [
        'reports/reports_view.xml',
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
    'qweb': [
        'static/libros.xml',
    ],
    'installable': True,
    'auto_install': False
}
