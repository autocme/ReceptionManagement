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
    br_company_id = fields.Many2one(
        'res.partner',
        string='Company',
        required=True,
        domain=[('is_company', '=', True)],
        placeholder='Select the company associated with this renter',
        help='The company associated with this renter',
        tracking=True
    )
    br_communications_officer_id = fields.Many2one(
        'res.partner',
        string='Communications Officer',
        required=True,
        placeholder='Select the communications officer',
        help='The person responsible for communications with this renter',
        tracking=True
    )
    br_garage_slot_ids = fields.One2many(
        'garage.slot',
        'gs_renter_id',
        string='Garage Slots',
        help='List of garage slots assigned to this renter'
    )
    br_scheduled_payment_ids = fields.One2many(
        'scheduled.payment',
        'sp_renter_id',
        string='Scheduled Payments',
        help='List of scheduled payments for this renter'
    )
    br_invitation_count = fields.Integer(
        string='Invitation Count',
        compute='_compute_invitation_count',
        help='Number of invitations created for this renter'
    )

    @api.depends('br_company_id')
    def _compute_name(self):
        """
        Compute the display name based on company
        """
        for record in self:
            if record.br_company_id:
                record.name = record.br_company_id.name
            else:
                record.name = 'Draft Renter'

    def _compute_invitation_count(self):
        """
        Compute the number of invitations for this renter
        """
        for record in self:
            record.br_invitation_count = self.env['reception.invitation'].search_count([
                ('ri_renter_id', '=', record.id)
            ])

    def action_view_invitations(self):
        """
        Action to view invitations for this renter
        """
        self.ensure_one()
        action = self.env.ref('j_reception.action_reception_invitation_tree').read()[0]
        action['domain'] = [('ri_renter_id', '=', self.id)]
        action['context'] = {
            'default_ri_renter_id': self.id,
            'search_default_ri_renter_id': self.id,
        }
        return action

    def check_due_payments(self):
        """
        Cron method to check for due payments and send notifications
        """
        today = fields.Date.today()
        due_payments = self.env['scheduled.payment'].search([
            ('sp_due_date', '<=', today),
            ('sp_is_notified', '=', False)
        ])
        
        for payment in due_payments:
            # Send notification email
            template = self.env.ref('j_reception.email_template_payment_due')
            if template:
                template.send_mail(payment.id, force_send=True)
            # Mark as notified
            payment.sp_is_notified = True