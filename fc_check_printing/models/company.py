# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class CompanyExtraFields(models.Model):
    _inherit = "res.company"

    account_check_printing_layout = fields.Selection(
      selection_add=[
        ('fc_check_printing.action_print_check', 'Cheques FC'),
        ('fc_check_printing.action_print_check_3', 'Cheques FC 3'),
      ], 
      ondelete={
          'fc_check_printing.action_print_check': 'set default'
      }
    )
