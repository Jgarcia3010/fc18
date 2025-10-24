# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

class AccountMove(models.Model):
    _inherit = "account.move"
    
    caja_chica = fields.Boolean(default=False, string="Compra de caja chica")
    facturasexternas = fields.One2many(
              'account.facturaexterna', 'move_id',
              string='Facturas de caja chica',
              readonly=False, required=False)

    def write(self, vals):
        """
          Custom fields in account.move.line are lost with the current way in which invoice lines are validated and then stored
        """
        if "invoice_line_ids" in vals and "line_ids" in vals:
            idToIndex = dict([(line[1], i) for i, line in enumerate(vals["line_ids"]) ] )
            logging.info(str(vals))
            logging.info(str(idToIndex))
            for line in vals["invoice_line_ids"]:
                if isinstance(line[2], dict) and "facturaexterna" in line[2] and \
                    line[1] in idToIndex:
                    vals["line_ids"][ idToIndex[ line[1] ] ][2]["facturaexterna"] = line[2]["facturaexterna"]

        return super().write(vals)


    @api.constrains('ref')
    def _validate_unique_id(self):
        if len(self._ids) != 1:
            return

        if 'x_studio_serie' in self.env['account.move']._fields:
            if not self.x_studio_serie or not self.ref:
                return
            if (len(self.x_studio_serie) + len(self.ref)) == 0:
                return

            found_records = self.search([('x_studio_serie','=',self.x_studio_serie), ('ref', '=', self.ref), ('id', '!=', self.id)])
            if len(found_records) > 0:
                raise ValidationError(f'Número de factura duplicado. Se encontró la factura con serie "{self.x_studio_serie}", y número "{self.ref}"' + (f' con el nombre: {found_records.name}' if found_records.name else '') )

            found_records = self.env['account.facturaexterna'].search([('serie','=',self.x_studio_serie), ('factura', '=', self.ref)])
            if len(found_records) > 0:
                raise ValidationError(f'Número de factura duplicado. Se encontró la factura {self.x_studio_serie}-{self.ref} en la factura de caja chica {found_records[0].move_id.name}')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    facturaexterna = fields.Many2one('account.facturaexterna',
                                     string='Factura',
                                     required=False, readonly=False,
                                     ondelete="set null")
