# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging


class AccountFacturaExterna(models.Model):
    _inherit = "account.facturaexterna"

    tax_withholding_isr = fields.Selection(
        [
            ('quarter_witholding', 'Sujeto a Pagos Trimestrales'),
            ('definitive_withholding', 'Sujeto a Retención Definitiva'),
            ('small_taxpayer_withholding', 'Pequeño Contribuyente')
        ], string="Régimen tributario"
    )

    @api.onchange('proveedor')
    def _onchange_partner_id(self):
        self.tax_withholding_isr = self.proveedor.tax_withholding_isr