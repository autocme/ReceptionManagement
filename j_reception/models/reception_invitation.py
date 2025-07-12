# -*- coding: utf-8 -*-
"""
Reception Invitation model for managing building invitations
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import re


class ReceptionInvitation(models.Model):
    """
    Model for managing building invitations
    """
    _name = 'reception.invitation'
    _description = 'Reception Invitation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ri_sequence desc'

    ri_sequence = fields.Char(
        string='Sequence',
        required=True,
        copy=False,
        readonly=True,
        default='/',
        help='Unique sequence number for the invitation'
    )
    ri_responsible_user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        required=True,
        default=lambda self: self.env.user,
        placeholder='Select the responsible user',
        help='The user responsible for this invitation',
        tracking=True
    )
    ri_renter_id = fields.Many2one(
        'building.renter',
        string='Renter',
        required=True,
        placeholder='Select the renter for this invitation',
        help='The renter associated with this invitation',
        tracking=True
    )
    ri_state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('attended', 'Attended'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='scheduled', required=True, tracking=True,
       help='Current state of the invitation')
    ri_invitation_datetime = fields.Datetime(
        string='Invitation Date & Time',
        required=True,
        placeholder='Set invitation date and time',
        help='Scheduled date and time for the invitation',
        tracking=True
    )
    ri_guest_name = fields.Char(
        string='Guest Name',
        required=True,
        placeholder='Enter guest full name',
        help='Full name of the guest'
    )
    ri_guest_email = fields.Char(
        string='Guest Email',
        required=True,
        placeholder='Enter guest email address',
        help='Email address of the guest for notifications'
    )
    ri_guest_phone = fields.Char(
        string='Guest Phone',
        placeholder='Enter guest phone number',
        help='Phone number of the guest'
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Display name for the invitation'
    )

    @api.depends('ri_sequence', 'ri_guest_name', 'ri_renter_id')
    def _compute_name(self):
        """
        Compute the display name for the invitation
        """
        for record in self:
            if record.ri_sequence != '/':
                renter_name = record.ri_renter_id.name if record.ri_renter_id else 'Unknown'
                record.name = f"{record.ri_sequence} - {record.ri_guest_name} ({renter_name})"
            else:
                record.name = 'Draft Invitation'

    @api.model
    def create(self, vals):
        """
        Override create to generate sequence and send initial email
        """
        if vals.get('ri_sequence', '/') == '/':
            vals['ri_sequence'] = self.env['ir.sequence'].next_by_code('reception.invitation') or '/'
        
        invitation = super(ReceptionInvitation, self).create(vals)
        
        # Send initial invitation email
        invitation._send_invitation_email()
        
        return invitation

    def write(self, vals):
        """
        Override write to handle datetime changes and state changes
        """
        datetime_changed = False
        state_changed = False
        
        for record in self:
            if 'ri_invitation_datetime' in vals and vals['ri_invitation_datetime'] != record.ri_invitation_datetime:
                datetime_changed = True
            if 'ri_state' in vals and vals['ri_state'] != record.ri_state:
                state_changed = True
        
        result = super(ReceptionInvitation, self).write(vals)
        
        # Send datetime change notification
        if datetime_changed:
            for record in self:
                record._send_datetime_change_email()
        
        # Send attendance notification
        if state_changed and vals.get('ri_state') == 'attended':
            for record in self:
                record._send_attendance_notification()
        
        return result

    def _send_invitation_email(self):
        """
        Send initial invitation email to guest
        """
        template = self.env.ref('j_reception.email_template_new_invitation', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_datetime_change_email(self):
        """
        Send email notification when invitation datetime changes
        """
        template = self.env.ref('j_reception.email_template_datetime_change', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_attendance_notification(self):
        """
        Send notification to responsible user when guest attends
        """
        template = self.env.ref('j_reception.email_template_attendance_notification', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)

    def action_mark_attended(self):
        """
        Action to mark invitation as attended
        """
        self.write({'ri_state': 'attended'})

    def action_mark_cancelled(self):
        """
        Action to mark invitation as cancelled
        """
        self.write({'ri_state': 'cancelled'})

    @api.constrains('ri_guest_email')
    def _check_email_format(self):
        """
        Validate email format
        """
        for record in self:
            if record.ri_guest_email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.ri_guest_email):
                    raise ValidationError('Please enter a valid email address.')

    @api.constrains('ri_invitation_datetime')
    def _check_future_datetime(self):
        """
        Validate that invitation datetime is in the future (for new invitations)
        """
        for record in self:
            if record.ri_invitation_datetime and record.ri_state == 'scheduled':
                if record.ri_invitation_datetime <= fields.Datetime.now():
                    raise ValidationError('Invitation date and time must be in the future.')

    @api.model
    def check_overdue_invitations(self):
        """
        Cron method to check for overdue invitations
        """
        now = fields.Datetime.now()
        overdue_invitations = self.search([
            ('ri_state', '=', 'scheduled'),
            ('ri_invitation_datetime', '<', now)
        ])
        
        overdue_invitations.write({'ri_state': 'overdue'})