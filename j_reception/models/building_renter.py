# -*- coding: utf-8 -*-
"""
Building Renter model for managing building rental information
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BuildingRenter(models.Model):
    """
    Main model for managing renter information
    """
    _name = 'building.renter'
    _description = 'Building Renter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Display name for the renter'
    )
    company_id = fields.Many2one(
        'res.partner',
        string='Company',
        required=True,
        domain=[('is_company', '=', True)],
        context={'default_is_company': True},
        placeholder='Select the company associated with this renter',
        help='The company associated with this renter',
        tracking=True
    )
    officer_id = fields.Many2one(
        'res.users',
        string='Officer',
        required=True,
        placeholder='Select the officer',
        help='The person responsible for communications with this renter',
        tracking=True
    )
    garage_slot_ids = fields.One2many(
        'garage.slot',
        'renter_id',
        string='Garage Slots',
        help='List of garage slots assigned to this renter'
    )
    scheduled_payment_ids = fields.One2many(
        'scheduled.payment',
        'renter_id',
        string='Scheduled Payments',
        help='List of scheduled payments for this renter'
    )
    invitation_count = fields.Integer(
        string='Invitation Count',
        compute='_compute_invitation_count',
        help='Number of invitations created for this renter'
    )

    @api.depends('company_id')
    def _compute_name(self):
        """
        Compute the display name based on company
        """
        for record in self:
            if record.company_id:
                record.name = record.company_id.name
            else:
                record.name = 'Draft Renter'

    @api.constrains('company_id')
    def _check_unique_company_officer(self):
        """
        Ensure one company can only have one officer
        """
        for record in self:
            if record.company_id:
                existing = self.search([
                    ('company_id', '=', record.company_id.id),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        f"Company '{record.company_id.name}' already has an officer assigned. "
                        f"Each company can only have one officer."
                    )

    def _compute_invitation_count(self):
        """
        Compute the number of invitations for this renter
        """
        for record in self:
            record.invitation_count = self.env['reception.invitation'].search_count([
                ('renter_id', '=', record.id)
            ])

    def action_view_invitations(self):
        """
        Action to view invitations for this renter
        """
        self.ensure_one()
        action = self.env.ref('j_reception.action_reception_invitation_tree').read()[0]
        action['domain'] = [('renter_id', '=', self.id)]
        action['context'] = {
            'default_renter_id': self.id,
            'search_default_renter_id': self.id,
        }
        return action

    def check_due_payments(self):
        """
        Cron method to check for due payments and send notifications
        """
        today = fields.Date.today()
        due_payments = self.env['scheduled.payment'].search([
            ('due_date', '<=', today),
            ('is_notified', '=', False)
        ])
        
        for payment in due_payments:
            # Send notification email
            template = self.env.ref('j_reception.email_template_payment_due')
            if template:
                template.send_mail(payment.id, force_send=True)
            # Mark as notified
            payment.is_notified = True