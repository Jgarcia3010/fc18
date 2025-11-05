# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CabysCode(models.Model):
    _name = 'cabys.code'
    _description = 'Códigos CABYS'
    _order = 'name'

    name = fields.Char(string='Código CABYS', required=True)
    parent_id = fields.Many2one('cabys.code', string='Padre')
    partner_ids = fields.Many2many(
        'res.partner',
        'partner_cabys_rel',
        'cabys_id',
        'partner_id',
        string='Partners'
    )
    active = fields.Boolean(default=True)