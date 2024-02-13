import json
import logging
import requests
from odoo import http
from odoo.http import request
_logger = logging.getLogger(__name__)



class ShipmentStatusUpdater(http.Controller):

    @http.route('/retrieve_status/', type='http', auth="public", methods=['POST'], csrf=False)
    def update_shipment_status(self, **kw):
        try:
            # content_type = request.httprequest.headers.get('Content-Type')
            # if content_type != 'application/json':
            #     return Response('Unsupported Media Type', status=415)
            request_data = json.loads(request.httprequest.get_data())

            _logger.info('Received shipment status update data: %s' % (request_data))

            if 'waybillNo' in request_data and 'statusCode' in request_data and 'statusName' in request_data and 'updateTime' in request_data and 'note' in request_data and 'orderId' in request_data:
                waybillNo = request_data['waybillNo']
                shipment_status = request_data['note']
                updateTime = request_data['updateTime']


                picking = request.env['stock.picking'].search([('carrier_tracking_ref', '=', waybillNo)], limit=1)
                if picking:
                    picking.write({
                        'ajex_shipment_status_push': shipment_status
                    })
                    picking.write({
                        'x_updateTime': updateTime
                    })
                    _logger.info('Shipment Status Updated: %s' % (request_data))
                    response = {
                        "responseCode": "100",
                        "responseMessage": "Success"
                    }
                    return json.dumps(response)
                else:
                    _logger.warning('Shipment Not Found for waybillNo : %s' % (waybillNo))
                    response = {
                        "responseCode": "401",
                        "responseMessage": "Shipment Not Found"
                    }
                    return json.dumps(response)
            else:
                _logger.warning('Data is missing or invalid')
                response = {
                    "responseCode": "403",
                    "responseMessage": "Data is missing or invalid"
                }
                return json.dumps(response)
            
        except Exception as e:
            _logger.error(str(e))
            response = {
                "responseCode": "500",
                "responseMessage": "Internal Server Error"
            }

            return json.dumps(response)
