# -*- coding: utf-8 -*-
from babel import dates
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import logging

MESES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre"
]

class account_payment(models.Model):
    _inherit = "account.payment"
    cheque_no_negociable = fields.Boolean(string='No negociable')
    concepto = fields.Text(string='Concepto')
    cheque_formato = fields.Selection([
        ('1', 'Formato 1'),
        ('2', 'Formato 2'),
        ('3', 'Formato 3'),
    ], default = '1', string="Formato de impresión", help="El formato 1 incluye los datos de la cuenta bancario en el voucher, en la parte de abajo.")
    analytic_account = fields.Many2one('account.analytic.account',
                                     string='Cuenta analítica',
                                     required=False, readonly=False,
                                     ondelete="set null")

    def do_print_checks(self):
        check_layout = self.company_id.account_check_printing_layout
        redirect_action = self.env.ref('account.action_account_config')
        if not check_layout or check_layout == 'disabled':
            msg = _("You have to choose a check layout. For this, go in Invoicing/Accounting Settings, search for 'Checks layout' and set one.")
            raise RedirectWarning(msg, redirect_action.id, _('Go to the configuration panel'))
        report_action = self.env.ref(check_layout, False)
        raise UserError(report_action)
        if not report_action:
            msg = _("Something went wrong with Check Layout, please select another layout in Invoicing/Accounting Settings and try again.")
            raise RedirectWarning(msg, redirect_action.id, _('Go to the configuration panel'))
        self.write({'is_move_sent': True})
        return report_action.report_action(self)

    def _check_get_pages(self):
        returnvalue = self._check_build_page_info(0, False)
        #returnvalue["amount_in_word"] = returnvalue["amount_in_word"].replace("*", "").strip(" ")
        returnvalue["pago_name"] = self.name
        returnvalue["cheque_formato"] = self.cheque_formato
        returnvalue["banco"] = self.journal_id.name
        returnvalue["cuenta"] = self.journal_id.bank_account_id.acc_number

        amount_in_word_no_cents = self.currency_id.amount_to_text(int(self.amount))
        cents = int(round((self.amount - int(self.amount)) * 100, 2))
        amount_in_word_no_cents_no_currency = amount_in_word_no_cents.split(self.currency_id.currency_unit_label)[0] + 'CON ' + str(cents) + '/100'
        returnvalue["amount_in_word"] = amount_in_word_no_cents_no_currency.upper()
        #raise UserError(amount_in_word_no_cents_no_currency)

        alines = []
        for line in self.move_id.line_ids:
            aline = {}
            aline["code"] = line.account_id.code
            aline["name"] = line.account_id.name
            aline["debe"] = line.debit
            aline["haber"] = line.credit
            alines.append(aline)
        returnvalue["lines"] = alines
        returnvalue["proyecto"] = ""

        # Poner datos adicionales
        returnvalue['nonegociable'] = self.cheque_no_negociable
        returnvalue['fecha_esp'] = "Guatemala, " + str(self.date.day) + " de " + MESES[self.date.month-1] + " de " + str(self.date.year)
        returnvalue['concepto'] = self.concepto
        returnvalue["proyecto"] = "[{}] {}".format(
                    self.analytic_account.code,
                    self.analytic_account.name
                  )

        term_lines = self.line_ids.filtered(lambda line: line.account_id.internal_type in ('receivable', 'payable'))
        invoices = (term_lines.matched_debit_ids.debit_move_id.move_id + term_lines.matched_credit_ids.credit_move_id.move_id)\
            .filtered(lambda x: x.is_outbound())
        invoices = invoices.sorted(lambda x: x.invoice_date_due or x.date)

        # Group partials by invoices.
        invoice_map = {invoice: self.env['account.partial.reconcile'] for invoice in invoices}
        for partial in term_lines.matched_debit_ids:
            invoice = partial.debit_move_id.move_id
            if invoice in invoice_map:
                invoice_map[invoice] |= partial
        for partial in term_lines.matched_credit_ids:
            invoice = partial.credit_move_id.move_id
            if invoice in invoice_map:
                invoice_map[invoice] |= partial

        if 'in_invoice' in invoices.mapped('move_type'):
            facturas = "Facturas: "
            facturas += ", ".join([str(invoice.x_studio_serie) + " - " + str(invoice.ref)
                        for invoice, partials in invoice_map.items()
                          if invoice.move_type == 'in_invoice'])
        else:
            facturas = ""
        if 'out_refund' in invoices.mapped('move_type'):
            reembolsos = "Reembolsos: "
            reembolsos += ", ".join([str(invoice.x_studio_serie) + " - " + str(invoice.ref)
                           for invoice, partials in invoice_map.items()
                           if invoice.move_type == 'out_refund'])
        else:
            reembolsos = ""

        returnvalue["facturas"] = facturas
        returnvalue["reembolsos"] = reembolsos
        returnvalue["circular"] = self.ref
        logging.info(str(returnvalue))

        return [returnvalue]



class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    analytic_account = fields.Many2one(
        'account.analytic.account',
        string='Cuenta analítica',
        required=False, readonly=False, store=True,
        ondelete="set null",
        compute='_compute_analytic_account'
    )

    @api.depends('can_edit_wizard')
    def _compute_analytic_account(self):
        ''' Helper to compute the analytic account based on the batch.
        :param batch_result:    A batch returned by '_get_batches'.
        :return:                An analytic account id to be set on payment.
        '''
        for wizard in self:
            if wizard.can_edit_wizard:
                batches = wizard._get_batches()
                first_analytic_account = batches[0]['lines'][0].analytic_account_id or batches[0]['lines'][0].move_id.x_studio_cuenta_analitica
                wizard.analytic_account = first_analytic_account
            else:
                wizard.analytic_account = False


    def _create_payment_vals_from_wizard(self):
        # OVERRIDE
        payment_vals = super()._create_payment_vals_from_wizard()
        payment_vals['analytic_account'] = self.analytic_account.id
        return payment_vals
