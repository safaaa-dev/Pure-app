# __manifest__.py

{
    'name': 'Daily Comparison Report',
    'version': '1.0.4',
    'category': 'eCommerce',
    'license': 'OPL-1',
    'summary': 'This plugin helps to follow-up and managing customer',
    'description': "Daily Comparison Report plugin serves as a valuable tool for eCommerce businesses providing essential functionalities for customer relationship management and performance monitoring. ",
    'author': "Pure IT Solutions",
    'depends': ['base', 'crm', 'sale', 'stock'],
    'data': [
        'views/followup_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    "images":["static/description/odoo-CRM-sales.png"],
}
