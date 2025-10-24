{
    'name': "Extracto de cuentas",

    'summary': """Extracto de cuentas contables""",

    'description': """Balance de una cuenta contable seleccionada, en un periodo específico""",

    'author': "Droide",
    'category': 'account',
    'version': '14.0',

    'depends': ['base', 'account', 'account_accountant'],

    'data': [
        #SECURITY
        'security/ir.model.access.csv',
        #VIEWS
        #REPORTS
        #WIZARD
        'wizard/account_extract_views.xml',
    ],
    'demo': [],
}
