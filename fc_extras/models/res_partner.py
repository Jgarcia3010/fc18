# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, values):
        user_id = self.env['res.users'].browse(self._uid)
        allowed_values = 'reminder_date_before_receipt' in values.keys() or 'receipt_reminder_email' in values.keys()
        user_allowed_to_write = user_id.has_group('fc_extras.fc_res_partner_admin') or allowed_values
        if user_allowed_to_write:
            return super(ResPartner, self).write(values)
        else:
            raise UserError('No tienes permiso para editar contactos')