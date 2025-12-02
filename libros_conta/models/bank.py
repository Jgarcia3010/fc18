# -*- coding: utf-8 -*-
from odoo import fields, models

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    account_type = fields.Selection([ ('1', '1 - Monetaria'),('2', '2 - Ahorro'),],'Tipo de cuenta', default='1')
