# -*- coding: utf-8 -*-
"""
Garage Slot model for managing garage slot assignments
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class GarageSlot(models.Model):
    """
    Model to manage garage slots for renters
    """
    _name = 'garage.slot'
    _description = 'Garage Slot'
    _order = 'number'

    renter_id = fields.Many2one(
        'building.renter',
        string='Renter',
        required=True,
        ondelete='cascade',
        help='The renter who owns this garage slot'
    )
    number = fields.Char(
        string='Number',
        required=True,
        placeholder='e.g., A-15',
        help='Garage slot number or identifier'
    )

    @api.constrains('number', 'renter_id')
    def _check_unique_garage_number(self):
        """
        Ensure garage slot numbers are unique within the same renter
        """
        for record in self:
            if record.renter_id:
                existing = self.search([
                    ('number', '=', record.number),
                    ('renter_id', '=', record.renter_id.id),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        f'Garage slot number "{record.number}" already exists for this renter. '
                        'Please use a different number.'
                    )