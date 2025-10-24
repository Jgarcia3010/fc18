# -*- coding: utf-8 -*-
{
    'name': 'Imprimir Cheques (FC)',
    'version': '1.0',
    'category': 'Accounting/Localizations/Check',
    'summary': 'Imprimir cheques',
    'description': """""",
    'website': '',
    'depends' : ['account_check_printing'],
    'data': [
        'data/fc_check_printing.xml',
        'report/print_check.xml',
        'report/print_check_3.xml',
        'report/print_check_fc.xml',
        'report/print_check_fc_3.xml',
        'views/account_payment_views.xml'
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
