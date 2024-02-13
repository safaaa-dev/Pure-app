from odoo import _, api, fields, models


class ShippingInvoice(models.Model):
    _name = 'shipping.invoice'
    _description = 'Shipping Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']



    name = fields.Char(string='CDV Number', required=True)
    account_invoice_id = fields.Many2one('account.move', string='Account Invoice')
    date_start = fields.Date(
        string="Creation date",
        help="Date when the user initiated the request.",
        default=fields.Date.context_today,
        tracking=True,
    )
    shipping_company = fields.Selection([
        ('smsa', 'SMSA'),
        ('ajex', 'AJEX'),
        ('Quicksilver', 'Quicksilver'),
        # ... يمكنك إضافة شركات شحن إضافية حسب الحاجة
    ], string='Shipping Company', help='Select the shipping company')

    # Add a one2many field to relate to order lines
    order_line = fields.One2many('shipping.order.line', 'shipping_invoice_id', string='Order Lines')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    # You can define the total_cdv field to compute the sum of CDV from order lines
    total_cdv = fields.Float(string="Total CDV", compute='_compute_total_cdv')
    # invoice_ids = fields.One2many('supplier.invoice', 'shipping_invoice_id', string='Supplier Invoices')
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
                    'product_id': 3,
                    'name': order_line.sale_order_id.name,
                    'price_unit': order_line.total_cdv,
                    'account_id': invoice.account_id.id,
                    'analytic_account_id': invoice.analytic_account_id,
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

                invoice.state = 'invoice_creation'

    def action_done(self):
        for invoice in self:
            invoice.state = 'done'
        return True
    def action_reject(self):
        for invoice in self:
            invoice.state = 'rejected'
        return True

    def action_approve(self):
        for invoice in self:
            invoice.state = 'approved'
        return True
    def action_reject(self):
        for invoice in self:
            invoice.state = 'rejected'
        return True


        return True
    def action_create_invoice(self):
        for invoice in self:
            # إلقاء الفاتورة عند الضغط على الزر
            invoice.action_approve()

    def action_set_to_draft(self):
        for invoice in self:
            invoice.state = 'draft'


    @api.depends('sale_order_id.amount_total')
    def _compute_shipment_cost(self):
        for record in self:
            if record.sale_order_id:
                COD_Amount = record.sale_order_id.amount_total
                record.COD_Amount = COD_Amount

    @api.depends('order_line.cdv', 'order_line.documentation_charge', 'order_line.admin_charges', 'order_line.vat_on_admin_charges', 'shipping_company')
    def _compute_total_cdv(self):
        for record in self:
            total_cdv = 0.0
            if record.shipping_company == 'smsa':
                total_cdv = sum(record.order_line.mapped(
                    lambda line: line.cdv + line.documentation_charge + line.admin_charges + line.vat_on_admin_charges))
            else:
                total_cdv = sum(record.order_line.mapped(lambda line: line.cdv))
            record.total_cdv = total_cdv

class ShippingOrderLine(models.Model):
    _name = 'shipping.order.line'
    _description = 'Shipping Order Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    sale_order_id = fields.Many2one('sale.order', string='Sale Order', unique=True, index=True)

    COD_Amount = fields.Float(string='COD Amount', compute='_compute_shipment_cost', store=True)
    tax_percentage = fields.Float(string='Tax Percentage', default=1.5)
    cdv = fields.Float(string='CDV Cost', compute='_compute_cdv_cost', store=True)
    total_cdv = fields.Float(string='Total CDV Cost', compute='_compute_total_cdv_cost', store=True)
    shipping_invoice_id = fields.Many2one('shipping.invoice', string='Shipping Invoice')

    documentation_charge = fields.Float(string='Documentation Charge', default=0.15)
    admin_charges = fields.Integer(string='Admin Charges', default=1)
    vat_on_admin_charges = fields.Float(string='VAT on Admin Charges', default=0.15, store=True)
    vat = fields.Float(string='VAT on Admin Charges', default=0.15)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ], string='Invoice State', default='draft', readonly=True)

    # في النموذج shipping.order.line
    shipping_company = fields.Selection(related='shipping_invoice_id.shipping_company', string='Shipping Company',
                                        store=True)


    def action_approve(self):
        for invoice_line in self:
            invoice_line.state = 'approved'

    def action_set_to_draft(self):
        for invoice in self:
            invoice.state = 'draft'


    @api.depends('COD_Amount', 'tax_percentage')
    def _compute_cdv_cost(self):
        for record in self:
            cdv = (record.COD_Amount * record.tax_percentage) / 100
            record.cdv = cdv


    @api.depends('cdv', 'documentation_charge', 'admin_charges', 'vat_on_admin_charges', 'shipping_company')
    def _compute_total_cdv_cost(self):
        for record in self:
            if record.shipping_company == 'smsa':
                total_cdv = sum([
                    record.cdv,
                    record.documentation_charge,
                    record.admin_charges,
                    record.vat_on_admin_charges,
                ])
            else:
                total_cdv = sum([record.cdv])

            record.total_cdv = total_cdv

    @api.depends('sale_order_id.amount_total')
    def _compute_shipment_cost(self):
        for record in self:
            if record.sale_order_id:
                COD_Amount = record.sale_order_id.amount_total
                record.COD_Amount = COD_Amount


class SupplierInvoice(models.Model):
    _name = 'supplier.invoice'
    _description = 'Supplier Invoice'

    invoice_number = fields.Char(string='Invoice Number', required=True)
    amount = fields.Float(string='Amount')
    shipping_invoice_id = fields.Many2one('shipping.invoice', string='Shipping Invoice')
    supplier_id = fields.Char(string='Vender')
