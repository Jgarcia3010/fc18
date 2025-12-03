# -*- coding: utf-8 -*-

from odoo import api, models, sql_db, fields, _
from decimal import Decimal, ROUND_HALF_UP
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from datetime import datetime

# SAT LAW REFERENCE AS 2019-11-25 for Agentes Retenedores de IVA
# ---------------------------------------------------------------------------------------------------------------
# |         AGENTE RETENCION        |      Producto / Operacion      |  % Retencion  |    Retener a partir de   |
# |-------------------------------------------------------------------------------------------------------------|
# | Exportadores                    | Agrícolas y pecuarios          |       65 %    |       Q 2,500.00         |
# |                                 | Producto no agropecuarios      |       15 %    |       Q 2,500.00         |
# |                                 | Bienes o servicios             |       15 %    |       Q 2,500.00         |
# |-------------------------------------------------------------------------------------------------------------|
# | Beneficiarios del Decreto 29-89 | Bienes o servicios             |       65 %    |       Q 2,500.00         |
# |-------------------------------------------------------------------------------------------------------------|
# | Sector publico                  | Bienes o servicios             |       25 %    |       Q 2,500.00         |
# |-------------------------------------------------------------------------------------------------------------|
# | Operadores de tarjetas de       | Pagos de tarjetahabientes      |       15 %    |    Cualquier Monto       |
# | Credito                         | Pago de combustibles           |      1.5 %    |    Cualquier Monto       |
# |-------------------------------------------------------------------------------------------------------------|
# | Contribuyentes especiales       | Bienes o servicios             |       15 %    |       Q 2,500.00         |
# |-------------------------------------------------------------------------------------------------------------|
# | Otros Agentes de retencion      | Bienes o servicios             |       15 %    |       Q 2,500.00         |
# |-------------------------------------------------------------------------------------------------------------|
#
# Escenarios adicionales
# En caso de ser pequeño contribuyente se aplica un 5% en todos los casoso
# En caso de ser ambos agentes retenedores de IVA no se aplica retención


class AccountMove(models.Model):
    _inherit = 'account.move'

    tax_withholding_isr = fields.Selection(
        [
            ('quarter_witholding', 'Sujeto a Pagos Trimestrales'),
            ('definitive_withholding', 'Sujeto a Retención Definitiva'),
            ('small_taxpayer_withholding', 'Pequeño Contribuyente')
        ], string="Régimen tributario", default="quarter_witholding"
    )

    tax_withholding_price = fields.Float(string='Monto de retención')
    tax_withholding_iva = fields.Selection(
        [
            ('no_witholding', 'No es agente rentenedor de IVA'),
            ('export', 'Exportadores'),
            ('decree_28_89', 'Beneficiarios del Decreto 28-89'),
            ('public_sector', 'Sector Público'),
            ('credit_cards_companies', 'Operadores de Tarjetas de Crédito y/o Débito'),
            ('special_taxpayer', 'Contribuyente Especiales'),
            ('special_taxpayer_export', 'Contribuyente Especial y Exportador'),
            ('others', 'Otros Agentes de Retención'),
            ('variable', 'Retención Variable')
        ], string='Retención IVA')

    tipo_gasto = fields.Selection([('compra', 'Compra/Bien'), ('servicio', 'Servicio'), ('importacion', 'Importación/Exportación'), ('combustible', 'Combustible'), ('mixto', 'Mixto')], string="Tipo de Gasto", default="compra")
    numero_viejo = fields.Char(string="Numero Viejo")
    serie_rango = fields.Char(string="Serie Rango")
    inicial_rango = fields.Integer(string="Inicial Rango")
    final_rango = fields.Integer(string="Final Rango")
    tax_withold_amount = fields.Monetary(string='Retención ISR')
    
    isr_withold_amount = fields.Monetary(string='Retención ISR')
    iva_withold_amount = fields.Monetary(string='Retención IVA')
    tax_withholding_amount_iva = fields.Monetary(string='Retención IVA')
    diario_facturas_por_rangos = fields.Boolean(string='Las facturas se ingresan por rango', help='Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción', related="journal_id.facturas_por_rangos")

    user_country_id = fields.Char(string="UserCountry", default=lambda self: self.env.company.country_id.code)

    # FEL fields - CORREGIDOS (Campos normales en lugar de related)
    serie = fields.Char(string='Serie')
    dte_number = fields.Char(string='Número', related="payment_reference")

    type_invoice = fields.Selection(
        [
            ('normal_invoice', 'Factura normal'),
            ('special_invoice', 'Factura especial'),
            ('cambiaria', 'Factura Cambiaria'),
            ('cambiaria_exp', 'Factura Cambiaria Exp.'),
            ('credito_exp', 'Nota de Crédito Exp.'),
            ('nota_debito', 'Nota de Débito'),
            ('debito_exp', 'Nota de Débito Exp.'),
            ('nota_abono', 'Nota de Abono')
        ], string='Tipo de factura', default='normal_invoice')

    ref_analytic_line_ids = fields.One2many('account.analytic.line', 'id', string='Analytic lines')
    show_analytic_lines = fields.Boolean(store=False)
    bank_operation_ref = fields.Char(string="Referencia bancaria")
    provider_invoice_serial = fields.Char(string="Factura serie")
    provider_invoice_number = fields.Char(string="Factura número", related="ref")
    
    """
    #############################
    ### Assets Capitalization ###
    #############################
    """
    # Invoice reference for the capitalization move
    capitalization_invoice_id = fields.Many2one('account.move', string="Factura de capitalización")
    
    # CORRECCIÓN: Cambiado de Monetary a Many2one para solucionar el DatatypeMismatch
    capitalization_move_id = fields.Many2one('account.move', string="Asiento de capitalización")

    iva_withhold_value = fields.Monetary(
        string='Retención IVA'
    )
    
    """
    def write(self, vals):
        for rec in self:
            
            changed_amount = False

            if 'isr_withold_amount' in vals:
                sum_validation = float(vals['isr_withold_amount']) - float(rec.isr_withold_amount)
                print('Sum validation', sum_validation, float(vals['isr_withold_amount']), float(rec.isr_withold_amount))
                if sum_validation!= 0:
                    changed_amount = True
                    
            print('Changed Amount', changed_amount)
            res = super(AccountMove, rec).write(vals)
            
            #if rec.move_type == "in_invoice":
            #    if changed_amount:
            #        rec.check_isr_lines()
                
            return res
    """
    @api.model
    def create(self, values):
        res = super(AccountMove, self).create(values)
        res.tax_withholding_isr = res.partner_id.tax_withholding_isr
        return res

    def action_cancel(self):
        for rec in self:
            rec.numero_viejo = rec.name
        return super(AccountMove, self).action_cancel()
    
    def check_isr_iva_lines(self):
        return