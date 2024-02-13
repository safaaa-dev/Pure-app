import logging
import requests
import json
from datetime import datetime
from odoo import models, fields, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[("ajex_provider", "AJEX")],
                                     ondelete={'ajex_provider': 'set default'})
    ajex_provider_package_id = fields.Many2one('stock.package.type', string="Package Info", help="Default Package")

    ajex_service_type_id = fields.Selection(
        [('AJEX ICX', 'AJEX ICX'), ('DOMESTIC E-COMMERCE EXPRESS', 'DOMESTIC E-COMMERCE EXPRESS'),
         ('AJEX IRX', 'AJEX IRX')], default='DOMESTIC E-COMMERCE EXPRESS', string='Package Service Type')


    def check_address_details(self, address_id, required_fields):
        """
            check the address of Shipper and Recipient
            param : address_id: res.partner, required_fields: ['country_id', 'street']
            return: missing address message
        """

        res = [field for field in required_fields if not address_id[field]]
        if res:
            return "Missing Values For Address :\n %s" % ", ".join(res).replace("_id", "")

    def ajex_provider_rate_shipment(self, order):
        """
           This method is used for get rate of shipment
           param : order : sale.order
           return: 'success': False : 'error message' : True
           return: 'success': True : 'error_message': False
        """
        # Shipper and Recipient Address
        shipper_address_id = order.warehouse_id.partner_id
        recipient_address_id = order.partner_shipping_id

        shipper_address_error = self.check_address_details(shipper_address_id, ['zip', 'city', 'country_id', 'street'])
        recipient_address_error = self.check_address_details(recipient_address_id,
                                                             ['zip', 'city', 'country_id', 'street'])
        total_weight = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0

        product_weight = (order.order_line.filtered(
            lambda x: not x.is_delivery and x.product_id.type == 'product' and x.product_id.weight <= 0))
        product_name = ", ".join(product_weight.mapped('product_id').mapped('name'))

        if shipper_address_error or recipient_address_error or product_name:
            return {'success': False, 'price': 0.0,
                    'error_message': "%s %s  %s " % (
                        "Shipper Address : %s \n" % (shipper_address_error) if shipper_address_error else "",
                        "Recipient Address : %s \n" % (recipient_address_error) if recipient_address_error else "",
                        "product weight is not available : %s" % (product_name) if product_name else ""
                    ),
                    'warning_message': False}
        try:
            header = {'Content-Type': 'application/json'}
            api_url = ""
            request_data = {}
            request_type = "POST"
            response_status, response_data = self.ajex_provider_create_shipment(request_type, api_url, request_data,
                                                                                header)
            if response_status:
                return {'success': True, 'price': 0.0,
                        'error_message': False, 'warning_message': False}
            else:
                return {'success': False, 'price': 0.0,
                        'error_message': response_data, 'warning_message': False}
        except Exception as e:
            return {'success': False, 'price': 0.0,
                    'error_message': e, 'warning_message': False}

    def ajex_provider_retrive_single_package_info(self, height=False, width=False, length=False, weight=False,
                                                  package_name=False, package_id=False, default_package_id=False):
        cargo_info_list = []
        if package_id:
            for product_ifo in package_id.quant_ids:
                cargo_info_value = {
                    "name": product_ifo.product_id and product_ifo.product_id.name,
                    "count": product_ifo.available_quantity,
                    "totalValue": (product_ifo.available_quantity * product_ifo.product_id.list_price),
                    "hsCode": product_ifo.product_id.hs_code,
                    "countryOfOrigin": product_ifo.product_id.country_of_origin.name
                }
                cargo_info_list.append(cargo_info_value)
        if default_package_id:
            for product_ifo in default_package_id:
                cargo_info_value = {
                    "name": product_ifo.product_id and product_ifo.product_id.name,
                    "count": product_ifo.qty_done,
                    "totalValue": (product_ifo.qty_done * product_ifo.product_id.list_price),
                    "hsCode": product_ifo.product_id.hs_code,
                    "countryOfOrigin": product_ifo.product_id.country_of_origin.name
                }
                cargo_info_list.append(cargo_info_value)

        return {
            "weight": weight,
            "length": length,
            "width": width,
            "height": height,
            "quantity": sum(package_id.quant_ids.mapped('available_quantity')) if package_id else sum(
                default_package_id.mapped('qty_done')),
            "cargoInfo": cargo_info_list
        }

    def ajex_provider_packages(self, picking):
        package_list = []
        weight_bulk = picking.weight_bulk
        package_ids = picking.package_ids

        for package_id in package_ids:
            height = package_id.package_type_id and package_id.package_type_id.height or 0
            width = package_id.package_type_id and package_id.package_type_id.width or 0
            length = package_id.package_type_id and package_id.package_type_id.packaging_length or 0
            weight = package_id.shipping_weight
            package_name = package_id.name
            package_list.append(
                self.ajex_provider_retrive_single_package_info(height, width, length, weight, package_name, package_id,
                                                               default_package_id=False))
        if weight_bulk:
            default_package_id = picking.move_ids.move_line_ids.filtered(lambda move: not move.result_package_id)
            height = self.ajex_provider_package_id and self.ajex_provider_package_id.height or 0
            width = self.ajex_provider_package_id and self.ajex_provider_package_id.width or 0
            length = self.ajex_provider_package_id and self.ajex_provider_package_id.packaging_length or 0
            weight = weight_bulk
            package_name = picking.name
            package_list.append(
                self.ajex_provider_retrive_single_package_info(height, width, length, weight, package_name,
                                                               package_id=False, default_package_id=default_package_id))
        return package_list

    def ajex_provider_create_shipment(self, request_type, api_url, request_data, header):
        _logger.info("Shipment Request API URL:::: %s" % api_url)
        _logger.info("Shipment Request Data:::: %s" % request_data)
        response_data = requests.request(method=request_type, url=api_url, headers=header, data=request_data)
        if response_data.status_code in [200, 201]:
            response_data = json.loads(response_data.text)
            _logger.info(">>> Response Data {}".format(response_data))
            return True, response_data
        else:
            return False, response_data.text

    def ajex_provider_send_shipping(self, picking):
        shipper_address_id = picking.picking_type_id and picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.partner_id
        recipient_address_id = picking.partner_id
        company_id = self.company_id
        tracking_number = ""
        shipper_address_error = self.check_address_details(shipper_address_id, ['zip', 'city', 'country_id', 'street'])
        recipient_address_error = self.check_address_details(recipient_address_id,
                                                             ['country_id', 'street'])
        if shipper_address_error or recipient_address_error or not picking.shipping_weight:
            raise ValidationError("%s %s  %s " % (
                "Shipper Address : %s \n" % (shipper_address_error) if shipper_address_error else "",
                "Recipient Address : %s \n" % (recipient_address_error) if recipient_address_error else "",
                "Shipping weight is missing!" if not picking.shipping_weight else ""
            ))

        sender_zip = shipper_address_id.zip or ""
        sender_city = shipper_address_id.city or ""
        sender_country_code = shipper_address_id.country_id and shipper_address_id.country_id.code or ""
        sender_state_code = shipper_address_id.state_id and shipper_address_id.state_id.code or ""
        sender_street = shipper_address_id.street or ""
        sender_phone = shipper_address_id.phone or ""
        sender_email = shipper_address_id.email or ""

        receiver_zip = recipient_address_id.zip or ""
        receiver_city = recipient_address_id.city or ""
        receiver_country_code = recipient_address_id.country_id and recipient_address_id.country_id.code or ""
        receiver_country_name = recipient_address_id.country_id and recipient_address_id.country_id.name or ""
        receiver_state_code = recipient_address_id.city_id and recipient_address_id.city_id.name or ""
        receiver_district = recipient_address_id.neighborhood_id and recipient_address_id.neighborhood_id.name or ""
        receiver_street = recipient_address_id.street or ""
        receiver_street2 = recipient_address_id.street2 or ""
        receiver_phone = recipient_address_id.phone or ""
        receiver_phone1 = recipient_address_id.phone or ""
        receiver_phone = receiver_phone.replace(" ", "").replace("+", "")[3:]
        receiver_email = recipient_address_id.email or ""

        weight_bulk = picking.weight_bulk
        package_ids = picking.package_ids
        total_packages = len(package_ids) + 1 if weight_bulk else 0
        packages = self.ajex_provider_packages(picking)
        order_type = picking.sale_id.ajex_order_type_ids

        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%dT%H:%M:%S.000+03:00")

        try:
            header = {
                'Authorization': 'Bearer {0}'.format(company_id.ajex_token),
                'Content-Type': 'application/json'
            }
            api_url = "{0}order-management/api/v2/order".format(company_id.ajex_api_url)
            request_data = ({
                "orderId": str(picking.origin or picking.id or ""),
                "orderTime": dt_string,
                "productCode": "SE0123",
                "expressType": self.ajex_service_type_id,
                "totalDeclaredValue": picking.sale_id and picking.sale_id.amount_total,
                "declaredCurrency": recipient_address_id.country_id and recipient_address_id.country_id.currency_id and recipient_address_id.country_id.currency_id.name,
                "parcelTotalWeight": total_packages,
                "pickupMethod": "PICKUP",
                "paymentMethod": "SENDER_INSTALLMENT",
                "customerAccount": company_id.ajax_customer_account,
                "buyerName": recipient_address_id.name,
                "senderInfo": {
                    "name": shipper_address_id.name,
                    "phone": "+971542506770",
                    "email": sender_email,
                    "contactType": "INDIVIDUAL",
                    "addressType": "LOOKUP",
                    "country": shipper_address_id.country_id.name,
                    "countryCode": sender_country_code,
                    "city": "Ajman",
                    "district": "Ajman",
                    "detailedAddress": "Horizon Towers - Tower D - Floor number 18 - Office No. 1802"
                },
                "receiverInfo": {
                    "name": recipient_address_id.name,
                    "phone": receiver_phone,
                    "email": "customer@gastrozero.com",
                    "contactType": "INDIVIDUAL",
                    "addressType": "LOOKUP",
                    "country": receiver_country_name,
                    "countryCode": receiver_country_code,
                    "city": receiver_state_code,
                    "district": receiver_district,
                    "detailedAddress": receiver_street,
                },
                "parcels": [
                {
                    "weight": 0.5,
                    "cargoInfo": [
                        {

                            "name": str(
                                picking.sale_id and picking.sale_id.sale_order_template_id and picking.sale_id.sale_order_template_id.name or ""),
                            "count": 1,
                            "totalValue": float(picking.sale_id and picking.sale_id.order_line[0] and picking.sale_id.order_line[0].price_subtotal * 0.10 or 0),
                            "hsCode": "21069093",
                            "countryOfOrigin": "United Arab Emirates"
                        }

                    ]
                },
            ],
            })
            if order_type == "PREPAID":
                prepaid_order = request_data
                prepaid_order.update({"addedServices": [
                    {
                        "serviceName": "IN01",
                        "val1": picking.sale_id and picking.sale_id.amount_total,
                        "val2": recipient_address_id.country_id and recipient_address_id.country_id.currency_id and recipient_address_id.country_id.currency_id.name
                    }
                ]})

            request_type = "POST"
            response_status, response_data = self.ajex_provider_create_shipment(request_type, api_url, json.dumps(request_data),
                                                                                header)
            if response_status and response_data.get('waybillNumber'):
                tracking_number = response_data.get('waybillNumber')
                pdf_url = response_data.get('waybillFileUrl')

                headers = {'Content-Type': "application/x-www-form-urlencoded", 'Accept': "application/pdf"}
                pdf_response = requests.request("GET", url=pdf_url, headers=headers)
                logmessage = ("<b>Tracking Numbers:</b> %s") % (tracking_number)
                picking.message_post(body=logmessage,
                                     attachments=[
                                         ("%s.pdf" % (tracking_number), pdf_response.content)])
                shipping_data = {'exact_price': 0.0, 'tracking_number': tracking_number}
                shipping_data = [shipping_data]
                return shipping_data
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e)

    def ajex_provider_cancel_shipment(self, picking):
        company_id = self.company_id
        api_url = "https://apps-sit.aj-ex.com/order-management/api/v1/cancel-order"
        request_data = json.dumps({
            "waybillNumber": picking.carrier_tracking_ref
        })
        request_type = "POST"
        header = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {0}'.format(company_id.ajex_token)
        }
        try:
            response_status, response_data = self.ajex_provider_create_shipment(request_type, api_url, request_data,
                                                                                header)
            if response_status and response_data:
                delete_shipment_result = response_data.get('responseMessage')
                if delete_shipment_result == 'Success':
                    picking.carrier_tracking_ref = ''
                    _logger.info("Successfully deleted shipment in AJAX")
                else:
                    raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e)

    def ajex_provider_get_tracking_link(self, picking):
        company_id = self.company_id
        count_delivery_fail = 0
        awb_number = picking.carrier_tracking_ref.split(',')[0]

        api_url = "https://apps.aj-ex.com/order-management/api/v1/order-tracking/{0}".format(
            picking.carrier_tracking_ref)
        request_data = {}
        request_type = "GET"
        header = {
            'Authorization': 'Bearer {0}'.format(company_id.ajex_token),
        }

        response_status, response_data = self.ajex_provider_create_shipment(request_type, api_url, request_data, header)

        if response_status and response_data:
            if isinstance(response_data, str):
                raise ValidationError(response_data)
            else:
                # معالجة الاستجابة الناجحة وتعيين القيم للحقول اللازمة
                status_ids = response_data.get('orderTrackingHistory', [])
                for status in status_ids:
                    picking.ajex_shipment_status = status.get('note')
                    picking.ajex_shipment_note = status.get('status')
                    status_code_count = status.get('statusCode')
                    if status_code_count == 70:
                        count_delivery_fail += 1
                picking.ajex_delivery_attempt = count_delivery_fail
                
                return 'https://ajex.customerportalnew.shipsy.io/consignments/details/{0}'.format(awb_number)
        else:
            if isinstance(response_data, str):
                raise ValidationError(response_data)
            else:
                raise ValidationError("Unknown error occurred during tracking.")
        raise ValidationError(e)