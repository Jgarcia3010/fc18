# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

class ResPartner(models.Model):
    _inherit = "res.partner"
    _name = "res.partner"

    exclude_libros = fields.Boolean(default = False, string="Excluir de libros de compras y ventas")
