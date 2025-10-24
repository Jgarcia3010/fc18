from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class PaymentLine(models.Model):
    _name = 'payment.line'
    _description = 'Línea de diario de pagos'

    payment_journal_id = fields.Many2one(
        ondelete="restrict",
        comodel_name="payment.journal",
        string="Línea de pago"
    )
    partner_id = fields.Many2one(
        ondelete="restrict",
        comodel_name='res.partner',
        string='Proveedor',
        domain="[('supplier_rank', '>', 0)]",
        required=True
    )
    journal_id = fields.Many2one(
        ondelete="restrict",
        comodel_name='account.journal',
        string='Diario',
        domain="[('type', 'in', ('bank', 'cash'))]",
        required=True
    )
    available_payment_method_ids = fields.Many2one(
        ondelete="restrict",
        string="Método de pago",
        comodel_name="account.payment.method",
        domain="[('payment_type', '=', 'outbound')]"
    )
    payment_method_code = fields.Char(related='available_payment_method_ids.code')
    analytic_account_id = fields.Many2one(
        ondelete="restrict",
        comodel_name='account.analytic.account',
        string='Cuenta analítica'
    )
    partner_bank_id = fields.Many2one(
        ondelete="restrict",
        comodel_name='res.partner.bank',
        string='Cuenta bancaria beneficiaria',
        domain="[('partner_id', '=', partner_id)]"
    )
    is_non_negociable = fields.Boolean(
        string = "No negociable"
    )
    is_down_payment = fields.Boolean(
        string = "Pago anticipado"
    )
    motive = fields.Char(
        string="Motivo"
    )
    ref = fields.Char(
        string="Circular"
    )

    invoice_ids = fields.Many2many(
        comodel_name='account.move',
        string='Factura'
    )

    invoices_total = fields.Float(
        string='Importe adeudado',
        compute='_compute_invoices_total'
    )
    amount_total = fields.Float(
        string='Total de línea',
        compute='_compute_invoices_total'
    )
    next_check_number = fields.Char(
        string='No. cheque',
        compute='_compute_next_check_number'
    )
    payment_id = fields.Many2one(
        comodel_name='account.payment'
    )
    amount_to_pay = fields.Float(
        string='Monto a pagar',
        help='Si es distinto de Q0.00, será el pago que se aplicará a la factura de la línea de pago'
    )
    amount_paid = fields.Float(
        string='Monto pagado',
        compute='_compute_amount_paid'
    )

    def _compute_next_check_number(self):
        for rec in self:
            if not rec.payment_id:
                rec.next_check_number = 'Sin asignar'
            else:
                rec.next_check_number = rec.payment_id.check_number

    @api.depends('invoice_ids')
    def _compute_invoices_total(self):
        for rec in self:
            rec.invoices_total = 0
            rec.amount_total = 0
            for invoice in rec.invoice_ids:
                rec.invoices_total += invoice.amount_residual
                rec.amount_total += invoice.amount_total

    @api.depends('payment_id')
    def _compute_amount_paid(self):
        for rec in self:
            if rec.payment_id:
                rec.amount_paid = rec.payment_id.amount
            else:
                rec.amount_paid = 0.00

    @api.onchange('partner_id')
    def _onchange_partner_id_domain(self):
        if self.partner_id:
            payment_journal = self.payment_journal_id
            invoice_ids = []
            if payment_journal and payment_journal.payment_lines:
                for line in payment_journal.payment_lines:
                    if line.partner_id.id == self.partner_id.id and line.id != self.id:
                        invoice_ids += line.invoice_ids.ids
            
            domain = [
                ("partner_id", "=", self.partner_id.id),
                ("state", "=", "posted"),
                ("payment_state", "in", ["not_paid", "partial"]),
                ("move_type", "=", "in_invoice")
            ]
            
            if invoice_ids:
                domain.append(("id", 'not in', invoice_ids))
            
            return {'domain': {'invoice_ids': domain}}
        else:
            return {'domain': {'invoice_ids': [('id', '=', False)]}}