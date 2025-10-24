from email.policy import default
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from itertools import groupby

import logging

_logger = logging.getLogger(__name__)

class PaymentJournal(models.Model):
    _name = 'payment.journal'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]
    _description = 'Diario de pagos'

    name = fields.Char(
        string = 'Nombre',
        required = True,
        tracking = True
    )
    date = fields.Date(
        string = 'Fecha de creación',
        default = datetime.today().strftime('%Y-%m-%d'),
        tracking = True
    )
    journal_type = fields.Many2one(
        string = 'Tipo de diario',
        comodel_name='payment.journal.type',
        ondelete='restrict'
    )
    journal_amount = fields.Float(
        string = 'Total',
        compute = '_compute_journal_amount',
        store = True
    )
    journal_amount_total = fields.Float(
        string = 'Total',
        compute = '_compute_journal_amount'
    )
    journal_state = fields.Selection(
        string = 'Estado',
        selection = [
            ('draft','Borrador'),
            ('posted','Contabilizado'),
            ('registered','Registrado'),
            ('cancel','Cancelado')
        ],
        default = 'draft',
        ondelete = 'cascade',
        tracking = True
    )
    payment_lines = fields.One2many(
        comodel_name='payment.line',
        inverse_name='payment_journal_id',
        string='Línea de pago'
    )
    payment_count = fields.Integer(
        compute='_compute_payment_count'
    )
    journal_amount_paid = fields.Float(
        string='Monto pagado',
        compute='_compute_journal_amount_paid'
    )
    @api.depends('payment_lines')
    def _compute_journal_amount_paid(self):
        for rec in self:
            journal_amount_paid = 0.00
            for line in rec.payment_lines:
                journal_amount_paid += line.amount_paid
            rec.journal_amount_paid = journal_amount_paid

    def _compute_payment_count(self):
        for rec in self:
            count = 0
            for line in rec.payment_lines:
                if line.payment_id:
                    count += 1
            rec.payment_count = count
    
    def action_view_payments(self):
        return {
            'name': 'Pagos',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'domain': [('payment_journal_id', '=', self.id)],
            'context': '{"create": False}'
        }

    @api.depends('payment_lines')
    def _compute_journal_amount(self):
        for rec in self:
            rec.journal_amount = 0
            rec.journal_amount_total = 0
            if rec.payment_lines and rec.payment_lines.invoice_ids:
                for invoice in rec.payment_lines.invoice_ids:
                    rec.journal_amount += invoice.amount_residual
                    rec.journal_amount_total += invoice.amount_total
            else:
                rec.journal_amount = 0
                rec.journal_amount_total = 0

    @api.onchange('payment_lines')
    def _onchange_payment_lines(self):
        # reset journal state to draft
        self.journal_state = 'draft'

    def validate_payment_journal(self):
        #nada que hacer
        self.journal_state = 'posted'

    def register_payment_journal(self):
        #agregar pagos y bla bla
        if not self.payment_lines:
            raise ValidationError('Debe ingresar al menos una línea de pago')
        for payment_line in self.payment_lines:
            if payment_line.amount_to_pay > 0 and len(payment_line.invoice_ids) > 1:
                raise UserError('No puede aplicar un pago parcial a más de 1 factura')
            self.create_payment(payment_line)
        self.journal_state = 'registered'

    def create_payment(self, payment_line):
        amount = payment_line.amount_to_pay if payment_line.amount_to_pay > 0 else sum(invoice.amount_residual for invoice in payment_line.invoice_ids)
        payment = self.env['account.payment'].create({
            'date': self.date,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': payment_line.invoice_ids[0].partner_id.id,
            'amount': amount,
            'journal_id': payment_line.journal_id.id,
            'company_id': self.env.company.id,
            'currency_id': self.env.company.currency_id.id,

            #'reconciled_bill_ids': invoice.id,
            #'reconciled_bills_count': 1,
            'has_reconciled_entries': True,
            'is_reconciled': True,
            #'invoice_line_ids': invoice.invoice_line_ids,
            'ref': payment_line.ref,
            'partner_bank_id': payment_line.partner_bank_id.id,
            'analytic_account': payment_line.analytic_account_id.id,
            'es_anticipo': payment_line.is_down_payment,
            'concepto': payment_line.motive or '',
            'cheque_no_negociable': payment_line.is_non_negociable,
            'payment_method_id': payment_line.available_payment_method_ids.id,
            'payment_journal_id': self.id
        })
        payment.action_post()
        receivable_line = payment.line_ids.filtered('debit')
        for invoice in payment_line.invoice_ids:
            invoice.js_assign_outstanding_line(receivable_line.id)
        payment_line.payment_id = payment
        return payment

    def payment_journal_cancel(self):
        for line_id in self.payment_lines:
            payment_ids = self.env['account.payment'].search([
                ('payment_journal_id', '=', self.id)
            ])
        for payment_id in payment_ids:
            payment_id.action_draft()
            payment_id.action_cancel()
            msg = 'El pago fue cancelado desde el diario de pagos {0}'.format(self.name)
            payment_id.message_post(body=msg)
            self.journal_state = 'cancel'