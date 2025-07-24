# -*- coding: utf-8 -*-
"""
Booking model for managing facility bookings
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import pytz


class Booking(models.Model):
    """
    Model to manage facility bookings
    """
    _name = 'booking'
    _description = 'Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'booking_datetime desc'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        help='Display name for the booking'
    )
    facility_id = fields.Many2one(
        'facilities',
        string='Facility',
        required=True,
        placeholder='Select the facility',
        help='The facility being booked',
        tracking=True
    )
    duration_id = fields.Many2one(
        'duration',
        string='Duration',
        required=True,
        placeholder='Select the duration',
        help='Duration of the booking',
        tracking=True
    )
    booking_datetime = fields.Datetime(
        string='Booking Date',
        required=True,
        placeholder='Select date and time',
        help='Date and time of the booking',
        tracking=True
    )
    officer_id = fields.Many2one(
        'res.users',
        string='Officer',
        required=True,
        default=lambda self: self.env.user,
        help='The officer responsible for this booking'
    )
    renter_id = fields.Many2one(
        'building.renter',
        string='Tenant',
        required=True,
        default=lambda self: self._get_default_renter(),
        placeholder='Select the tenant',
        help='The tenant making the booking',
        tracking=True
    )


    @api.depends('facility_id', 'booking_datetime', 'renter_id')
    def _compute_name(self):
        """
        Compute the display name for the booking
        """
        for record in self:
            if record.facility_id and record.booking_datetime:
                # Convert UTC datetime to user's timezone for display
                user_tz = pytz.timezone(record.env.user.tz or 'Asia/Riyadh')
                booking_date_local = pytz.utc.localize(record.booking_datetime).astimezone(user_tz)
                booking_date = booking_date_local.strftime('%Y-%m-%d %H:%M')
                record.name = f"{record.facility_id.name} - {booking_date}"
            else:
                record.name = _('Draft Booking')

    def _get_default_renter(self):
        """
        Get default renter based on current user's officer relationship
        """
        renter = self.env['building.renter'].search([('officer_id', '=', self.env.user.id)], limit=1)
        return renter.id if renter else False

    @api.depends('renter_id')
    def _compute_show_renter_field(self):
        """
        Control visibility of renter field based on user permissions
        """
        for record in self:
            # Check if user has admin group
            if self.env.user.has_group('j_reception.group_j_reception_admin'):
                record.show_renter_field = True
            # Check if user has tenant group
            elif self.env.user.has_group('j_reception.group_j_reception_renter'):
                # Show only if current user is officer of the renter in this booking
                if record.renter_id.sudo() and record.renter_id.sudo().officer_id == self.env.user:
                    record.show_renter_field = True
                else:
                    record.show_renter_field = False
            else:
                record.show_renter_field = False

    @api.constrains('facility_id', 'booking_datetime', 'duration_id')
    def _check_booking_conflict(self):
        """
        Ensure no booking conflicts for the same facility
        """
        for record in self:
            if record.facility_id and record.booking_datetime and record.duration_id:
                # Calculate end time
                end_time = record.booking_datetime + timedelta(minutes=record.duration_id.minutes)

                # Check for overlapping bookings
                existing_bookings = self.search([
                    ('facility_id', '=', record.facility_id.id),
                    ('id', '!=', record.id)
                ])

                for booking in existing_bookings:
                    existing_end_time = booking.booking_datetime + timedelta(minutes=booking.duration_id.minutes)

                    # Check if times overlap
                    if (record.booking_datetime < existing_end_time and 
                        end_time > booking.booking_datetime):
                        # Convert times to user's timezone for error message
                        user_tz = pytz.timezone(record.env.user.tz or 'Asia/Riyadh')
                        booking_start_local = pytz.utc.localize(booking.booking_datetime).astimezone(user_tz)
                        booking_end_local = pytz.utc.localize(existing_end_time).astimezone(user_tz)

                        raise ValidationError(
                            _("The facility '%s' is already booked from %s to %s. Please choose a different time.") % (
                                record.facility_id.name,
                                booking_start_local.strftime('%Y-%m-%d %H:%M'),
                                booking_end_local.strftime('%Y-%m-%d %H:%M')
                            )
                        )

    @api.constrains('renter_id', 'booking_datetime', 'duration_id')
    def _check_daily_booking_limit(self):
        """
        Check if tenant exceeds daily booking limit
        """
        for record in self:
            if record.renter_id.sudo() and record.booking_datetime and record.duration_id:
                # Get daily booking limit from settings
                daily_limit = int(self.env['ir.config_parameter'].sudo().get_param('j_reception.daily_booking_limit', 0))

                if daily_limit > 0:
                    # Get start and end of the booking day
                    booking_date = record.booking_datetime.date()
                    day_start = datetime.combine(booking_date, datetime.min.time())
                    day_end = datetime.combine(booking_date, datetime.max.time())

                    # Find all bookings for this renter on the same day
                    same_day_bookings = self.search([
                        ('renter_id', '=', record.renter_id.sudo().id),
                        ('booking_datetime', '>=', day_start),
                        ('booking_datetime', '<=', day_end),
                        ('id', '!=', record.id)
                    ])

                    # Calculate total minutes booked
                    total_minutes = sum(booking.duration_id.minutes for booking in same_day_bookings)
                    total_minutes += record.duration_id.minutes

                    if total_minutes > daily_limit:
                        raise ValidationError(
                            _("Daily booking limit exceeded. You can only book %s minutes per day. Currently booked: %s minutes. Trying to book: %s minutes.") % (
                                daily_limit,
                                total_minutes - record.duration_id.minutes,
                                record.duration_id.minutes
                            )
                        )

    @api.constrains('booking_datetime')
    def _check_future_datetime(self):
        """
        Ensure booking is in the future
        """
        for record in self:
            if record.booking_datetime:
                # Get current time in UTC (same as what's stored in booking_datetime)
                now_utc = fields.Datetime.now()

                # Add a 1 minute buffer to avoid immediate expiration
                if record.booking_datetime <= now_utc:
                    # Convert times to user's timezone for error message
                    user_tz = pytz.timezone(record.env.user.tz or 'Asia/Riyadh')
                    booking_local = pytz.utc.localize(record.booking_datetime).astimezone(user_tz)
                    now_local = pytz.utc.localize(now_utc).astimezone(user_tz)

                    raise ValidationError(
                        _("Booking time must be in the future. Selected time: %s Current time: %s Please select a future date and time.") % (
                            booking_local.strftime('%Y-%m-%d %H:%M'),
                            now_local.strftime('%Y-%m-%d %H:%M')
                        )
                    )

    def write(self, vals):
        """
        Override write method to control edit permissions for tenant users
        """
        # Check if user has admin group - allow all edits
        if self.env.user.has_group('j_reception.group_j_reception_admin'):
            return super(Booking, self).write(vals)

        # Check if user has tenant group - restrict edits
        if self.env.user.has_group('j_reception.group_j_reception_renter'):
            for record in self:
                # Check if current user is officer of the renter for this booking
                if not (record.renter_id.sudo() and record.renter_id.sudo().officer_id == self.env.user):
                    raise UserError(
                        _("You are not authorized to edit this booking. You can only edit bookings for tenants where you are the officer.")
                    )

        return super(Booking, self).write(vals)