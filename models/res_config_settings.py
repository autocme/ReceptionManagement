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

    # Configuration field for geographical location URL
    j_reception_location_url = fields.Char(
        string='Geographical Location URL',
        config_parameter='j_reception.location_url',
        help='URL to the geographical location that will be included in invitation emails (e.g., Google Maps link)'
    )

    @api.model
    def get_values(self):
        """
        Get configuration values
        """
        res = super(ResConfigSettings, self).get_values()
        res.update(
            j_reception_location_url=self.env['ir.config_parameter'].sudo().get_param('j_reception.location_url', default='')
        )
        return res

    def set_values(self):
        """
        Set configuration values
        """
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('j_reception.location_url', self.j_reception_location_url)
