from odoo import models, Command
import logging
_logger = logging.getLogger(__name__)

class EstateProperty(models.Model):
    _inherit = "estate.property"

    def action_sold_property(self):
        """ When a property is sold, generate an invoice """
        res = super().action_sold_property()
        _logger.info("Overridden action_sold_property method is being called!")
        
        account_move_vals = {
            'partner_id': self.buyer_id.id,  # Use the buyer's ID from the property
            'move_type': 'out_invoice',     # Move type for a customer invoice
            'invoice_line_ids': [
                Command.create({
                    'name': 'Property Sale - 6% of Selling Price',
                    'quantity': 1,  # Adjust based on your requirement
                    'price_unit': self.selling_price * 0.06,  # 6% of the selling price
                }),
                 Command.create({
                    'name': 'Administrative Fees',
                    'quantity': 1,  # Adjust based on your requirement
                    'price_unit': 100.00,  # Fixed administrative fee
                }),
            ],
        }
        
        # Create the account.move
        self.env['account.move'].create(account_move_vals)
        return res