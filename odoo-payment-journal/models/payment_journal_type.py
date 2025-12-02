from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class PaymentJournalType(models.Model):
    _name = 'payment.journal.type'
    _description = 'Tipo de diario de pagos'

    name = fields.Char(
        string="Tipo"
    )
    