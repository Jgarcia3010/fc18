# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # --- AGREGA ESTE CAMPO PARA CORREGIR EL ERROR ---
    tipo_de_gasto = fields.Selection([
        ('compra', 'Compra/Bien'),
        ('servicio', 'Servicio'),
        ('combustible', 'Combustible'),
        ('mixto', 'Mixto'),
        ('importacion', 'Importación')
    ], string="Tipo de Gasto", default='compra')
    # ------------------------------------------------

    @api.constrains('x_studio_bien_o_servicio')
    def _constraint_x_studio_bien_o_servicio(self):
        if self.x_studio_bien_o_servicio and self.x_studio_bien_o_servicio not in ['articulo', 'servicio', 'combustible']:
            raise ValidationError('El campo "Bien o servicio" debe contener uno de los siguiente valores: articulo, servicio, combustible')