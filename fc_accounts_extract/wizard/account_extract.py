
from odoo import api, fields, models
import xlwt
import base64
import io
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


import logging

_logger = logging.getLogger(__name__)

class AccountCommissions(models.TransientModel):
    _name = "account.extract.report"
    _description = "Extracto de cuentas"

    file_name = fields.Char('Nombre archivo', size=32)
    xls_file = fields.Binary('Archivo', filters='.xls')

    date_from = fields.Date(
        string="Fecha inicial"
    )

    date_to = fields.Date(
        string="Fecha final"
    )

    account_id = fields.Many2one(
        string='Cuenta',
        comodel_name='account.account'
    )

    def pdf_report (self):
        return

    def xlsx_report(self, **args):
        for w in self:
            libro = xlwt.Workbook()
            hoja = libro.add_sheet('extracto')
            result = self.getAccountExtract(w.account_id, w.date_from, w.date_to)
            data = result['data'] #arr
            initial_balance = result['summary']['initial_balance']
            # add info
            now = datetime.now()
            hoja.write(0, 0, 'Extracto de cuentas')
            hoja.write(1, 0, str(w.account_id.code) + ' - ' + str(w.account_id.name))
            hoja.write(2, 0, w.account_id.company_id.name)
            hoja.write(3, 0, 'Generado el ' + str(now.strftime("%d/%m/%Y, %H:%M:%S")))
            hoja.write(4, 0, 'Saldo inicial: ')
            hoja.write(4, 1, round(int(initial_balance), 2))
            column = 0
            row = 5
            hoja.write(row, column, 'No. de asiento')
            column += 1
            hoja.write(row, column, 'Fecha')
            column += 1
            hoja.write(row, column, 'Referencia de la factura')
            column += 1
            hoja.write(row, column, 'Proyecto')
            column += 1
            hoja.write(row, column, 'NIT del proveedor')
            column += 1
            hoja.write(row, column, 'Nombre del proveedor')
            column += 1
            hoja.write(row, column, 'Descripción')
            column += 1
            hoja.write(row, column, 'Debe')
            column += 1
            hoja.write(row, column, 'Haber')
            column += 1
            hoja.write(row, column, 'Suma acumulada')

            column = 0
            row += 1
            for line in data:
                hoja.write(row, column, line['number'])
                column += 1
                hoja.write(row, column, line['date'].strftime("%d/%m/%Y"))
                column += 1
                hoja.write(row, column, line['ref'])
                column += 1
                hoja.write(row, column, line['project'])
                column += 1
                hoja.write(row, column, line['supplier_vat'])
                column += 1
                hoja.write(row, column, line['supplier_name'])
                column += 1
                hoja.write(row, column, line['description'])
                column += 1
                hoja.write(row, column, line['debit'])
                column += 1
                hoja.write(row, column, line['credit'])
                column += 1
                hoja.write(row, column, line['balance'])

                column = 0
                row +=1

            f = io.BytesIO()
            libro.save(f)
            datos = base64.b64encode(f.getvalue())
            self.write({'xls_file': datos, 'file_name': 'extracto_cuentas.xls'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.extract.report',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
    
    def getAccountExtract(self, account_id, date_from, date_to):
        data = []
        initial_balance = self.getInitialBalance(account_id, date_from)
        balance = initial_balance
        journal_items = self.env['account.move.line'].search([
            ('account_id', '=', account_id.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('parent_state', '=', 'posted')
        ], order="date asc")
        for item in journal_items:
            if account_id.account_behavior == 'plus_credit_minus_debit':
                balance += (item.credit - item.debit)
            elif account_id.account_behavior == 'plus_debit_minus_credit':
                balance += (item.debit - item.credit)
            else:
                raise UserError('La cuenta contable debe tener un comportamiento asignado')
            data.append(
                {
                    'number': item.move_id.name,
                    'date': item.date,
                    'ref': item.name,
                    'project': item.analytic_account_id.name,
                    'supplier_vat': item.partner_id.vat,
                    'supplier_name': item.partner_id.name,
                    'description': item.name,
                    'debit': item.debit,
                    'credit': item.credit,
                    'balance': balance

                }
            )
        return {
            'data': data,
            'summary': {
                'initial_balance': initial_balance
            }
        }
    
    def getInitialBalance(self, account_id, date_from):
        journal_items = self.env['account.move.line'].search([
            ('account_id', '=', account_id.id),
            ('date', '<', date_from), #get all journal items previous to the initial date
            ('parent_state', '=', 'posted')
        ])
        initial_balance = 0
        for item in journal_items:
            #_logger.info(item.move_id.name)
            if account_id.account_behavior == 'plus_credit_minus_debit':
                initial_balance += (item.credit - item.debit)
            elif account_id.account_behavior == 'plus_debit_minus_credit':
                initial_balance += (item.debit - item.credit)
            else:
                raise UserError('La cuenta contable debe tener un comportamiento asignado')
        _logger.info('xxxxxxxxxxxxxxxxxxxx initial_balance')
        _logger.info(initial_balance)
        return initial_balance