# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=False):
        for rec in self:
            if rec.move_type == 'out_invoice':
                duplicated_ref = self.env['account.move'].search_read([
                    ('payment_reference', '=', rec.payment_reference)
                ],
                limit=2,
                order='invoice_date asc')
                
                if len(duplicated_ref) == 2:
                    customer = duplicated_ref[0]['partner_id'][1]
                    payment_reference = duplicated_ref[0]['payment_reference']
                    invoice_date = duplicated_ref[0]['invoice_date']
                    err = 'Referencia de cliente duplicada detectada. Probablemente registró dos veces la misma factura / factura rectificativa del cliente: %s - %s - %s'%(customer, payment_reference, invoice_date)
                    raise UserError(err)

        return super(AccountMove,self)._post(soft)
    