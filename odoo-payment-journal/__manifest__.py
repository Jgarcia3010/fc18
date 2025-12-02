{
    'name': "Odoo Payment Journal",
    'summary': """Odoo Payment Journal""",
    'description': """Asign payments to supplier invoices from a single window""",
    'author': "Droide",
    'category': 'account',
    'version': '18.0',
    'depends': ['base', 'account', 'account_accountant','account_check_printing'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_payment_views.xml',
        'views/payment_journal_views.xml',
    ],
    'demo': [],
}