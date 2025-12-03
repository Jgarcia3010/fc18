# -*- coding: utf-8 -*-
from babel import dates
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import logging


class account_payment(models.Model):
    _inherit = "account.payment"
    es_anticipo = fields.Boolean(string="Pago anticipado")
