# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import xlwt
import base64
import io

class ExtractoCuentas(models.TransientModel):
    _name = "libros_conta.extractos_de_cuentas"
    _description = "Extractos de cuentas contables."

    # Campos básicos para filtros
    date_from = fields.Date(string='Fecha Inicial')
    date_to = fields.Date(string='Fecha Final', default=fields.Date.context_today)
    journal_ids = fields.Many2many('account.journal', string='Diarios')
    target_move = fields.Selection([
        ('posted', 'Todos los asientos publicados'),
        ('all', 'Todos los asientos')
    ], string='Movimientos objetivo', default='posted', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', 
                                default=lambda self: self.env.company)
    
    # Campos específicos del extracto
    account = fields.Many2one('account.account', string='Cuenta', required=True)
    name = fields.Char('Nombre archivo', size=32)
    file = fields.Binary('Archivo', filters='.xls')

    def check_report(self):
        """Método para el botón Print - Generar reporte PDF"""
        self.ensure_one()
        
        if not self.account:
            raise UserError(_("Debe seleccionar una cuenta."))
        
        data = {
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'journal_ids': self.journal_ids.ids,
                'target_move': self.target_move,
                'company_id': self.company_id.id,
                'account_id': self.account.id,
                'account_name': f"{self.account.code} - {self.account.name}",
                'sort_selection': 'date',
            }
        }
        
        return self.env.ref('libros_conta.action_report_extracto').report_action(self, data=data)

    def print_xls_file(self):
        """Método para el botón .XLS - Generar archivo Excel"""
        self.ensure_one()
        
        if not self.account:
            raise UserError(_("Debe seleccionar una cuenta."))
        
        lines = self._get_move_lines()
        
        # Crear libro Excel (mantener tu código original)
        libro = xlwt.Workbook()
        hoja = libro.add_sheet('Extracto de Cuenta')
        
        # Encabezados
        encabezados = ['Asiento', 'Fecha', 'Cuenta', 'Referencia', 'Proyecto', 'NIT', 'Contacto', 'Descripción', 'Debe', 'Haber', 'Saldo Acumulado']
        for col, encabezado in enumerate(encabezados):
            hoja.write(0, col, encabezado)
        
        # Datos
        row = 1
        saldo_acumulado = 0
        
        for line in lines:
            saldo_acumulado += (line.credit - line.debit)
            
            hoja.write(row, 0, line.move_id.name or '')
            hoja.write(row, 1, line.date or '')
            hoja.write(row, 2, line.account_id.code or '')
            hoja.write(row, 3, line.move_id.ref or '')
            hoja.write(row, 4, line.analytic_account_id.code if line.analytic_account_id else '')
            hoja.write(row, 5, line.partner_id.vat if line.partner_id else '')
            hoja.write(row, 6, line.partner_id.name if line.partner_id else '')
            hoja.write(row, 7, line.name or '')
            hoja.write(row, 8, line.debit or 0)
            hoja.write(row, 9, line.credit or 0)
            hoja.write(row, 10, saldo_acumulado)
            row += 1

        f = io.BytesIO()
        libro.save(f)
        datos_archivo = base64.b64encode(f.getvalue())

        nombre_archivo = f'extracto-{self.account.code}-{fields.Date.today()}.xls'
        self.write({'file': datos_archivo, 'name': nombre_archivo})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'libros_conta.extractos_de_cuentas',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _get_move_lines(self):
        """Obtener líneas de asiento contable según los filtros"""
        domain = [
            ('account_id', '=', self.account.id),
            ('company_id', '=', self.company_id.id)
        ]
        
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        
        if self.journal_ids:
            domain.append(('journal_id', 'in', self.journal_ids.ids))
        
        if self.target_move == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
        else:
            domain.append(('move_id.state', 'in', ('posted', 'draft')))
        
        return self.env['account.move.line'].search(domain, order='date, move_id')

    def _get_report_lines(self, data):
        """Método auxiliar para el reporte PDF"""
        domain = [
            ('account_id', '=', data['form']['account_id']),
            ('company_id', '=', data['form']['company_id'])
        ]
        
        if data['form'].get('date_from'):
            domain.append(('date', '>=', data['form']['date_from']))
        if data['form'].get('date_to'):
            domain.append(('date', '<=', data['form']['date_to']))
        
        if data['form'].get('journal_ids'):
            domain.append(('journal_id', 'in', data['form']['journal_ids']))
        
        if data['form'].get('target_move') == 'posted':
            domain.append(('move_id.state', '=', 'posted'))
        
        return self.env['account.move.line'].search(domain, order='date, move_id')