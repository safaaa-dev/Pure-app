from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ajex_order_type_ids = fields.Selection(
        [('COD', 'COD'), ('PREPAID', 'PREPAID')], default='PREPAID', string='Package Order Type')