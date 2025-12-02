# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = "account.journal"

    journal_usage = fields.Selection(
        selection=[
            ('import','Importación'),
            ('export','Exportación'),
        ],
        string='Tipo de diario'
    )