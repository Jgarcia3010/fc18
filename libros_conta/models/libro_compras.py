from odoo import models, fields, api
import logging
from functools import lru_cache
import locale
from datetime import datetime

class AccountInvoiceCompras(models.Model):
    _name = "account.invoice.librocompras"
    _description = "Libro Contable de Compras"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    # ==== Invoice fields ====
    vat = fields.Char(string='NIT', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Nombre', readonly=True)
    move_id = fields.Many2one('account.move', readonly=True, string="Factura")
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    date = fields.Date(string='Fecha', readonly=True)
    filter_date = fields.Date(string='Fecha para filtro', readonly=True)
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
    mpcbase = fields.Float(readonly=True, string="Materiales Pequeño Contribuyente")
    mpcimpuestos = fields.Float(readonly=True, string="Materiales PC Impuestos")
    spcbase = fields.Float(readonly=True, string="Servicios Pequeño Contribuyente")
    spcimpuestos = fields.Float(readonly=True, string="Servicios PC Impuestos")
    factura = fields.Char(string="Número", readonly=True)
    serie = fields.Char(string="Serie", readonly=True)
    importation = fields.Float(
        string="Importación",
        compute="_compute_import",
        default = 0.0
    )
    
    currency_id = fields.Many2one('res.currency', related='move_id.currency_id', string='Currency', readonly=True)
    total = fields.Monetary(related='move_id.amount_total_signed', string='Total', currency_field='currency_id', readonly=True)
    
    @api.depends('move_id')
    def _compute_import(self):
        for rec in self:
          if rec.move_id.journal_id.journal_usage == 'import':
              rec.importation = rec.sbase + rec.simpuestos
          else:
              rec.importation = 0

    @api.onchange('importation')
    def _onchange_importation(self):
        for rec in self:
            if rec.importation > 0:
                rec.sbase = rec.simpuestos = 0

    _depends = {
        'account.move': [
            'name', 'state', 'move_type', 'partner_id', 'invoice_user_id', 'fiscal_position_id',
            'invoice_date', 'invoice_date_due', 'invoice_payment_term_id', 'partner_bank_id',
        ],
        'account.move.line': [
            'move_id', 'company_id',  'partner_id'
        ],
        'account.facturaexterna': [
            'factura', 'serie'
        ]
    }

    def imprimir(self, fields, domain, context):
        report_action = self.env.ref("libros_conta.action_imprimir_libro_compras")
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
                factura,
                serie,
                move_type,
                "date",
                filter_date,
                mbase,
                mimpuestos,
                sbase,
                simpuestos,
                mpcbase,
                mpcimpuestos,
                spcbase,
                spcimpuestos
        '''

    @api.model
    def _from(self):
        # CORRECCIÓN 1: Usar ::VARCHAR en lugar de CAST() para evitar error de sintaxis JSON con valores nulos.
        # CORRECCIÓN 2: Mantener %% para evitar TypeError de Python.
        # CORRECCIÓN 3: Mantener display_type = 'product'
        
        return '''
          FROM
          (
            SELECT
              move.id AS id,
              partner.vat,
              line.partner_id,
              line.move_id,
              line.company_id,
              move.ref AS factura,
              move.x_studio_serie AS serie,
              move.move_type,
              move.date AS "date",
              move.date AS filter_date,
              
              SUM(CASE WHEN template.x_studio_bien_o_servicio IN ('bien', 'articulo') AND COALESCE(fispos.name::VARCHAR, '') NOT ILIKE '%%Pequeño Contribuyente%%' THEN line.balance ELSE 0 END)  AS mbase,
              SUM(CASE WHEN template.x_studio_bien_o_servicio IN ('bien', 'articulo') AND COALESCE(fispos.name::VARCHAR, '') NOT ILIKE '%%Pequeño Contribuyente%%'  THEN 0.12*line.balance ELSE 0 END)  AS mimpuestos,
              SUM(CASE WHEN (coalesce(template.x_studio_bien_o_servicio,'') NOT IN ('bien', 'articulo'))  AND COALESCE(fispos.name::VARCHAR, '') NOT ILIKE '%%Pequeño Contribuyente%%'  THEN line.balance ELSE 0 END) AS sbase,
              SUM(CASE WHEN (coalesce(template.x_studio_bien_o_servicio,'') NOT IN ('bien', 'articulo')) AND COALESCE(fispos.name::VARCHAR, '') NOT ILIKE '%%Pequeño Contribuyente%%' THEN 0.12*line.balance ELSE 0 END) AS simpuestos,
              SUM(CASE WHEN template.x_studio_bien_o_servicio IN ('bien', 'articulo') AND COALESCE(fispos.name::VARCHAR, '') ILIKE '%%Pequeño Contribuyente%%' THEN line.balance ELSE 0 END) AS mpcbase,
              SUM(CASE WHEN template.x_studio_bien_o_servicio IN ('bien', 'articulo')  AND COALESCE(fispos.name::VARCHAR, '') ILIKE '%%Pequeño Contribuyente%%' THEN 0*line.balance ELSE 0 END) AS mpcimpuestos,
              SUM(CASE WHEN (coalesce(template.x_studio_bien_o_servicio,'') NOT IN ('bien', 'articulo'))  AND COALESCE(fispos.name::VARCHAR, '') ILIKE '%%Pequeño Contribuyente%%' THEN line.balance ELSE 0 END) AS spcbase,
              SUM(CASE WHEN (coalesce(template.x_studio_bien_o_servicio,'') NOT IN ('bien', 'articulo'))  AND COALESCE(fispos.name::VARCHAR, '') ILIKE '%%Pequeño Contribuyente%%' THEN 0 ELSE 0 END) AS spcimpuestos


            FROM account_move_line line
              LEFT JOIN res_partner partner ON partner.id = line.partner_id
              INNER JOIN account_move move ON move.id = line.move_id
              LEFT JOIN account_fiscal_position fispos ON fispos.id = move.fiscal_position_id
              LEFT JOIN product_product product ON product.id = line.product_id
              LEFT JOIN product_template template ON template.id = product.product_tmpl_id
              LEFT JOIN (
                SELECT * FROM account_move WHERE move_type = 'in_refund'
              ) refund ON refund.reversed_entry_id = move.id

            WHERE move.move_type IN ('in_invoice', 'in_refund')
              AND COALESCE(template.exclude_libros, template.exclude_libros, FALSE) = FALSE
              AND COALESCE(partner.exclude_libros, FALSE) = FALSE
              
              AND line.display_type = 'product'
              
              AND move.state NOT IN ('draft', 'cancel')
              AND COALESCE(move.caja_chica, FALSE) = FALSE
              AND
                ( COALESCE(move.x_studio_nota_de_crdito_interna, FALSE) = FALSE AND COALESCE(refund.x_studio_nota_de_crdito_interna, FALSE) = FALSE)

            GROUP BY move.id, partner.vat, line.partner_id, line.move_id, line.company_id, move.move_type, move.date, move.ref, move.x_studio_serie, fispos.name


            UNION

            SELECT
              -1*factura.id AS id,
              partner.vat,
              partner.id AS partner_id,
              line.move_id,
              line.company_id,
              factura.factura AS factura,
              factura.serie AS serie,
              move.move_type,
              move.date AS "date",
              move.date AS filter_date,
              
              SUM(CASE WHEN template.x_studio_bien_o_servicio IN ('bien', 'articulo') AND COALESCE(fispos.name::VARCHAR, '') NOT ILIKE '%%Pequeño Contribuyente%%' THEN line.balance ELSE 0 END) AS mbase,
              SUM(CASE WHEN template.x_studio_bien_o_servicio IN ('bien', 'articulo') AND COALESCE(fispos.name::VARCHAR, '') NOT ILIKE '%%Pequeño Contribuyente%%'  THEN 0.12*line.balance ELSE 0 END) AS mimpuestos,
              SUM(CASE WHEN (coalesce(template.x_studio_bien_o_servicio,'') NOT IN ('bien', 'articulo'))  AND COALESCE(fispos.name::VARCHAR, '') NOT ILIKE '%%Pequeño Contribuyente%%'  THEN line.balance ELSE 0 END) AS sbase,
              SUM(CASE WHEN (coalesce(template.x_studio_bien_o_servicio,'') NOT IN ('bien', 'articulo')) AND COALESCE(fispos.name::VARCHAR, '') NOT ILIKE '%%Pequeño Contribuyente%%' THEN 0.12*line.balance ELSE 0 END) AS simpuestos,
              SUM(CASE WHEN template.x_studio_bien_o_servicio IN ('bien', 'articulo') AND COALESCE(fispos.name::VARCHAR, '') ILIKE '%%Pequeño Contribuyente%%' THEN line.balance ELSE 0 END) AS mpcbase,
              SUM(CASE WHEN template.x_studio_bien_o_servicio IN ('bien', 'articulo')  AND COALESCE(fispos.name::VARCHAR, '') ILIKE '%%Pequeño Contribuyente%%' THEN 0*line.balance ELSE 0 END) AS mpcimpuestos,
              SUM(CASE WHEN (coalesce(template.x_studio_bien_o_servicio,'') NOT IN ('bien', 'articulo'))  AND COALESCE(fispos.name::VARCHAR, '') ILIKE '%%Pequeño Contribuyente%%' THEN line.balance ELSE 0 END) AS spcbase,
              SUM(CASE WHEN (coalesce(template.x_studio_bien_o_servicio,'') NOT IN ('bien', 'articulo'))  AND COALESCE(fispos.name::VARCHAR, '') ILIKE '%%Pequeño Contribuyente%%' THEN 0 ELSE 0 END) AS spcimpuestos

            FROM account_move_line line
              LEFT JOIN account_facturaexterna factura ON factura.id = line.facturaexterna
              LEFT JOIN res_partner partner ON partner.id = factura.proveedor
              LEFT JOIN account_move move ON move.id = line.move_id
              LEFT JOIN account_fiscal_position fispos ON fispos.id = factura.fiscal_position_id
              LEFT JOIN product_product product ON product.id = line.product_id
              LEFT JOIN product_template template ON template.id = product.product_tmpl_id

            WHERE
                  move.move_type IN ('in_invoice', 'in_refund')
              
              AND line.display_type = 'product'
              
              AND line.facturaexterna IS NOT NULL
              AND COALESCE(template.exclude_libros, template.exclude_libros, FALSE) = FALSE
              AND move.state NOT IN ('draft', 'cancel')
              AND move.caja_chica = TRUE
              AND COALESCE(partner.exclude_libros, FALSE) = FALSE
            GROUP BY factura.id, partner.vat, partner.id, line.move_id, line.company_id, move.date, factura.factura, factura.serie, move.move_type, fispos.name
          ) temptable
        '''

    @api.model
    def _where(self):
        return 'WHERE company_id = {}'.format(self.env.company.id)