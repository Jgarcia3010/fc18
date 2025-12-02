{
    'name': "FC Extras",

    'summary': """Extra functionalities for FC""",

    'description': """1. Analytic account blocking\n""",

    'author': "Droide",
    'category': 'account',
    'version': '14.0',

    'depends': ['base', 'analytic', 'account', 'purchase'],

    'data': [
        #SECURITY
        'security/security.xml',
        'security/ir.model.access.csv',
        #VIEWS
        'views/account_move_views.xml',
        'views/analytic_account_views.xml',
        'views/purchase_order_views.xml',
        #REPORTS
        'report/report_purchaseorder_document_inherit.xml',
    ],
    'demo': [],
}
