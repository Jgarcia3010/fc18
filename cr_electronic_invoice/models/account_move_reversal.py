from odoo import models, fields

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    reference_code_id = fields.Many2one(
        'some.model',  # Cambia 'some.model' por el modelo que corresponda
        string="Código Referencia"
    )
    reference_document_id = fields.Many2one(
        'some.model',  # Cambia 'some.model' por el modelo que corresponda
        string="Documento Referencia"
    )
