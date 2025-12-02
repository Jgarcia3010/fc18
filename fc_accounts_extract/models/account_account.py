# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccountAccount(models.Model):
    _inherit = "account.account"

    account_behavior  = fields.Selection(
        string='Comportamiento de la cuenta',
        selection=[
            ('plus_credit_minus_debit', 'Crédito suma, débito resta'),
            ('plus_debit_minus_credit', 'Débito suma, crédito resta')
        ]
    )