from odoo import models, fields, api, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    exclude_libros = fields.Boolean(default = False, string="Excluir de libros de compras y ventas")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    exclude_libros = fields.Boolean(default = False, string="Excluir de libros de compras y ventas")
    exclude_reporte_costos = fields.Boolean(default = False, string="Excluir de reporte de costos(facturas)")