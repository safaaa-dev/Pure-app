import requests
import logging

from odoo import models, fields
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import json

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    use_ajex_shipping_provider = fields.Boolean(copy=False, string="Are You Use AJEX Shipping Provider.?",
                                                help="If use AJEX shipping provider than value set TRUE.",
                                                default=False)
    ajex_api_url = fields.Char(string="API URL", copy=False, default="https://apps-sit.aj-ex.com/")

    ajex_username = fields.Char(string="Username", copy=False)
    ajex_password = fields.Char(string="Password", copy=False)
    ajex_token = fields.Char(string="Bearer Token", copy=False, readonly=1)
    ajax_customer_account = fields.Char(string="Account Number", copy=False)


    def get_ajax_token(self):
        url = "{0}authentication-service/api/auth/login".format(self.ajex_api_url)
        payload = json.dumps({
            "username": self.ajex_username,
            "password": self.ajex_password
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code in [200]:
            self.ajex_token = json.loads(response.text).get("accessToken")
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "Yeah! Token Get Successfully.",
                    'img_url': '/web/static/img/smile.svg',
                    'type': 'rainbow_man',
                }
            }
        else:
            raise ValidationError(response.content)



    def ajax_generate_authentication_token_using_crone(self, ):
        for credential_id in self.search([]):
            try:
                if credential_id.use_ajex_shipping_provider:
                    credential_id.get_ajax_token()
            except Exception as e:
                _logger.info("Getting an error in Generate Token request Odoo to AJEX: {0}".format(e))