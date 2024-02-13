# from odoo import api, fields, models
# from odoo.exceptions import ValidationError
#
#
# class ShippingReturnInvoice(models.Model):
#     _name = 'sec.return.invoice'
#     _description = 'Shipping Return Invoice'
#
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     name = fields.Char(string='SEC Number', required=True)
#     order_line = fields.One2many('sec.return.order.line', 'shipping_return_invoice_id', string='Order Lines')
#     supplier_id = fields.Many2one('res.partner', string='Supplier')
#     account_invoice_id = fields.Many2one('account.move', string='Account Invoice')
#     date_start = fields.Date(
#         string="Creation date",
#         help="Date when the user initiated the request.",
#         default=fields.Date.context_today,
#         tracking=True,
#     )
#
#     total_cdv = fields.Float(string="Total", compute='_compute_total_cdv')
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('to_approve', 'To be approved'),
#         ('approved', 'Approved'),
#         ('invoice_creation', 'Invoice Creation'),
#         ('rejected', 'Rejected'),
#         ('done', 'Done'),
#     ], string='Invoice State', default='draft')
#
#     def action_to_approve(self):
#         for invoice in self:
#             invoice.state = 'to_approve'
#         return True
#
#     def action_invoice_creation(self):
#         for invoice in self:
#             if invoice.order_line:
#                 invoice_lines = [(0, 0, {
#                     'product_id': 35,
#                     'name': order_line.sale_order_id.name,
#                     'price_unit': order_line.total_cdv,
#                     'tax_ids': [(6, 0, [])],
#                 }) for order_line in invoice.order_line]
#
#                 invoice.env['account.move'].sudo().create({
#                     'move_type': 'in_invoice',
#                     'invoice_origin': invoice.name,
#                     'invoice_date': invoice.date_start,
#                     'invoice_date_due': invoice.date_start,
#                     'partner_id': invoice.supplier_id.id,
#                     'invoice_line_ids': invoice_lines,
#                 })
#
#                 invoice.state = 'approved'
#
#     def action_approve(self):
#         for invoice in self:
#             invoice.state = 'approved'
#
#     def action_done(self):
#         for invoice in self:
#             invoice.state = 'done'
#         return True
#
#     def action_reject(self):
#         for invoice in self:
#             invoice.state = 'rejected'
#         return True
#
#     def action_create_invoice(self):
#         for invoice in self:
#             # إلقاء الفاتورة عند الضغط على الزر
#             invoice.action_approve()
#
#     def action_set_to_draft(self):
#         for invoice in self:
#             invoice.state = 'draft'
#
#     @api.depends('order_line.COD_Charges', 'order_line.Delivery_Charges', 'order_line.GPA', 'order_line.Return_Charges')
#     def _compute_total_cdv(self):
#         for record in self:
#             SEC = sum(record.order_line.mapped(
#                 lambda line: line.COD_Charges + line.Delivery_Charges + line.GPA + line.Return_Charges))
#             record.total_cdv = SEC
#
#
# class ShippingReturnOrderLine(models.Model):
#     _name = 'sec.return.order.line'
#     _description = 'SEC Return Order Line'
#
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     sale_order_id = fields.Many2one('sale.order', string='Sale Order', unique=True,
#                                     domain=[('delivery_stage_id', '=', 'تم الارجاع عجمان')])
#
#     @api.onchange('sale_order_id')
#     def check_duplicate_sale_order(self):
#         if self.sale_order_id:
#             duplicate_records = self.search([('sale_order_id', '=', self.sale_order_id.id)])
#             if len(duplicate_records) > 0:
#                 duplicate_record_names = ", ".join(duplicate_records.mapped('shipping_return_invoice_id.name'))
#                 self.sale_order_id = False
#                 raise ValidationError("الطلب الذي تحاول اضافته موجود بالكشف :   %s" % duplicate_record_names)
#
#     COD_Amount = fields.Float(string='COD Amount', compute='_compute_shipment_cost', store=True)
#     Delivery_Charges = fields.Float(string='Delivery Charges', default=23.10)
#     COD_Charges = fields.Float(string='COD Charges', default=8.0)
#     Return_Charges = fields.Float(string='Return Charges', default=0.0)
#     GPA = fields.Float(string='GPA', compute='_compute_GPA', store=True)
#     total_cdv = fields.Float(string='Total Cost', compute='_compute_total_cdv_cost', store=True)
#     shipping_invoice_id = fields.Many2one('sec', string='Shipping Invoice')
#     order_line = fields.One2many('sec.order.line', 'shipping_invoice_id', string='Order Lines')
#
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('approved', 'Approved')
#     ], string='Invoice State', default='draft', readonly=True)
#
#     def action_approve(self):
#         for record in self:
#             record.state = 'approved'
#
#     def action_set_to_draft(self):
#         for record in self:
#             record.state = 'draft'
#
#     @api.depends('Delivery_Charges')
#     def _compute_GPA(self):
#         for record in self:
#             GPA = record.Delivery_Charges * 0.1
#             record.GPA = GPA
#
#     @api.depends('COD_Amount', 'tax_percentage')
#     def _compute_cdv_cost(self):
#         for record in self:
#             cdv = (record.COD_Amount * record.tax_percentage) / 100
#             record.cdv = cdv
#
#     @api.depends('Delivery_Charges', 'COD_Charges', 'GPA', 'Return_Charges')
#     def _compute_total_cdv_cost(self):
#         for line in self:
#             line.total_cdv = line.Delivery_Charges + line.COD_Charges + line.GPA + line.Return_Charges
#
#     @api.depends('sale_order_id.amount_total')
#     def _compute_shipment_cost(self):
#         for record in self:
#             if record.sale_order_id:
#                 COD_Amount = record.sale_order_id.amount_total
#                 record.COD_Amount = COD_Amount
#
#     @api.depends('sale_order_id.amount_total')
#     def _compute_shipment_cost(self):
#         for record in self:
#             if record.sale_order_id:
#                 COD_Amount = record.sale_order_id.amount_total
#                 record.COD_Amount = COD_Amount
#
#     # تنفيذ باقي الحقول والوظائف الأخرى كما هو
