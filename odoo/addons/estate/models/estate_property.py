from odoo import models, fields, api
from datetime import date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero
import string
import random
import time
import logging
import os
from datetime import datetime


_logger = logging.getLogger(__name__)


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Table that describes a real estate property!"
    _order = "id desc"
    # _auto = False

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    postcode = fields.Char()
    date_availability = fields.Date(copy=False, default=lambda self: date.today() + timedelta(days=90))
    expected_price = fields.Float(required=True)
    selling_price = fields.Float(readonly=True, copy=False)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    score = fields.Integer(default=0)
    garden_orientation = fields.Selection(
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West')
        ],
        string="Garden Orientation",
        help="Select the orientation of the garden."
    )
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('cancelled', 'Cancelled')
        ],
        required=True,
        copy=False,
        default='new',
        string="State",
        help="The state of the property"
    )

    active = fields.Boolean(
        default=True,
        string="Active",
        help="Indicates if the property is active or archived",
        index=True
    )

    property_type_id = fields.Many2one(comodel_name="estate.property.type", string="Property Type",
                                       ondelete="restrict")

    salesPerson_id = fields.Many2one('res.users', string='Salesperson', index=True,
                                     default=lambda self: self.env.user)
    buyer_id = fields.Many2one('res.partner', string='Buyer', index=True, copy=False)
    tag_ids = fields.Many2many('estate.property.tag', string='Tags')
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string='Offers')

    total_area = fields.Integer(compute="_compute_total_area")
    best_price = fields.Integer(compute="_compute_max_offer_price")

    _sql_constraints = [
        (
            '_expected_price_positive',
            'CHECK(expected_price > 0)',
            'The expected price MUST be positive.'
        ),
        (
            '_selling_price_positive',
            'CHECK(selling_price >= 0)',
            'The selling price MUST be 0 or positive.'
        ),
    ]
    

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price_percentage(self):
        for record in self:
            if (not float_is_zero(record.selling_price, precision_rounding=0.01)
                    and float_compare(record.selling_price, record.expected_price * 0.9, precision_rounding=0.01) < 0):
                raise ValidationError("The selling price cannot be lower than 90% of the expected price")

    @api.depends("offer_ids.price")
    def _compute_max_offer_price(self):
        for record in self:
            # record.best_price = max(id.price for id in record.offer_ids)
            record.best_price = max(record.offer_ids.mapped("price"), default=0)

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden == True:
            self.garden_area = 10
            self.garden_orientation = 'north'
            self.score = 7
        else:
            self.garden_area = 0
            self.garden_orientation = False
            self.score = 0
            # u can return a warning if u want
        # return {'warning': {
        #     'title': ("Warning"),
        #     'message': ('This option is not supported for Authorize.net')}}

    def action_cancel_property(self):
        for record in self:
            if record.state != 'sold':
                record.state = 'cancelled'
            else:
                raise UserError("Sold properties cannot be cancelled. edited")

    def action_sold_property(self):
        for record in self:
            if record.state != 'cancelled':
                record.state = 'sold'
            else:
                raise UserError("Cancelled properties cannot be sold.")

    @api.constrains('score')
    def _check_score(self):
        for record in self:
            if not (1 <= record.score <= 10):
                raise ValidationError("The score must be between 1 and 10.")


    def generate_daily_report(self):
        """Generate and save the daily property report."""
        try:
            # report_dir = 'C:/Program Files/Odoo 18.0.20241124/server/odoo/addons/estate'
            report_dir = '/opt/odoo/server/odoo/addons/estate'
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)

            # properties = self.search([], limit=100)
            properties = self.env['estate.property'].sudo().search([('active', '=', False)], limit=100)
            _logger.info(f"Fetched properties: {properties}")
            if not properties:
                _logger.warning("No properties found to generate the report.")
                return

            # report_action = self.env.ref('estate.estate_property_report_action')
            # if not report_action:
            #     _logger.error("Report action not found.")

            # Render the template
            # rendered_report = report._render({
            #     'docs': properties,
            # })

            # Generate the report using the QWeb template
            # rendered_report = self.env['ir.actions.report'].sudo()._render_qweb_html(
            #     report_action.id, properties
            # )
            # report_filename = f"daily_property_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.html"
            report_filename = f"daily_property_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            file_path = os.path.join(report_dir, report_filename)
            if not file_path:
                _logger.error("File path is not set correctly.")
                return
            with open(file_path, 'w') as f:
                # f.write(rendered_report)
                # f.write(rendered_report[0])
                # f.write("Hello\n")
                f.write("Daily Property Report\n")
                f.write("=" * 30 + "\n")
                for property in properties:
                    f.write(f"Property Name: {property.name}\n")
                    f.write(f"Status: {property.postcode}\n")
                    f.write(f"Offer Deadline: {property.bedrooms}\n")
                    f.write("-" * 30 + "\n")
        except Exception as e:
            _logger.info(f"Generated file: {e}")

# logic applied during normal record deletion not when the module is uninstalled
    @api.ondelete(at_uninstall=False)
    def _prevent_deletion(self):
        for record in self:
            if record.state not in ('new', 'cancelled'):
                    # use _ if u need translation: _("You cannot delete a property unless its state is 'New' or 'Cancelled'.")
                raise UserError("You cannot delete a property unless its state is 'New' or 'Cancelled'.")


    # @api.model
    # def action_insert_properties(self, *args, **kwargs):
    #     start_time = time.time()
    #     property_types = self.env['estate.property.type'].search([])  # Get all property types
    #     property_tags = self.env['estate.property.tag'].search([])  # Get all property tags
    #     property_data = []
    #     batch_size = 1000
    #     for i in range(9000000, 10000001):
    #         letters = random.choices(string.ascii_uppercase, k=2)  # Two random uppercase letters
    #         digits = random.choices(string.digits, k=3)  # Three random digits
    #         last_letters = random.choices(string.ascii_uppercase, k=2)  # Two more random uppercase letters
    #         postcode = f"{''.join(letters)}-{''.join(digits)}-{''.join(last_letters)}"
    #         property_type = property_types[i % len(property_types)]
    #         tags = random.sample(property_tags, 2) if len(property_tags) >= 2 else property_tags
    #
    #         property_data.append(
    #             {
    #                 'name': f'Property {i}',
    #                 'expected_price': 4 + i % 1000000,
    #                 'description': f'This is property {i}',
    #                 'postcode': postcode,
    #                 'living_area': i % 100,
    #                 'facades': i%4,
    #                 'bedrooms': 1 + i%6,
    #                 'garage': True if i % 2 == 0 else False,
    #                 'garden': True if i % 2 != 0 else False,
    #                 'garden_area': 20 if i % 2 != 0 else 0,
    #                 'garden_orientation': 'north' if i % 2 != 0 else None,
    #                 'state': 'new',
    #                 'property_type_id': property_type.id,  # Link property type
    #                 'tag_ids': [(6, 0, [tag.id for tag in tags])],
    #             }
    #         )
    #         if len(property_data) >= batch_size:
    #             self.env['estate.property'].create(property_data)
    #             property_data = []
    #             print(f'{i} records inserted')
    #
    #     if len(property_data) >= batch_size:
    #         self.env['estate.property'].create(property_data)
    #         property_data = []  # Clear the list after batch inser
    #
    #     end_time = time.time()
    #     time_taken = end_time - start_time
    #     print(f'Time taken for inserting 10,000 records: {time_taken} seconds')

