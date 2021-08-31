from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_discount = fields.Boolean(default=False)
