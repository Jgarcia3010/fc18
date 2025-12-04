from odoo import models, fields, api
import logging
from functools import lru_cache


class AccountInvoiceVentas(models.Model):
    _name = "account.invoice.libroventas"
    _description = "Invoices Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    # ==== Invoice fields ====
    vat = fields.Char(string='NIT', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Nombre', readonly=True)
    move_id = fields.Many2one('account.move', readonly=True, string="Factura")
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    date = fields.Date(string='Fecha', readonly=True)
    move_type = fields.Selection([
        ('out_invoice', 'Factura'),
        ('in_invoice', 'Factura'),
        ('out_refund', 'Nota de Crédito'),
        ('in_refund', 'Nota de Crédito'),
        ], readonly=True, string="Tipo")

    mbase = fields.Float(readonly=True, string="Materiales Base")
    mimpuestos = fields.Float(readonly=True, string="Materiales Impuestos")
    sbase = fields.Float(readonly=True, string="Servicios Base")
    simpuestos = fields.Float(readonly=True, string="Servicios Impuestos")
    # exportm = fields.Float(readonly=True, string="Exportación de Materiales")
    # exports = fields.Float(readonly=True, string="Exportación de Servicios")
    factura = fields.Char(string="Número", readonly=True)
    serie = fields.Char(string="Serie", readonly=True)
    exportation = fields.Float(
        string='Exportación',
        compute='_compute_export',
        default = 0.0
    )
    
    currency_id = fields.Many2one('res.currency', related='move_id.currency_id', string='Currency', readonly=True)
    total = fields.Monetary(related='move_id.amount_total_signed', string='Total', currency_field='currency_id', readonly=True)

    @api.depends('move_id')
    def _compute_export(self):
        for rec in self:
          # Se asume que journal_id.journal_usage es un campo custom que ya existe
          if rec.move_id.journal_id.journal_usage == 'export':
              rec.exportation = rec.sbase + rec.simpuestos
          else:
              rec.exportation = 0

    @api.onchange('exportation')
    def _onchange_exportation(self):
        for rec in self:
            if rec.exportation > 0:
                rec.sbase = rec.simpuestos = 0

    _depends = {
        'account.move': [
            'name', 'state', 'move_type', 'partner_id', 'invoice_user_id', 'fiscal_position_id',
            'invoice_date', 'date', 'invoice_payment_term_id', 'partner_bank_id',
        ],
        'account.move.line': [
            'move_id', 'company_id',  'partner_id'
        ]
    }



    def imprimir(self, fields, domain, context):
        """
          Imprimir el reporte basado en un @domain (filtro) y sólo los campos incluidos en el array @fields. El contexto ( @context ) define la compañía, el idioma, etc. Esto se llama por ahora desde el frontend, en la vista de lista del informe.
        """
        report_action = self.env.ref("libros_conta.action_imprimir_libro_ventas")
        model = self.with_context(**context)
        searchresult = model.search(domain, offset=0, limit=False, order=False)
        exportdata = searchresult.export_data(fields)
        fieldsnames = [self._fields[field].string for field in fields]

        if len(exportdata['datas']) == 0:
            return None;

        daterange = [False, False]
        for item in domain:
            if type(item) == list and item[0] == "filter_date":
                if item[1] == ">=":
                    daterange[0] = item[2]
                if item[1] == "<=":
                    daterange[1] = item[2]

        summable = [ type(cell) == float  for cell in exportdata['datas'][0] ]
        sums = [ sum([ row[i] for row in exportdata['datas'] ]) if isfloat else None for i, isfloat in enumerate(summable) ]

        data = {
            "columns": fieldsnames,
            "colnames": fields,
            "sums": sums,
            "daterange": daterange,
            "domain": domain
        }

        return report_action.report_action(False, data)

    @property
    def _table_query(self):
        query = '%s %s %s' % (self._select(), self._from(), self._where())
        return query

    @api.model
    def _select(self):
        return '''
            SELECT
                id,
                vat,
                partner_id,
                move_id,
                company_id,
                move_type,
                "date",
                mbase,
                mimpuestos,
                sbase,
                simpuestos,
                factura,
                serie
        '''

    @api.model
    def _from(self):
        # CORRECCIÓN: Se duplicaron los símbolos '%' a '%%' en los ILIKE para evitar el TypeError de Python
        return '''
            FROM
            (
SELECT
line.move_id AS id,
partner.vat,
line.partner_id,
line.move_id,
line.company_id,
move.move_type,
move.date,
move.payment_reference AS factura,
move.x_studio_serie AS serie,

SUM(CASE WHEN template.x_studio_bien_o_servicio = 'bien' THEN line.price_subtotal ELSE 0 END) * (CASE WHEN move.move_type = 'out_refund' THEN -1 ELSE 1 END) AS mbase,
SUM(CASE WHEN template.x_studio_bien_o_servicio = 'bien' THEN line.price_total - line.price_subtotal ELSE 0 END) * (CASE WHEN move.move_type = 'out_refund' THEN -1 ELSE 1 END) AS mimpuestos,
SUM(CASE WHEN COALESCE(template.x_studio_bien_o_servicio, '') <> 'bien' THEN line.price_subtotal ELSE 0 END) * (CASE WHEN move.move_type = 'out_refund' THEN -1 ELSE 1 END) AS sbase,
SUM(CASE WHEN COALESCE(template.x_studio_bien_o_servicio, '') <> 'bien' THEN line.price_total - line.price_subtotal ELSE 0 END) * (CASE WHEN move.move_type = 'out_refund' THEN -1 ELSE 1 END) AS simpuestos

FROM account_move_line line
LEFT JOIN res_partner partner ON partner.id = line.partner_id
INNER JOIN account_move move ON move.id = line.move_id
LEFT JOIN product_product product ON product.id = line.product_id
LEFT JOIN product_template template ON template.id = product.product_tmpl_id

WHERE
      move.move_type IN ('out_invoice', 'out_refund')
      AND COALESCE(template.exclude_libros, template.exclude_libros, FALSE) = FALSE
      AND COALESCE(partner.exclude_libros, FALSE) = FALSE
      
      -- Corrección anterior mantenida (display_type)
      AND line.display_type = 'product'
      
      AND move.state NOT IN ('draft', 'cancel')

GROUP BY
          partner.vat, line.partner_id,
          line.move_id, line.company_id, move.move_type, move.date,
          move.payment_reference, move.x_studio_serie
            ) temptable
        '''

    @api.model
    def _where(self):
        return 'WHERE company_id = {}'.format(self.env.company.id)