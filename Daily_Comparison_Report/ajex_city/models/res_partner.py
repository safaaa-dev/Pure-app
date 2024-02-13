from odoo import fields, models
import json

class City(models.Model):
    _name = 'ajex.city'
    _description = 'City'

    name = fields.Char(string='City Name', required=True)


class Neighborhood(models.Model):
    _name = 'ajex.neighborhood'
    _description = 'Neighborhood'

    name = fields.Char(string='Neighborhood Name', required=True)
    city_id = fields.Many2one('ajex.city', string='City', required=True)

    def default(self):
        return {
            'name': self.name,
        }

