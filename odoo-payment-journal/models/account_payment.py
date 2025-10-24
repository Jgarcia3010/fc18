from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_journal_id = fields.Many2one(
        string="Diario de pagos",
        comodel_name="payment.journal",
        ondelete="restrict"
    )