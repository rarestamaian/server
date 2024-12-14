from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Table that describes a property offer"
    _order = "price desc"

    price = fields.Float()
    status = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused')
    ], copy=False)

    partner_id = fields.Many2one( 'res.partner', required=True)
    property_id = fields.Many2one('estate.property', string='Property', required=True)

    validity = fields.Integer(default=7)
    date_deadline = fields.Date(compute="_compute_deadline", inverse="_inverse_deadline")

    property_type_id = fields.Many2one(
        comodel_name="estate.property.type",
        string="Property Type",
        related="property_id.property_type_id",
        store=True,
        )
    # store = enabled storage to allow searching, filtering, grouping
#    the above related field must be defined as Many2one not as field.Integer
    _sql_constraints = [
    (
       '_offer_price_positive',
       'CHECK(price > 0)',
       'The offer price MUST be greater than 0.'
    ),
    ]

    @api.depends("create_date", "validity")
    def _compute_deadline(self):
        for record in self:
            creation_date = record.create_date or fields.Datetime.now()
            record.date_deadline = creation_date + timedelta(days=record.validity)

    def _inverse_deadline(self):
        for record in self:
            record.create_date = fields.Datetime.to_datetime(record.date_deadline) - timedelta(days=record.validity)

    def action_accept_offer(self):
        for record in self:
            record.status = 'accepted'
            record.property_id.selling_price = record.price
            record.property_id.buyer_id = record.partner_id
            record.property_id.state = 'offer_accepted'
            other_offers = record.property_id.offer_ids - record
            other_offers.write({'status': 'refused'})

    def action_refuse_offer(self):
        for record in self:
            record.status = 'refused'
# instead of @api.model bc it will be deprecated. model_create_multi = vals can be a list of dicts not a single dict, to create multiple records at a time
    # also implement the function to deal with list of dicts for vals
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            property_obj = self.env['estate.property'].browse(val.get('property_id'))
            if property_obj.offer_ids.filtered(lambda offer: offer.price > val.get('price')):
                raise UserError("You cannot create an offer with a lower price than an existing offer.")
            if property_obj.state == 'new':
                property_obj.state = 'offer_received'
        return super().create(vals)
