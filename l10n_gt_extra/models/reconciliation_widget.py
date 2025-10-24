# -*- coding: utf-8 -*-

import copy
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import formatLang, format_date, parse_date


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _prepare_move_lines(self, move_lines, target_currency=False, target_date=False, recs_count=0):

        ret = super(AccountReconciliation, self)._prepare_move_lines(move_lines)
        context = dict(self._context or {})
        ret_bank_ref = []
        ret_counter = 0
        for line in move_lines:
            ret[ret_counter]['bank_operation_ref'] = line.move_id.bank_operation_ref or ''
            ret_counter += 1

        return ret

    @api.model
    def _domain_move_lines_for_reconciliation(self, st_line, aml_accounts, partner_id, excluded_ids=[], search_str=False, mode='rp'):
        domain = super(AccountReconciliation, self)._domain_move_lines_for_reconciliation(st_line, aml_accounts, partner_id, excluded_ids, search_str)
        domain = expression.OR([domain, [('move_id.bank_operation_ref', 'ilike', search_str)]])
        return domain
