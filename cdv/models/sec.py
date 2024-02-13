from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ShippingInvoice(models.Model):
    _name = 'sec'
    _description = 'Shipping Invoice'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='SEC Number', required=True)
    order_line = fields.One2many('sec.order.line', 'shipping_invoice_id', string='Order Lines')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    account_invoice_id = fields.Many2one('account.move', string='Account Invoice')
    date_start = fields.Date(
        string="Creation date",
        help="Date when the user initiated the request.",
        default=fields.Date.context_today,
        tracking=True,
    )
   
    total_cdv = fields.Float(string="Total", compute='_compute_total_cdv')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To be approved'),
        ('approved', 'Approved'),
        ('invoice_creation', 'Invoice Creation'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
    ], string='Invoice State', default='draft')

    def action_to_approve(self):
        for invoice in self:
            invoice.state = 'to_approve'
        return True

    def action_invoice_creation(self):
        for invoice in self:
            if invoice.order_line:
                invoice_lines = [(0, 0, {
                    'product_id': 35,
                    'name': order_line.sale_order_id.name,
                    'price_unit': order_line.total_cdv,
                    'tax_ids': [(6, 0, [])],
                }) for order_line in invoice.order_line]

                invoice.env['account.move'].sudo().create({
                    'move_type': 'in_invoice',
                    'invoice_origin': invoice.name,
                    'invoice_date': invoice.date_start,
                    'invoice_date_due': invoice.date_start,
                    'partner_id': invoice.supplier_id.id,
                    'invoice_line_ids': invoice_lines,
                })

                invoice.state = 'approved'

    def action_approve(self):
        for invoice in self:
            invoice.state = 'approved'

    def action_done(self):
        for invoice in self:
            invoice.state = 'done'
        return True

    def action_reject(self):
        for invoice in self:
            invoice.state = 'rejected'
        return True

    def action_done(self):
        for invoice in self:
            invoice.state = 'done'
        return True

    def action_create_invoice(self):
        for invoice in self:
            # إلقاء الفاتورة عند الضغط على الزر
            invoice.action_approve()

    def action_set_to_draft(self):
        for invoice in self:
            invoice.state = 'draft'

    @api.depends('order_line.COD_Charges', 'order_line.Delivery_Charges', 'order_line.GPA', 'order_line.Return_Charges')
    def _compute_total_cdv(self):
        for record in self:
            SEC = sum(record.order_line.mapped(lambda line: line.COD_Charges + line.Delivery_Charges + line.GPA + line.Return_Charges))
            record.total_cdv = SEC


class ShippingOrderLine(models.Model):
    _name = 'sec.order.line'
    _description = 'SEC Order Line'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        unique=True,
        domain=[('delivery_stage_id', 'in', ['تم التسليم', 'تم الارجاع عجمان', 'Quicksilver Fulfillment'])]
    )

    @api.onchange('sale_order_id')
    def check_duplicate_sale_order(self):
        if self.sale_order_id:
            duplicate_records = self.search([('sale_order_id', '=', self.sale_order_id.id)])
            if len(duplicate_records) > 0:
                duplicate_record_names = ", ".join(duplicate_records.mapped('shipping_invoice_id.name'))
                self.sale_order_id = False
                raise ValidationError("الطلب الذي تحاول اضافته موجود بالكشف :   %s" % duplicate_record_names)

            # Check the delivery stage of the sale order
            if self.sale_order_id.delivery_stage_id == 'تم التسليم':
                self.Return_Charges = 0  # If delivered, set Return_Charges to 0
            else:
                # Check the supplier
                if self.shipping_invoice_id.supplier_id.name == 'QuickSliver':
                    self.Return_Charges = 4  # If supplier is QuickSliver, set Return_Charges to 4
                else:
                    self.Return_Charges = 0  # If supplier is not QuickSliver, set Return_Charges to 0

    COD_Amount = fields.Float(string='COD Amount', compute='_compute_shipment_cost', store=True)
    Delivery_Charges = fields.Float(
        string='Delivery Charges',
        default=16,
        compute='_compute_delivery_charges'
    )
    COD_Charges = fields.Float(string='COD Charges', default=4.0)
    Return_Charges = fields.Float(string='Return Charges', default=0)
    GPA = fields.Float(string='VAT', compute='_compute_GPA', store=True)
    total_cdv = fields.Float(string='Total Cost', compute='_compute_total_cdv_cost', store=True)
    shipping_invoice_id = fields.Many2one('sec', string='Shipping Invoice')
    order_line = fields.One2many('sec.order.line', 'shipping_invoice_id', string='Order Lines')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ], string='Invoice State', default='draft', readonly=True)

    def action_approve(self):
        for record in self:
            record.state = 'approved'

    def action_set_to_draft(self):
        for record in self:
            record.state = 'draft'

    @api.depends('shipping_invoice_id.supplier_id')
    def _compute_delivery_charges(self):
        for record in self:
            if record.shipping_invoice_id.supplier_id.name == 'SMSA':
                record.Delivery_Charges = 12  # Set Delivery Charges to 12 if the supplier is 'SMSA'
            elif record.shipping_invoice_id.supplier_id.name == 'QuickSilver':
                record.Delivery_Charges = 16  # Set Delivery Charges to 16 if the supplier is 'QuickSilver'
            else:
                record.Delivery_Charges = 0  # Set a default value of 0 if the supplier is neither 'SMSA' nor 'QuickSilver'

    @api.depends('Delivery_Charges', 'shipping_invoice_id.supplier_id')
    def _compute_GPA(self):
        for record in self:
            if record.shipping_invoice_id.supplier_id.name == 'QuickSliver':
                record.GPA = record.Delivery_Charges * 0.15  # Set GPA to 10% of Delivery Charges if the supplier is 'smsa'
            else:
                record.GPA = 0  # Set GPA to 15% of Delivery Charges for other suppliers

    @api.depends('COD_Amount', 'tax_percentage')
    def _compute_cdv_cost(self):
        for record in self:
            cdv = (record.COD_Amount * record.tax_percentage) / 100
            record.cdv = cdv

    @api.depends('Delivery_Charges', 'COD_Charges', 'GPA', 'Return_Charges')
    def _compute_total_cdv_cost(self):
        for line in self:
            line.total_cdv = line.Delivery_Charges + line.COD_Charges + line.GPA + line.Return_Charges

    @api.depends('sale_order_id.amount_total')
    def _compute_shipment_cost(self):
        for record in self:
            if record.sale_order_id:
                COD_Amount = record.sale_order_id.amount_total
                record.COD_Amount = COD_Amount

    @api.depends('sale_order_id.amount_total')
    def _compute_shipment_cost(self):
        for record in self:
            if record.sale_order_id:
                COD_Amount = record.sale_order_id.amount_total
                record.COD_Amount = COD_Amount
