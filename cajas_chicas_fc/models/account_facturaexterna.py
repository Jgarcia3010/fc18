# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

class AccountFacturaExterna(models.Model):
    _name = "account.facturaexterna"
    _description = "Facturas de caja chica"

    purchase_order_id = fields.Many2one('purchase.order', string='Pedido de compra',
                              index=True, required=False, readonly=True,
                              auto_join=True, ondelete="cascade")
    move_id = fields.Many2one('account.move', string='Compra',
                              index=True, required=False, readonly=True,
                              auto_join=True, ondelete="cascade")
    company_id = fields.Many2one(
        string='Company', store=True, readonly=True,
        related='move_id.company_id', change_default=True, default=lambda self: self.env.company)
    proveedor = fields.Many2one('res.partner',
            readonly=False,
            states={'draft': [('readonly', False)]},
            check_company=True,
            string='Proveedor')
    serie = fields.Char(string="Serie de factura", required=True)
    factura = fields.Char(string="No. de factura", required=True)
    name = fields.Char(compute='_compute_name', readonly=True)
    fecha = fields.Date(required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  readonly=True,
                                  default=lambda self: self.env.company.currency_id)
    fiscal_position_id = fields.Many2one(
            'account.fiscal.position',
            string='Fiscal Position',
            readonly=False,
            check_company=True,
            domain="[('company_id', '=', company_id)]", ondelete="restrict",
            help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices. "
             "The default value comes from the customer."
    )


    @api.onchange('proveedor')
    def _onchange_partner_id(self):
        self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(
            self.proveedor.id)

    # @api.constrains('serie', 'factura')
    # def _validate_unique_id(self):
    #     if len(self._ids) != 1:
    #         return
    #     if not self.serie or not self.factura:
    #             return
    #     if (len(self.serie) + len(self.factura)) == 0:
    #         return

    #     found_records = self.search([('serie','=',self.serie), ('factura', '=', self.factura), ('id','!=', self.id)])
    #     logging.info('DEBUG DEBUG DEBUG ' + str(len(found_records)) + ' ' + str(found_records))
    #     if len(found_records) > 0:
    #         raise ValidationError('Número de factura duplicado. Se encontró la factura ' + self.serie + '-' + self.factura + ((' en la factura de caja chica ' + found_records[0].move_id.name) if (found_records[0].move_id and found_records[0].move_id.name) else ''))

    #     if 'x_studio_serie' in self.env['account.move']._fields:
    #         found_records = self.env['account.move'].search([('x_studio_serie','=',self.serie), ('ref', '=', self.factura)])
    #         if len(found_records) > 0:
    #             raise ValidationError('Número de factura duplicado. Se encontró la factura ' + self.serie + '-' + self.factura + (' con el nombre: ' + found_records.name if found_records.name else '') )
    
    @api.model
    def create(self, values):
        params_cch = [
            ('serie','=',values['serie']),
            ('factura', '=', values['factura'])
        ]
        params_fact = [
            ('x_studio_serie','=',values['serie']),
            ('ref', '=', values['factura'])
        ]

        existing_record_cch = self.env['account.facturaexterna'].search(params_cch)
        if len(existing_record_cch) > 0:
            raise ValidationError('Número de factura duplicado. Se encontró la factura ' + values['serie'] + '-' + values['factura'] + \
            ((' en la factura de caja chica ' + existing_record_cch[0].move_id.name) if (existing_record_cch[0].move_id and existing_record_cch[0].move_id.name) else ''))

        existing_record_fact = self.env['account.move'].search(params_fact)
        if len(existing_record_fact) > 0:
            raise ValidationError('Número de factura duplicado. Se encontró la factura ' + self.serie + '-' + self.factura + \
            (' con el nombre: ' + existing_record_fact[0].name))
        res = super(AccountFacturaExterna, self).create(values)
        return res

    def _compute_name(self):
        for record in self:
            record.name = record.serie + " - " + record.factura
