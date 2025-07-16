# -*- coding: utf-8 -*-
"""
Configuration settings for J Reception module
"""

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    """
    Configuration settings for J Reception module
    """
    _inherit = 'res.config.settings'

    j_reception_location_url = fields.Char(
        string='Geographical Location URL',
        config_parameter='j_reception.location_url',
        help='URL to the geographical location that will be included in invitation emails (e.g., Google Maps link)'
    )
    j_reception_building_image = fields.Binary(
        string='Building Image',
        config_parameter='j_reception.building_image',
        help='Image of the building that will be included in invitation emails'
    )
    j_reception_daily_booking_limit = fields.Integer(
        string='Daily Booking Limit (Minutes)',
        config_parameter='j_reception.daily_booking_limit',
        default=0,
        help='Maximum minutes a tenant can book per day (0 = no limit)'
    )

    @api.model
    def get_values(self):
        """
        Get configuration values
        """
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            j_reception_location_url=params.get_param('j_reception.location_url', default=''),
        )
        return res

    def set_values(self):
        """
        Set configuration values
        """
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('j_reception.location_url', self.j_reception_location_url or '')