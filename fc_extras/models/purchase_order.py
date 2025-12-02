# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date
from odoo.tools.float_utils import float_is_zero

import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    amount_total = fields.Monetary(tracking=True)
    amount_untaxed = fields.Monetary(tracking=True)
    partner_ref = fields.Char(tracking=True)
    
    # Campo de cuenta analítica actualizado para Odoo 18
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Cuenta Analítica',
        tracking=True,
        check_company=True,
        copy=True,
    )
    
    currency_id = fields.Many2one(tracking=True)
    date_order = fields.Datetime(tracking=True)
    date_planned = fields.Datetime(tracking=True)
    user_id = fields.Many2one(tracking=True)
    payment_term_id = fields.Many2one(tracking=True)
    fiscal_position_id = fields.Many2one(tracking=True)
    po_invoice_ids = fields.Many2many(
        comodel_name='account.move',
        compute='_compute_po_invoice_ids'
    )

    def _compute_po_invoice_ids(self):
        for rec in self:
            rec.po_invoice_ids = rec.mapped('order_line.invoice_lines.move_id')

    @api.depends('state', 'order_line.qty_to_invoice', 'order_line.invoice_lines.move_id.state', 'po_invoice_ids')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.invoice_status = 'no'
                continue

            ###
            move_ids = order.po_invoice_ids.filtered(lambda x: x.state != 'cancel')
            qty = 0.00
            qty_nc = 0.00
            for move_id in move_ids:
                if move_id.move_type == 'in_invoice':
                    qty += move_id.amount_total
                elif move_id.move_type == 'in_refund':
                    qty_nc += move_id.amount_total
            _logger.info(qty)
            _logger.info(qty_nc)
            if qty_nc > 0:
                if qty_nc < qty:
                    order.invoice_status = 'invoiced'
                else:
                    order.invoice_status = 'to invoice'
            else:
            ###
                if any(
                    not float_is_zero(line.qty_to_invoice, precision_digits=precision)
                    for line in order.order_line.filtered(lambda l: not l.display_type)
                ):
                    order.invoice_status = 'to invoice'
                elif (
                    all(
                        float_is_zero(line.qty_to_invoice, precision_digits=precision)
                        for line in order.order_line.filtered(lambda l: not l.display_type)
                    )
                    and order.invoice_ids
                ):
                    order.invoice_status = 'invoiced'
                else:
                    order.invoice_status = 'no'

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    #qty_invoiced = fields.Float(compute='_compute_qty_invoiced_2', string="Billed Qty", digits='Product Unit of Measure', store=True)
    #qty_to_invoice = fields.Float(compute='_compute_qty_invoiced', string='To Invoice Quantity', store=True, readonly=True, digits='Product Unit of Measure')


    #https://github.com/odoo/odoo/blob/14.0/addons/purchase/models/purchase.py#L904
    # @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_received', 'product_uom_qty', 'order_id.state')
    # def _compute_qty_invoiced(self):
    #     for line in self:
    #         # compute qty_invoiced
    #         qty = 0.0
    #         for inv_line in line.invoice_lines:
    #             if inv_line.move_id.state not in ['cancel']:
    #                 if inv_line.move_id.move_type == 'in_invoice':
    #                     qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
    #                 elif inv_line.move_id.move_type == 'in_refund':
    #                     qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom)
    #         line.qty_invoiced = qty

    #         # compute qty_to_invoice
    #         if line.order_id.state in ['purchase', 'done']:
    #             if line.product_id.purchase_method == 'purchase':
    #                 line.qty_to_invoice = line.product_qty - line.qty_invoiced
    #             else:
    #                 line.qty_to_invoice = line.qty_received - line.qty_invoiced
    #         else:
    #             line.qty_to_invoice = 0