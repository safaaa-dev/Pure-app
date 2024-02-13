from odoo import models, fields, api
from datetime import timedelta


class DailySalesReport(models.Model):
    _name = 'daily.sales.report'
    _description = 'Daily Sales Report'
    _inherit = 'mail.thread'

    report_date = fields.Date(string='Report Date', required=True, default=fields.Date.context_today)
    won_opportunities_count = fields.Integer(string='Won Opportunities Count',
                                             compute='_compute_won_opportunities_count', store=True)
    sale_orders_count = fields.Integer(string='Sale Orders Count',
                                       compute='_compute_sale_orders_count', store=True)
    sales_count = fields.Integer(string='Sales Count',
                                 compute='_compute_sales_count', store=True)
    delivery_orders_count = fields.Integer(string='Delivery Orders Count',
                                           compute='_compute_delivery_orders_count')
    account_invoices_count = fields.Integer(string='Account Invoices Count',
                                            compute='_compute_account_invoices_count')

    delivered_delivery_orders_count = fields.Integer(string='Delivered Delivery Orders Count',
                                                     compute='_compute_delivered_delivery_orders_count')


    @api.depends('report_date')
    def _compute_won_opportunities_count(self):
        for record in self:
            stage_id = self.env['crm.stage'].search([('name', '=', 'Confirm')], limit=1)
            record.won_opportunities_count = self.env['crm.lead'].search_count([
                ('stage_id', '=', stage_id.id),
                ('create_date', '<=', record.report_date + timedelta(days=1)),
            ])

    state = fields.Selection([
        ('draft', 'Draft'),
        ('not_matching', 'Not Matching'),
        ('matching', 'Matching'),


    ], string='Status', default='draft', readonly=True, states={'draft': [('readonly', False)]})

    def action_set_matching(self):
        self.state = 'matching'
        self.message_post(body="تم تغيير الحالة إلى 'Matching'.")

    def action_set_not_matching(self):
        self.state = 'not_matching'
        self.message_post(body="تم تغيير الحالة إلى 'Not Matching'.")

    def action_set_draft(self):
        self.state = 'draft'
        self.message_post(body="تم تغيير الحالة إلى 'Draft'.")

    @api.depends('report_date')
    def _compute_sale_orders_count(self):
        for record in self:
            record.sale_orders_count = self.env['sale.order'].search_count([
                ('date_order', '<=', record.report_date + timedelta(days=1)),
            ])

    @api.depends('report_date')
    def _compute_sales_count(self):
        for record in self:
            record.sales_count = self.env['sale.order'].search_count([
                ('state', '=', 'sale'),
                ('create_date', '<=', record.report_date + timedelta(days=1)),
            ])

    @api.depends('report_date')
    def _compute_delivery_orders_count(self):
        for record in self:
            # احسب عدد الطلبات التي ذهبت إلى العملاء
            delivered_orders = self.env['stock.picking'].search([
                ('picking_type_code', '=', 'outgoing'),
                ('custom_stage_id', '!=', False),
                ('create_date', '<=', record.report_date + timedelta(days=1)),
            ])
            # احسب عدد طلبات التوصيل
            record.delivery_orders_count = len(delivered_orders)

    @api.depends('report_date')
    def _compute_account_invoices_count(self):
        for record in self:
            invoices_count = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('x_studio_many2one_field_noId2', '!=', 'zz'),
                ('invoice_date_due', '<=', record.report_date + timedelta(days=1)),
            ])
            # قم بتحديث حقل عدد الفواتير
            record.account_invoices_count = len(invoices_count)

    @api.depends('report_date')
    def _compute_delivered_delivery_orders_count(self):
        for record in self:
            delivered_orders = self.env['stock.picking'].search([
                ('picking_type_code', '=', 'outgoing'),  # افحص طلبات التوصيل الخارجية فقط
                ('custom_stage_id', '=', 'تم التسليم'),  # افحص الطلبات التي تم تسليمها فقط
                ('scheduled_date', '<=', record.report_date + timedelta(days=1)),
            ])
            # احسب عدد طلبات التوصيل
            record.delivered_delivery_orders_count = len(delivered_orders)

    @api.depends('report_date')
    def _compute_confirmation_ratio(self):
        for record in self:
            # حساب عدد الفرص المؤكدة في اليوم
            stage_id = self.env['crm.stage'].search([('name', '=', 'Confirm')], limit=1)
            confirmed_opportunities = self.env['crm.lead'].search_count([
                ('stage_id', '=', stage_id.id),
                ('type', '=', 'opportunity'),
                ('create_date', '<=', record.report_date),
            ])

            # حساب عدد الفرص التي تم إنشاؤها في اليوم
            created_opportunities = self.env['crm.lead'].search_count([
                ('create_date', '<=', record.report_date),
                ('type', '=', 'opportunity'),
            ])

            # حساب نسبة التأكيد
            confirmation_ratio = (confirmed_opportunities / created_opportunities) * 100

            # تحديث حقل نسبة التأكيد
            record.confirmation_ratio = confirmation_ratio

    @api.depends('report_date')
    def _compute_confirmation_day(self):
        for record in self:
            # حساب عدد الفرص المؤكدة في اليوم
            stage_id = self.env['crm.stage'].search([('name', '=', 'Confirm')], limit=1)
            confirmed_opportunities = self.env['crm.lead'].search_count([
                ('stage_id', '=', stage_id.id),
                ('create_date', '<=', record.report_date + timedelta(days=1)),
                ('create_date', '>=', record.report_date),
                ('type', '=', 'opportunity'),
            ])

            # حساب عدد الفرص التي تم إنشاءها في اليوم
            created_opportunities = self.env['crm.lead'].search_count([
                ('create_date', '<=', record.report_date + timedelta(days=1)),
                ('create_date', '>=', record.report_date),
                ('type', '=', 'opportunity'),
            ])

            # التحقق من عدم القسمة على الصفر
            if created_opportunities != 0:
                confirmation_day = (confirmed_opportunities / created_opportunities) * 100
            else:
                confirmation_day = 0

            # تحديث حقل نسبة التأكيد
            record.confirmation_day = confirmation_day

    confirmation_ratio = fields.Float(string='Confirmation Ratio (%)', compute='_compute_confirmation_ratio',
                                      store=True)
    confirmation_day = fields.Float(string='Confirmation Ratio (%)', compute='_compute_confirmation_day',
                                    store=True)

    delivery_ratio = fields.Float(string='Delivery Ratio', compute='_compute_delivery_ratio',
                                        store=True)
    delivery_ratio_samsa = fields.Float(string='Delivery Ratio Samsa', compute='_compute_delivery_ratio_samsa',
                                        store=True)
    delivery_ratio_quick_silver = fields.Float(string='Delivery Ratio Quick Silver',
                                               compute='_compute_delivery_ratio_quick_silver', store=True)
    delivery_ratio_ajax = fields.Float(string='Delivery Ratio Ajax', compute='_compute_delivery_ratio_ajax', store=True)
    delivery_ratio_jordan = fields.Float(string='Delivery Ratio Jordan', compute='_compute_delivery_ratio_jordan',
                                         store=True)

    @api.depends('delivered_delivery_orders_count', 'delivery_orders_count')
    def _compute_delivery_ratio(self):
        for record in self:
            delivered_count_samsa = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),  # افحص طلبات التوصيل الخارجية فقط
                ('custom_stage_id', '=', 'تم التسليم'),
            ])
            total_count = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),
                ('custom_stage_id', '!=', 'في الشحن'),
            ])

            # تأكد من التحقق من قيمة total_count لتجنب القسمة على صفر
            record.delivery_ratio = (delivered_count_samsa / total_count) * 100 if total_count != 0 else 0

    @api.depends('delivered_delivery_orders_count', 'delivery_orders_count')
    def _compute_delivery_ratio_samsa(self):
        for record in self:
            delivered_count_samsa = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),  # افحص طلبات التوصيل الخارجية فقط
                ('custom_stage_id', '=', 'تم التسليم'),
                ('carrier_id', '=', 3),  # تحديد شركة الشحن "سمسا"
            ])
            total_count = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),
                ('custom_stage_id', '!=', 'في الشحن'),
                ('carrier_id', '=', 3),
            ])

            # تأكد من التحقق من قيمة total_count لتجنب القسمة على صفر
            record.delivery_ratio_samsa = (delivered_count_samsa / total_count) * 100 if total_count != 0 else 0

    @api.depends('delivered_delivery_orders_count', 'delivery_orders_count')
    def _compute_delivery_ratio_quick_silver(self):
        for record in self:
            delivered_count = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),  # افحص طلبات التوصيل الخارجية فقط
                ('custom_stage_id', '=', 'تم التسليم'),  # افحص الطلبات التي تم تسليمها فقط
                ('carrier_id', '=', 'Quick silver'),
            ])
            total_count = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),
                ('custom_stage_id', '!=', 'في الشحن'),
                ('carrier_id.name', '=', 'Quick silver'),
            ])

            # تأكد من التحقق من قيمة total_count لتجنب القسمة على صفر
            record.delivery_ratio_quick_silver = (delivered_count / total_count) * 100 if total_count != 0 else 0

    @api.depends('delivered_delivery_orders_count', 'delivery_orders_count')
    def _compute_delivery_ratio_ajax(self):
        for record in self:
            delivered_count = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),  # افحص طلبات التوصيل الخارجية فقط
                ('custom_stage_id', '=', 'تم التسليم'),
                ('carrier_id.name', '=', 'AJEX'),
            ])
            total_count = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),
                ('custom_stage_id', '!=', 'في الشحن'),
                ('carrier_id.name', '=', 'AJEX'),
            ])

            # تأكد من التحقق من قيمة total_count لتجنب القسمة على صفر
            record.delivery_ratio_ajax = (delivered_count / total_count) * 100 if total_count != 0 else 0

    @api.depends('delivered_delivery_orders_count', 'delivery_orders_count')
    def _compute_delivery_ratio_jordan(self):
        for record in self:
            delivered_count = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),  # افحص طلبات التوصيل الخارجية فقط
                ('custom_stage_id', '=', 'تم التسليم'),
                ('carrier_id', '=', 6),
            ])
            total_count = self.env['stock.picking'].search_count([
                ('picking_type_code', '=', 'outgoing'),
                ('custom_stage_id', '!=', 'في الشحن'),
                ('carrier_id', '=', 6),
            ])

            # تأكد من التحقق من قيمة total_count لتجنب القسمة على صفر
            record.delivery_ratio_jordan = (delivered_count / total_count) * 100











