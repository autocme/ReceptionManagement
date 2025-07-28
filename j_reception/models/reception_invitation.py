# -*- coding: utf-8 -*-
"""
Reception Invitation model for managing building invitations
"""

from odoo import models, fields, api, _
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
    _order = 'sequence desc'

    sequence = fields.Char(
        string='Sequence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Unique sequence number for the invitation'
    )
    officer_id = fields.Many2one(
        'res.users',
        string='Officer',
        required=True,
        default=lambda self: self.env.user,
        domain=lambda self: [('id', 'in', self.env['building.renter'].search([]).mapped('officer_id.id'))],
        placeholder='Select the officer',
        help='The user responsible for this invitation',
        tracking=True
    )
    renter_id = fields.Many2one(
        'building.renter',
        string='Renter',
        required=True,
        readonly=True,
        compute='_compute_renter_id',
        help='The renter associated with this invitation',
        tracking=True
    )
    subject = fields.Char(
        string='Subject',
        required=True,
        placeholder='Enter invitation subject',
        help='Subject of the invitation'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('attended', 'Attended'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True, tracking=True, copy=False,
       help='Current state of the invitation')
    invitation_datetime = fields.Datetime(
        string='Date',
        required=True,
        placeholder='Set invitation date and time',
        help='Scheduled date and time for the invitation',
        tracking=True
    )
    guest_partner_id = fields.Many2one(
        'res.partner',
        string='Guest',
        required=True,
        domain=lambda self: [('create_uid', '=', self.env.user.id)],
        placeholder='Select the guest',
        help='The guest partner for this invitation'
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Display name for the invitation'
    )
    officer_readonly = fields.Boolean(
        string='Officer Readonly',
        compute='_compute_officer_readonly',
        help='Control whether officer field is readonly based on user permissions'
    )

    @api.depends('sequence', 'guest_partner_id', 'renter_id')
    def _compute_name(self):
        """
        Compute the display name for the invitation
        """
        for record in self:
            if record.sequence != '/':
                renter_name = record.renter_id.name if record.renter_id else 'Unknown'
                guest_name = record.guest_partner_id.name if record.guest_partner_id else 'Unknown'
                record.name = f"{record.sequence} - {guest_name} ({renter_name})"
            else:
                record.name = 'Draft Invitation'

    @api.depends('officer_id')
    def _compute_renter_id(self):
        """
        Auto-populate renter when officer changes
        """
        for rec in self:
            if rec.officer_id:
                renter = self.env['building.renter'].search([
                    ('officer_id', '=', rec.officer_id.id)
                ], limit=1)
                if renter:
                    rec.renter_id = renter.id
                else:
                    rec.renter_id = False
            else:
                # If no officer selected, clear renter field
                rec.renter_id = False

    @api.depends('officer_id')
    def _compute_officer_readonly(self):
        """
        Control whether officer field is readonly based on user permissions
        """
        for record in self:
            # Check if user has admin group
            if self.env.user.has_group('j_reception.group_j_reception_admin'):
                # Admins can always edit officer field
                record.officer_readonly = False
            elif self.env.user.has_group('j_reception.group_j_reception_renter'):
                # Tenants cannot edit officer field (readonly)
                record.officer_readonly = True
            else:
                # Other users cannot edit officer field
                record.officer_readonly = True

    @api.model
    def default_get(self, fields_list):
        """
        Set default values for renter based on current user
        """
        res = super(ReceptionInvitation, self).default_get(fields_list)
        if 'renter_id' in fields_list:
            current_user = self.env.user
            renter = self.env['building.renter'].search([
                ('officer_id', '=', current_user.id)
            ], limit=1)
            if renter:
                res['renter_id'] = renter.id
        return res

    @api.constrains('officer_id', 'renter_id')
    def _check_officer_renter_relationship(self):
        """
        Ensure officer can only create invitations for their assigned renter
        (except for Reception Administrators who can create for any renter)
        """
        for record in self:
            if record.officer_id and record.renter_id:
                # Skip constraint check for Reception Administrators
                if self.env.user.has_group('j_reception.group_j_reception_admin'):
                    continue

                if record.renter_id.officer_id.id != record.officer_id.id:
                    raise ValidationError(
                        f"You can only create invitations for renters you are assigned to. "
                        f"You are not the officer for '{record.renter_id.name}'."
                    )

    @api.model
    def create(self, vals):
        """
        Override create to generate sequence
        """
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('reception.invitation') or _('New')

        invitation = super(ReceptionInvitation, self).create(vals)

        return invitation

    def write(self, vals):
        """
        Override write to handle datetime changes and state changes
        """
        datetime_changed = False
        state_changed = False

        for record in self:
            if 'invitation_datetime' in vals and vals['invitation_datetime'] != record.invitation_datetime:
                datetime_changed = True
            if 'state' in vals and vals['state'] != record.state:
                state_changed = True

        result = super(ReceptionInvitation, self).write(vals)

        # Send datetime change notification
        if datetime_changed:
            for record in self:
                record._send_datetime_change_email()

        # Send initial invitation email when state changes to scheduled
        if state_changed and vals.get('state') == 'scheduled':
            for record in self:
                record._send_invitation_email()

        # Send attendance notification
        if state_changed and vals.get('state') == 'attended':
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

    def action_confirm(self):
        """
        Action to confirm invitation (draft -> scheduled)
        """
        self.write({'state': 'scheduled'})

    def action_mark_attended(self):
        """
        Action to mark invitation as attended
        """
        self.write({'state': 'attended'})

    def action_mark_cancelled(self):
        """
        Action to mark invitation as cancelled
        """
        self.write({'state': 'cancelled'})



    @api.constrains('invitation_datetime')
    def _check_future_datetime(self):
        """
        Validate that invitation datetime is in the future (for new invitations)
        """
        for record in self:
            if record.invitation_datetime and record.state in ['draft', 'scheduled']:
                if record.invitation_datetime <= fields.Datetime.now():
                    raise ValidationError('Invitation date and time must be in the future.')

    @api.model
    def check_overdue_invitations(self):
        """
        Cron method to check for overdue invitations
        """
        now = fields.Datetime.now()
        overdue_invitations = self.search([
            ('state', '=', 'scheduled'),
            ('invitation_datetime', '<', now)
        ])

        overdue_invitations.write({'state': 'overdue'})