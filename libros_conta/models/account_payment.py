from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = "account.payment"

    check_number = fields.Char(string="Número de Cheque")