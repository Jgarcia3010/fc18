# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.misc import get_lang
from odoo.tools import pycompat
import io
import base64
import logging
import time
import datetime
import copy

class Pagos(models.TransientModel):
    _name = "libros_conta.pagos"
    _description = "Transacciones bancarias"
    @api.model
    def _get_default_journal(self):
        ''' Retrieve the default journal for the account.payment.
        /!\ This method will not override the method in 'account.move' because the ORM
        doesn't allow overriding methods using _inherits. Then, this method will be called
        manually in 'create' and 'new'.
        :return: An account.journal record.
        '''
        return self.env['account.move']._search_default_journal(('bank', 'cash'))

    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
        check_company=True,
        default=_get_default_journal)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    payment_journal_id = fields.Many2one(
        string="Diario de pago",
        comodel_name='payment.journal',
        required=True
    )

    file_download = fields.Binary('file', blank=True)


    def get_report(self):
        filters = [
            ('payment_journal_id', '=', self.payment_journal_id.id)
        ]

        data = self.env['account.payment'].search(filters)
        

        csvtitle = [
            "Tipo", "Cuenta", "NIT", "Nombre", "Monto", "", "Circular", "Asiento", "Factura", "Monto", "Diario"
        ]
        csvrows = [
            csvtitle
        ]
        for row in data:
            csvrow = [
                row.partner_bank_id.account_type,
                row.partner_bank_id.acc_number,
                row.partner_id.vat,
                row.partner_bank_id.acc_holder_name if row.partner_bank_id.acc_holder_name else row.partner_bank_id.partner_id.name,
                row.amount,
                '',
                row.ref if row.ref else "",
                row.name,
                row.reconciled_bill_ids[0].name if len(row.reconciled_bill_ids) > 0 else 'ANTICIPO',
                row.amount,
                row.journal_id.name
            ]
            csvrows.append(csvrow)

        fp = io.BytesIO()
        writer = pycompat.csv_writer(fp, quoting=1, delimiter='|')
        for row in csvrows:
            csvrow = []
            for cell in row:
                  csvrow.append(pycompat.to_text(cell))
            writer.writerow(csvrow)
        self.file_download = base64.b64encode(fp.getvalue())

        return {
            'type': 'ir.actions.act_url',
            'name': 'pagos',
            'url': '/web/content/libros_conta.pagos/%s/file_download/transacciones.csv?download=true' %(self.id),
        }
