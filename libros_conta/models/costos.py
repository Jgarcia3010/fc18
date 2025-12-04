from odoo import models, fields, api

class ReportCostos(models.Model):
    _name = "libros_conta.costos"
    _description = "Reporte de Costos"
    _auto = False
    _rec_name = 'fecha'
    _order = 'fecha desc'

    order_id = fields.Many2one('purchase.order', readonly=True, string="OC")
    move = fields.Many2one('account.move', readonly=True, string="Factura")
    analytic_account = fields.Many2one('account.analytic.account', readonly=True, string="Proyecto")
    fecha = fields.Date(string='Fecha')
    user_id = fields.Many2one('res.users', readonly=True, string='Solicitante')
    partner = fields.Many2one('res.partner', string='Proveedor', readonly=True)
    vat = fields.Char(string='NIT', readonly=True)
    product = fields.Many2one('product.product', readonly=True, string='Artículo')
    description = fields.Char(string='Descripción')
    quantity = fields.Float(string='Cantidad')
    unitprice = fields.Float(string='Precio unitario')
    total = fields.Float(string='Total')


    @property
    def _table_query(self):
        query = '%s %s %s' % (self._select(), self._from(), self._where())
        return query

    @api.model
    def _select(self):
        return '''
          SELECT
            id,
            order_id,
            move,
            analytic_account,
            fecha,
            user_id,
            partner,
            vat,
            product,
            description,
            quantity,
            unitprice,
            total
        '''

    @api.model
    def _from(self):
        return '''
          FROM
          (
            SELECT
                line.id AS id,
                order_id AS order_id,
                NULL AS move,
                x_studio_cuenta_analitica AS analytic_account,
                theorder.user_id AS user_id,
                date_order AS fecha,
                theorder.partner_id AS partner,
                partner.vat AS vat,
                product_id AS product,
                line.name AS description,
                product_qty AS quantity,
                price_unit AS unitprice,
                price_total AS total

            FROM purchase_order_line AS line
                LEFT JOIN res_partner partner ON partner.id = line.partner_id
                INNER JOIN purchase_order theorder ON theorder.id = line.order_id
                LEFT JOIN product_product product ON product.id = line.product_id
                LEFT JOIN product_template template ON template.id = product.product_tmpl_id

            WHERE theorder.state IN ('purchase')
                AND COALESCE(product.default_code, '') <> 'ISR RETENCIONES'
                AND theorder.company_id = {}

            UNION

            SELECT
                10000000+line.id AS id,
                NULL AS order_id,
                move.id AS move,
                x_studio_cuenta_analitica AS analytic_account,
                NULL AS user_id,
                factura.fecha AS fecha,
                move.partner_id AS partner,
                partner.vat AS vat,
                product_id AS product,
                line.name AS description,
                quantity AS quantity,
                price_unit AS unitprice,
                price_total AS total

            FROM account_move_line AS line
                LEFT JOIN account_facturaexterna factura ON factura.id = line.facturaexterna
                LEFT JOIN res_partner partner ON partner.id = line.partner_id
                INNER JOIN account_move move ON move.id = line.move_id
                LEFT JOIN product_product product ON product.id = line.product_id
                LEFT JOIN product_template template ON template.id = product.product_tmpl_id

            WHERE
                move.move_type IN ('in_invoice', 'in_refund')
                AND COALESCE(product.default_code, '') <> 'ISR RETENCIONES'
                
                -- CORRECCIÓN ODOO 18
                AND line.display_type = 'product'
                
                AND line.facturaexterna IS NOT NULL
                AND move.state NOT IN ('draft', 'cancel')
                AND move.caja_chica = TRUE

                AND move.company_id = {}
          ) temptable
        '''.format(self.env.company.id, self.env.company.id)

    @api.model
    def _where(self):
        return ''
