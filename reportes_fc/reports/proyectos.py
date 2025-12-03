from odoo import models, fields, api
import logging

class Proyectos(models.Model):
    _name = "reportesfc.proyectos"
    _description = "Reporte de Proyectos"
    _auto = False

    proyecto = fields.Many2one('account.analytic.group', readonly=True, string="Proyecto")
    subproyecto = fields.Many2one('account.analytic.account', readonly=True, string="Sub Proyecto")
    facturado_total = fields.Float(string='Total facturado')
    anticipo = fields.Float(string='Anticipo')
    anticipo_facturado = fields.Float(string='Facturado del anticipo')
    pendiente_facturar = fields.Float(string='Pendiente de facturar')
    facturas_pendientes = fields.Float(string='Facturas pendientes de pago')
    presupuesto = fields.Float(string='Presupuesto')
    por_cobrar = fields.Float(string='Por cobrar')
    honorarios_obra = fields.Float(string='Honorarios de obra')
    costo_directo = fields.Float(string='Costo Directo')
    mano_de_obra = fields.Float(string='Mano de Obra')
    impuestos = fields.Float(string='Impuestos')
    cuota_admin = fields.Float(string='Cuota administrativa')
    total_gastos = fields.Float(string='Total de gastos')
    pendiente_ejecutar = fields.Float(string='Pendiente de ejecutar / Utilidad')
    anticipos_proveedor = fields.Float(string='Anticipos del proveedor')
    por_pagar = fields.Float(string='Por pagar')
    iva_por_pagar = fields.Float(string='IVA por pagar')
    iva_por_cobrar = fields.Float(string='IVA por cobrar')
    iva_proyecto = fields.Float(string='IVA del proyecto')
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    @property
    def _table_query(self):
        query = '%s %s %s' % (self._select(), self._from(), self._where())
        return query

    @api.model
    def _select(self):
        return '''
        SELECT
            id,
            proyecto,
            subproyecto,
            facturado_total,
            anticipo,
            anticipo_facturado,
            LEAST(facturado_total - anticipo, 0) AS pendiente_facturar,
            GREATEST(facturado_total - anticipo, 0) AS facturas_pendientes,
            presupuesto,
            (presupuesto - facturado_total) AS por_cobrar,
            honorarios_obra,
            costo_directo,
            mano_de_obra,
            impuestos,
            cuota_admin,
            (honorarios_obra + costo_directo + mano_de_obra + impuestos + cuota_admin) AS total_gastos,
            (presupuesto - (honorarios_obra + costo_directo + mano_de_obra + impuestos + cuota_admin) ) AS pendiente_ejecutar,
            anticipos_proveedor,
            (honorarios_obra + costo_directo + mano_de_obra + impuestos + cuota_admin) - pagado AS por_pagar,
            (facturado_total/1.12) * 0.12 AS iva_por_pagar,
            ( (honorarios_obra + costo_directo + mano_de_obra) /1.12) * 0.12 AS iva_por_cobrar,
            ( (honorarios_obra + costo_directo + mano_de_obra - facturado_total)/1.12) * 0.12 AS iva_proyecto,
            company_id
        '''
    @api.model
    def _from(self):
        return '''
          FROM
          (
            SELECT
                account_analytic_account.id AS id,
                account_analytic_account.group_id AS proyecto,
                account_analytic_account.id AS subproyecto,
                (
                    -- https://github.com/odoo/odoo/blob/14.0/addons/account/models/account_payment.py#L463
                    SELECT
                        SUM(move.amount_total)
                    FROM account_payment payment
                    JOIN account_move move ON move.id = payment.move_id
                    JOIN account_move_line line ON line.move_id = move.id
                    JOIN account_partial_reconcile part ON
                        part.debit_move_id = line.id
                        OR
                        part.credit_move_id = line.id
                    JOIN account_move_line counterpart_line ON
                        part.debit_move_id = counterpart_line.id
                        OR
                        part.credit_move_id = counterpart_line.id
                    JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                    JOIN account_account account ON account.id = line.account_id
                    WHERE account.internal_type IN ('receivable', 'payable')
                        AND line.id != counterpart_line.id
                        AND invoice.move_type in ('in_invoice', 'in_refund')
                        AND payment.analytic_account = account_analytic_account.id
                        AND payment.es_anticipo IS TRUE
                ) AS anticipo_facturado,
                account_analytic_account.company_id
            FROM account_analytic_account
            GROUP BY account_analytic_account.id, proyecto, account_analytic_account.company_id

            ) basedata
            ''' + (
            '''
          LEFT JOIN (
            SELECT
                budgetline.analytic_account_id, budgetline.company_id AS company_id_P,
                SUM(budgetline.planned_amount) AS presupuesto
            FROM crossovered_budget_lines budgetline
            GROUP BY analytic_account_id, company_id_P
            ) presupuestos ON presupuestos.analytic_account_id = basedata.id AND presupuestos.company_id_P = company_id
            ''' if 'crossovered.budget.lines' in self.env else '''
          LEFT JOIN (
            SELECT
                temp_a.id AS analytic_account_id, temp_a.company_id AS company_id_P,
                0 AS presupuesto
            FROM account_analytic_account temp_a
            GROUP BY temp_a.id, temp_a.company_id
            ) presupuestos ON presupuestos.analytic_account_id = basedata.id AND presupuestos.company_id_P = company_id
            ''' ) + '''
          LEFT JOIN (
            SELECT
                x_studio_cuenta_analitica, account_move.company_id AS company_id_A,
                SUM(amount_total) AS facturado_total
            FROM account_move
            WHERE account_move.move_type IN ('out_invoice', 'out_refund') AND
                  account_move.state NOT IN ('draft', 'cancel')
            GROUP BY x_studio_cuenta_analitica, account_move.company_id

            ) moves ON moves.x_studio_cuenta_analitica = basedata.id AND
                       moves.company_id_A = basedata.company_id

          LEFT JOIN (
            SELECT
                analytic_account, account_move.company_id AS company_id_B,
                SUM(CASE WHEN payment_type = 'inbound' AND es_anticipo = TRUE THEN amount ELSE 0 END) AS anticipo,
                SUM(CASE WHEN payment_type = 'outbound' AND es_anticipo = TRUE THEN amount ELSE 0 END) AS anticipos_proveedor,
                SUM(CASE WHEN payment_type = 'outbound' THEN amount ELSE 0 END) AS pagado
            FROM account_payment thepayment
            LEFT JOIN account_move ON thepayment.move_id = account_move.id
            WHERE state = 'posted'
            GROUP BY analytic_account, company_id_B

            ) anticipos ON anticipos.analytic_account = basedata.id AND company_id_B = company_id

            LEFT JOIN (
              SELECT
                  SUM(CASE WHEN COALESCE(template.tipo_de_gasto, category.tipo_de_gasto) = 'honorarios' THEN line.price_total ELSE 0 END) AS honorarios_obra,
                  SUM(CASE WHEN COALESCE(template.tipo_de_gasto, category.tipo_de_gasto) = 'mano de obra' THEN line.price_total ELSE 0 END) AS mano_de_obra,
                  SUM(CASE WHEN COALESCE(template.tipo_de_gasto, category.tipo_de_gasto) = 'costo directo' THEN line.price_total ELSE 0 END) AS costo_directo,
                  SUM(CASE WHEN COALESCE(template.tipo_de_gasto, category.tipo_de_gasto) = 'impuestos' THEN line.price_total ELSE 0 END) AS impuestos,
                  SUM(CASE WHEN COALESCE(template.tipo_de_gasto, category.tipo_de_gasto) = 'administrativo' THEN line.price_total ELSE 0 END) AS cuota_admin,
                  move.x_studio_cuenta_analitica,
                  move.company_id AS company_id_C
              FROM account_move_line line
              INNER JOIN account_move move ON move.id = line.move_id
              LEFT JOIN product_product product ON product.id = line.product_id
              LEFT JOIN product_template template ON product.product_tmpl_id = template.id
              LEFT JOIN product_category category ON template.categ_id = category.id
              WHERE move.move_type IN ('in_invoice', 'in_refund') AND
                    NOT line.exclude_from_invoice_tab AND
                    move.state NOT IN ('draft', 'cancel') AND
                    COALESCE(move.x_studio_nota_de_crdito_interna, FALSE) = FALSE
              GROUP BY move.x_studio_cuenta_analitica, company_id_C
            ) costos ON costos.x_studio_cuenta_analitica = basedata.id AND company_id_C = company_id
          '''

    @api.model
    def _where(self):
        return 'WHERE company_id = {}'.format(self.env.company.id)
