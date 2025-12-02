# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bank_operation_ref = fields.Char(string="Referencia bancaria")
    account_journal_type = fields.Char(string="Tipo de diario", readonly=True, store=False)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.account_journal_type = self.journal_id.type

    def _prepare_payment_moves(self):

        all_move_vals = []
        all_moves = super(AccountPayment, self)._prepare_payment_moves()
        for payment in self:
            for move in all_moves:
                if payment.bank_operation_ref:
                    move['bank_operation_ref'] = payment.bank_operation_ref

        return all_moves


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    bank_operation_ref = fields.Char(string="Referencia bancaria")
    account_journal_type = fields.Char(string="Tipo de diario", readonly=True, store=False)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.account_journal_type = self.journal_id.type
