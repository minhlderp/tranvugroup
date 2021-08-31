# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_compare, float_is_zero
from collections import defaultdict
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)

class Picking(models.Model):
    _inherit = "stock.picking"

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Receiving in Stock'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")
    returnorder_id = fields.Many2one(
        'stock.picking', 'Return Order of',
        copy=False, index=True, readonly=True,
        check_company=True,
        help="If this shipment was split, then this field links to the shipment which contains the already processed part.")

    @api.depends('state', 'is_locked')
    def _compute_show_validate(self):
        super(Picking, self)._compute_show_validate()
        for picking in self:
            if not (picking.immediate_transfer) and picking.state == 'draft':
                picking.show_validate = False
            elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned','received') or not picking.is_locked:
                picking.show_validate = False
            else:
                picking.show_validate = True

    def _check_backorder(self):
        super(Picking, self)._check_backorder()
        """ This method will loop over all the move lines of self and
        check if creating a backorder is necessary. This method is
        called during button_validate if the user has already processed
        some quantities and in the immediate transfer wizard that is
        displayed if the user has not processed any quantities.

        :return: True if a backorder is necessary else False
        """
        quantity_todo = {}
        quantity_qc = {}
        for move in self.mapped('move_lines'):
            quantity_todo.setdefault(move.product_id.id, 0)
            quantity_qc.setdefault(move.product_id.id, 0)
            quantity_todo[move.product_id.id] += move.product_uom_qty
            quantity_qc[move.product_id.id] += move.quantity_qc
        for ops in self.mapped('move_line_ids').filtered(lambda x: x.package_id and not x.product_id and not x.move_id):
            for quant in ops.package_id.quant_ids:
                quantity_qc.setdefault(quant.product_id.id, 0)
                quantity_qc[quant.product_id.id] += quant.qty
        for pack in self.mapped('move_line_ids').filtered(lambda x: x.product_id and not x.move_id):
            quantity_qc.setdefault(pack.product_id.id, 0)
            quantity_qc[pack.product_id.id] += pack.product_uom_id._compute_quantity(pack.qty_done, pack.product_id.uom_id)
        return any(quantity_qc[x] < quantity_todo.get(x, 0) for x in quantity_qc)

    def _create_backorder(self):
        super(Picking, self)._create_backorder()

        """ This method is called when the user chose to create a backorder. It will create a new
        picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
        """
        backorders = self.env['stock.picking']
        for picking in self:
            moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
            if moves_to_backorder:
                backorder_picking = picking.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': picking.id
                })
                picking.message_post(
                    body=_('The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (
                        backorder_picking.id, backorder_picking.name))

                moves_to_backorder.write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('package_level_id').write({'picking_id':backorder_picking.id})
                moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
                backorder_picking.action_assign()
                backorders |= backorder_picking 
        return backorders
        
    def action_done(self):
        super(Picking, self).action_done()
        """Changes picking state to done by processing the Stock Moves of the Picking

        Normally that happens when the button "Done" is pressed on a Picking view.
        @return: True
        """
        self._check_company()

        todo_moves = self.mapped('move_lines').filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        # Check if there are ops not linked to moves yet
        for pick in self:
            if pick.owner_id:
                pick.move_lines.write({'restrict_partner_id': pick.owner_id.id})
                pick.move_line_ids.write({'owner_id': pick.owner_id.id})

         
            for ops in pick.move_line_ids.filtered(lambda x: not x.move_id):
                # Search move with this product
                moves = pick.move_lines.filtered(lambda x: x.product_id == ops.product_id)
                moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
                if moves:
                    ops.move_id = moves[0].id
                else:
                    new_move = self.env['stock.move'].create({
                                                    'name': _('New Move:') + ops.product_id.display_name,
                                                    'product_id': ops.product_id.id,
                                                    'product_uom_qty': ops.qty_done,
                                                    'quantity_inv': 0,
                                                    'quantity_qc': 0,
                                                    'product_uom': ops.product_uom_id.id,
                                                    'description_picking': ops.description_picking,
                                                    'location_id': pick.location_id.id,
                                                    'location_dest_id': pick.location_dest_id.id,
                                                    'picking_id': pick.id,
                                                    'picking_type_id': pick.picking_type_id.id,
                                                    'restrict_partner_id': pick.owner_id.id,
                                                    'company_id': pick.company_id.id,
                                                   })
                    ops.move_id = new_move.id
                    new_move._action_confirm()
                    todo_moves |= new_move
                    #'qty_done': ops.qty_done})
        todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
        self.write({'date_done': fields.Datetime.now()})
        self._send_confirmation_email()
        return True
  
    # def _check_returnorder(self):
    #     for move in self.move_lines:
    #         result_compare = float_compare(move.quantity_inv, move.quantity_qc, precision_digits=3)
    #         if result_compare:
    #             return True
    #     return False

    # def returnqty_act(self):
    #     action = self.env.ref('stock.act_stock_return_picking').read()[0]   
    #     return action

    def button_validate(self):
        super(Picking, self).button_validate()
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some items to move.'))

        # If no lots when needed, raise error
        picking_type = self.picking_type_id
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
        no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
        if no_reserved_quantities and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

        if picking_type.use_create_lots or picking_type.use_existing_lots:
            lines_to_check = self.move_line_ids
            if not no_quantities_done:
                lines_to_check = lines_to_check.filtered(
                    lambda line: float_compare(line.qty_done, 0,
                                               precision_rounding=line.product_uom_id.rounding)
                )

            for line in lines_to_check:
                product = line.product_id
                if product and product.tracking != 'none':
                    if not line.lot_name and not line.lot_id:
                        raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

    
        if no_quantities_done:
            view = self.env.ref('stock.view_immediate_transfer')
            wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
            return {
                'name': _('Immediate Transfer?'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.immediate.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
            view = self.env.ref('stock.view_overprocessed_transfer')
            wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.overprocessed.transfer',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wiz.id,
                'context': self.env.context,
            }

        # Check backorder should check for other barcodes
        if self._check_backorder():
            return self.action_generate_backorder_wizard()
        self.action_done()
        return 

class StockMove(models.Model):
    _inherit = "stock.move.line"
    quantity_inv = fields.Float('Quantity Inventory', digits='Product Unit of Measure')
    quantity_qc = fields.Float('Quantity QC', digits='Product Unit of Measure')

class StockMove(models.Model):
    _inherit = "stock.move"
    
    quantity_inv = fields.Float('Quantity Inventory', digits='Product Unit of Measure', copy=False, default=0)
    quantity_qc = fields.Float('Quantity QC', digits='Product Unit of Measure', copy=False, default=0)
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")

    @api.constrains('quantity_qc')
    def _check_quantityqc(self):
        result_compare = float_compare(self.quantity_qc, self.quantity_inv, precision_digits=3)
        if result_compare == 1:
            raise ValidationError(_("The quantity QC must be less than the quantity received in stock."))
    
    @api.constrains('quantity_inv')
    def _check_quantityinv(self):
        is_receive = True
        result_compare = float_compare(float(0), self.quantity_inv, precision_digits=3)
        result_compareq = float_compare(self.quantity_inv, self.product_uom_qty, precision_digits=3)
        if result_compare == 1 or result_compareq:
            is_receive = False
                
        if is_receive == False:
            raise ValidationError(_("The quantity received in stock must be more than 0."))

    @api.onchange('quantity_inv')
    def _check_quantityinv(self):
        self.quantity_done = self.quantity_inv
 
    @api.depends('move_line_ids.qty_done', 'move_line_ids.product_uom_id', 'move_line_nosuggest_ids.qty_done')
    def _quantity_done_compute(self):
        super(StockMove, self)._quantity_done_compute()
        """ This field represents the sum of the move lines `qty_done`. It allows the user to know
        if there is still work to do.

        We take care of rounding this value at the general decimal precision and not the rounding
        of the move's UOM to make sure this value is really close to the real sum, because this
        field will be used in `_action_done` in order to know if the move will need a backorder or
        an extra move.
        """
        move_lines = self.env['stock.move.line']
        for move in self:
            move_lines |= move._get_move_lines()

        data = self.env['stock.move.line'].read_group(
            [('id', 'in', move_lines.ids)],
            ['move_id', 'product_uom_id', 'qty_done'], ['move_id', 'product_uom_id'],
            lazy=False
        )

        rec = defaultdict(list)
        for d in data:
            rec[d['move_id'][0]] += [(d['product_uom_id'][0], d['qty_done'])]
        
        for move in self:
            result_compare = float_compare(move.product_uom_qty, move.quantity_inv, precision_digits=3)
            if(result_compare):
                move.quantity_done =  move.quantity_inv
            else: 
                uom = move.product_uom
                
                move.quantity_done = sum(
                    self.env['uom.uom'].browse(line_uom_id)._compute_quantity(qty, uom, round=False)
                    for line_uom_id, qty in rec.get(move.id, [])
                )

    def _prepare_extra_move_vals(self, qty):
        super(StockMove, self)._prepare_extra_move_vals(qty)
        vals = {
            'procure_method': 'make_to_stock',
            'origin_returned_move_id': self.origin_returned_move_id.id,
            'product_uom_qty': qty,
            'quantity_inv': 0,
            'quantity_qc': 0,
            'picking_id': self.picking_id.id,
            'price_unit': self.price_unit,
        }
        return vals

class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    quantity_inv = fields.Float("Quantity inv", digits='Product INV')
    quantity_qc = fields.Float("Quantity qc", digits='Product QC')

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move):
        super(ReturnPicking, self)._prepare_stock_return_picking_line_vals_from_move(stock_move)
        result_compare = float_compare(stock_move.quantity_inv, stock_move.quantity_qc, precision_digits=3)

        quantity = stock_move.product_qty - sum(
            stock_move.move_dest_ids
            .filtered(lambda m: m.state in ['partially_available', 'assigned', 'done'])
            .mapped('move_line_ids.product_qty')
        )
        quantity = float_round(quantity, precision_rounding=stock_move.product_uom.rounding)
        if(result_compare):
            return {
                'product_id': stock_move.product_id.id,
                'quantity': float_round(stock_move.quantity_inv - stock_move.quantity_qc, precision_rounding=stock_move.product_uom.rounding),
                'quantity_inv': 0,
                'quantity_qc': 0,
                'move_id': stock_move.id,
                'uom_id': stock_move.product_id.uom_id.id,
            }
        return {
            'product_id': stock_move.product_id.id,
            'quantity': quantity,
            'quantity_inv': 0,
            'quantity_qc': 0,
            'move_id': stock_move.id,
            'uom_id': stock_move.product_id.uom_id.id,
        }

    def _prepare_move_default_values(self, return_line, new_picking):
        super(ReturnPicking, self)._prepare_move_default_values(return_line,new_picking)
        result_compare = float_compare(return_line.quantity_inv, return_line.quantity_qc, precision_digits=3)
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'quantity_inv': 0,
            'quantity_qc': 0,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date_expected': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }

        if(result_compare):
            vals = {
                'product_id': return_line.product_id.id,
                'product_uom_qty': return_line.quantity_inv - return_line.quantity_qc,
                'quantity_inv': 0,
                'quantity_qc': 0,
                'product_uom': return_line.product_id.uom_id.id,
                'picking_id': new_picking.id,
                'state': 'draft',
                'date_expected': fields.Datetime.now(),
                'location_id': return_line.move_id.location_dest_id.id,
                'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
                'picking_type_id': new_picking.picking_type_id.id,
                'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
                'origin_returned_move_id': return_line.move_id.id,
                'procure_method': 'make_to_stock',
            }
            
        return vals

