from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    # property_ids = fields.One2many(
    #     'estate.property',  
    #     'salesPerson_id',   
    #     string='Properties',
    #     domain=[('state', 'in', ['new', 'offer_received'])],  # Domain to only list available properties
    #     # domain=[('state', '=', 'new')],  # Domain to only list available properties
    # )

    # property_subset_ids = fields.One2many(
    #     'estate.property',  
    #     compute='_compute_property_subset',
    # )
    property_subset_ids = fields.One2many(
        'estate.property',
        'salesPerson_id',
        string='Property Subset',
        compute='_compute_property_subset',
        store=False,
        help="Dynamically computes a subset of properties assigned to the salesperson."
    )

    # @api.depends('id') @ without this, the method is invoked whenever the field is accessed in the view
    def _compute_property_subset(self):
        for user in self:
            # Load only 30 records, adjust the order as needed
            properties = self.env['estate.property'].search([
                ('salesPerson_id', '=', user.id),
                ('state', 'in', ['new', 'offer_received'])
            ], limit=30)  # Limit the number of records to 30
            user.property_subset_ids = properties
            # user.property_subset_ids = user.property_ids[:30]