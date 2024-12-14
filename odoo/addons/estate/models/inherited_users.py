from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    property_ids = fields.One2many(
        'estate.property',  
        'salesPerson_id',   
        string='Properties',
        # domain=[('state', 'in', ['new', 'offer_received'])],  # Domain to only list available properties
        domain=[('state', '=', 'new')],  # Domain to only list available properties
    
    )
