from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ajex_shipment_status = fields.Char(string="AJAX Shipment Status", copy=False, readonly=1)
    ajex_shipment_note = fields.Char(string="AJAX Shipment Note", copy=False, readonly=1)
    ajex_delivery_attempt = fields.Char(string="Attempt ", copy=False, readonly=1)


    ajex_shipment_status_push = fields.Char(string="AJAX Shipment Push Status", copy=False, readonly=1)

    def ajax_tracking_statu(self):
        if self.carrier_tracking_ref:
            try:
                self.carrier_id.ajex_provider_get_tracking_link(self)
            except Exception as e:
                raise ValidationError(e)

    @api.model
    def run_ajax_tracking_statu(self):
        # ادخل هنا الشروط إذا كنت ترغب في تنفيذها بناءً على شروط معينة
        records_to_process = self.search([])
        records_to_process.ajax_tracking_statu()

    def ajax_tracking_status(self, *args, **kwargs):
        pickings = self.env['stock.picking'].search([
            ('state', 'in', ['done', 'cancel']),
            ('carrier_tracking_ref', '!=', False),
            ('carrier_id', '=', 9)
        ])

        for picking in pickings:
            try:
                picking.carrier_id.ajex_provider_get_tracking_link(picking)
            except Exception as e:
                raise ValidationError(e)

        
        # if self.carrier_tracking_ref:
        #     try:
        #         self.carrier_id.ajex_provider_get_tracking_link(self)
        #     except Exception as e:
        #         raise ValidationError(e)
        # pickings = self.env['stock.picking'].search(
        #     [('state', 'in', ['done', 'cancel']),
        #      ('carrier_tracking_ref', '!=', False),
        #      ('carrier_id', '=',9)
        #      ])
        # for picking in pickings:
        #     picking.ajex_provider_get_tracking_link(picking)
        #
    



