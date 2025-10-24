# -*- coding: utf-8 -*-
{
    'name': "Reportes para FC",
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Reporte financieros',
    'author': "Guillermo Ambrosio",
    'description': '',
    'website': "https://www.guilles.website",
    'depends': ['account', 'purchase'],
    'data': [
        'reports/proyectos.xml',
        'views/products.xml',
        'views/payments.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': True
}
