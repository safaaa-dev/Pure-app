from odoo import models, fields


class PackageDetails(models.Model):
    _inherit = 'stock.package.type'

    package_carrier_type = fields.Selection(selection_add=[("ajex_provider", "AJEX")],
                                            ondelete={'ajex_provider': 'set default'})
