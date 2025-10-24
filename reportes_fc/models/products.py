from odoo import models, fields, api, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    tipo_de_gasto = fields.Selection([
        ('honorarios', 'Honorarios de obra'),
        ('mano de obra', 'Mano de obra'),
        ('costo directo', 'Costo directo'),
        ('impuestos', 'Impuestos'),
        ('administrativo', 'Cuota administrativa')
    ], default = None, string="Tipo de gasto", help="Honorarios, materiales o costos directos.")



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tipo_de_gasto = fields.Selection([
        ('honorarios', 'Honorarios de obra'),
        ('mano de obra', 'Mano de obra'),
        ('costo directo', 'Costo directo'),
        ('impuestos', 'Impuestos'),
        ('administrativo', 'Cuota administrativa')
    ], default = None, string="Tipo de gasto", help="Honorarios, materiales o costos directos.")
