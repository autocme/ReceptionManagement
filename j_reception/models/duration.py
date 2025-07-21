# -*- coding: utf-8 -*-
"""
Duration model for managing booking durations
"""

from odoo import models, fields, api, _


class Duration(models.Model):
    """
    Model to manage booking durations
    """
    _name = 'duration'
    _description = 'Duration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'minutes'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=False,
        help='Display name for the duration'
    )
    minutes = fields.Integer(
        string='Minutes',
        required=True,
        placeholder='e.g., 30, 60, 90',
        help='Duration in minutes',
        tracking=True
    )

    def _compute_name(self):
        """
        Compute the display name based on minutes with proper translation
        """
        for record in self:
            if record.minutes:
                if record.minutes < 60:
                    record.name = f"{record.minutes} {record.with_context(lang=record.env.user.lang).env._('min')}"
                elif record.minutes == 60:
                    record.name = f"1 {record.with_context(lang=record.env.user.lang).env._('hour')}"
                elif record.minutes % 60 == 0:
                    hours = record.minutes // 60
                    record.name = f"{hours} {record.with_context(lang=record.env.user.lang).env._('hours')}"
                else:
                    hours = record.minutes // 60
                    mins = record.minutes % 60
                    record.name = f"{hours}h {mins}{record.with_context(lang=record.env.user.lang).env._('min')}"
            else:
                record.name = record.with_context(lang=record.env.user.lang).env._("New Duration")