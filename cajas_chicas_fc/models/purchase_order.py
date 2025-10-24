# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    caja_chica = fields.Boolean(default=False, string="Compra de caja chica")
    facturasexternas = fields.One2many(
              'account.facturaexterna', 'purchase_order_id',
              string='Facturas de caja chica',
              readonly=False, required=False)

    def _prepare_invoice(self):
        prepared_data = super()._prepare_invoice()
        prepared_data["caja_chica"] = self.caja_chica

        return prepared_data

    def action_create_invoice(self):
        returnvalue = super().action_create_invoice()

        for order in self:
            if order.invoice_ids is not None:
                for invoice in order.invoice_ids:
                    cuenta = order.x_studio_cuenta_analitica
                    invoice.write({
                        "x_studio_cuenta_analitica": cuenta
                    })
                facturasx = order.facturasexternas
                if facturasx is not None:
                    for f in facturasx:
                        f.write({
                            "move_id": invoice.id
                        })
        return returnvalue


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    facturaexterna = fields.Many2one('account.facturaexterna',
                                     string='Factura',
                                     required=False, readonly=False,
                                     ondelete="set null")

    def _prepare_account_move_line(self, move=False):
        prepared_data = super()._prepare_account_move_line(move)
        if self.facturaexterna:
            prepared_data["facturaexterna"] = self.facturaexterna.id

        return prepared_data
