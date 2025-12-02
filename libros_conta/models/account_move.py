# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

class AccountMove(models.Model):
    _inherit = "account.move"

    anticipo = fields.Boolean(default=False, string="Anticipo")

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tree_level1_ = fields.Many2one('account.account',
        string="Nivel 1", ondelete="set null", store=True, compute='_compute_levels'
    )
    tree_level2_ = fields.Many2one('account.account',
        string="Nivel 2", ondelete="set null", store=True, compute='_compute_levels'
    )
    tree_level3_ = fields.Many2one('account.account',
        string="Nivel 3", ondelete="set null", store=True, compute='_compute_levels'
    )

    @api.depends('account_id', 'account_id.code', 'company_id')
    def _compute_levels(self):
        for line in self:
            try:
                # Inicializar valores
                line.tree_level1_ = False
                line.tree_level2_ = False
                line.tree_level3_ = False

                # Validaciones de seguridad
                if not line.account_id or not line.account_id.code or not line.company_id:
                    continue

                code = str(line.account_id.code).strip()
                
                # Nivel 1 - primer carácter
                if len(code) >= 1:
                    level1_code = code[0]
                    level1_account = self.env["account.account"].search([
                        ('code', '=', level1_code),
                        ('company_id', '=', line.company_id.id),
                    ], limit=1)
                    if level1_account:
                        line.tree_level1_ = level1_account

                # Nivel 2 - primeros 2 caracteres
                if len(code) >= 2:
                    level2_code = code[0:2]
                    level2_account = self.env["account.account"].search([
                        ('code', '=', level2_code),
                        ('company_id', '=', line.company_id.id),
                    ], limit=1)
                    if level2_account:
                        line.tree_level2_ = level2_account

                # Nivel 3 - primeros 4 caracteres
                if len(code) >= 4:
                    level3_code = code[0:4]
                    level3_account = self.env["account.account"].search([
                        ('code', '=', level3_code),
                        ('company_id', '=', line.company_id.id),
                    ], limit=1)
                    if level3_account:
                        line.tree_level3_ = level3_account

            except Exception as e:
                # En caso de error, continuar con la siguiente línea
                logging.warning(f"Error computing levels for account move line {line.id}: {str(e)}")
                continue
