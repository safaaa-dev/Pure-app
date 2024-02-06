from odoo import fields, models
import json

class City(models.Model):
    _name = 'ajex.city'
    _description = 'City'

    report_date = fields.Date(string='Report Date', required=True, default=fields.Date.context_today)
    won_opportunities_count = fields.Integer(string='Won Opportunities Count')
    sale_orders_count = fields.Integer(string='Sale Orders Count')
    sales_count = fields.Integer(string='Sales Count')


class Neighborhood(models.Model):
    _name = 'ajex.neighborhood'
    _description = 'Neighborhood'

    name = fields.Char(string='Neighborhood Name', required=True)
    city_id = fields.Many2one('ajex.city', string='City', required=True)

    def default(self):
        return {
            'name': self.name,
        }

