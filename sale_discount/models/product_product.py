from odoo import fields, models, api
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            args = expression.AND([
                args,
                [('is_discount', '!=', True)]
            ])
        return super(ProductProduct, self).name_search(name, args, operator, limit)