class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def _process(self, cancel_backorder=False):
        super(StockBackorderConfirmation, self)._process(cancel_backorder)
        for confirmation in self:
            if cancel_backorder:
                for pick_id in confirmation.pick_ids:
                    moves_to_log = {}
                    for move in pick_id.move_lines:
                        if float_compare(move.product_uom_qty,
                                         move.quantity_qc,
                                         precision_rounding=move.product_uom.rounding) > 0:
                            moves_to_log[move] = (move.quantity_qc, move.product_uom_qty)
                    pick_id._log_less_quantities_than_expected(moves_to_log)
            confirmation.pick_ids.with_context(cancel_backorder=cancel_backorder).action_done()

class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        super(StockImmediateTransfer, self).process()
        pick_to_backorder = self.env['stock.picking']
        pick_to_do = self.env['stock.picking']
        for picking in self.pick_ids:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    if move_line.move_id.quantity_inv:
                        move_line.qty_done = move_line.move_id.quantity_inv
                    else:
                        move_line.qty_done = move_line.product_uom_qty
            if picking._check_backorder():
                pick_to_backorder |= picking
                continue
            pick_to_do |= picking
        # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
        if pick_to_do:
            pick_to_do.action_done()
        if pick_to_backorder:
            return pick_to_backorder.action_generate_backorder_wizard()
        return False
