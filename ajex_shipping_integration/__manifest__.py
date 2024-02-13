# -*- coding: utf-8 -*-pack
{

    # App information
    'name': 'AJEX Shipping Integration',
    'category': 'Website',
    'version': '16.0.0',
    'summary': """Using AJAX Easily manage Shipping Operation in odoo.Export Order While Validate Delivery Order.Import Tracking From AJEX to odoo.Generate Label in odoo.We also Provide the ups,fedex,dhl express shipping integration.""",
    'license': 'OPL-1',

    # Dependencies
    'depends': ['delivery'],

    # Views
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'view/res_company.xml',
        'view/sale_order.xml',
        'view/stock_picking.xml',
        'view/delivery_carrier.xml',
    ],
    # Odoo Store Specific
    'images': ['static/description/cover.jpg'],

    # Author
    'author': 'Vraja Technologies',
    'website': 'http://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'price': '199',
    'currency': 'EUR',

}
# version changelog
