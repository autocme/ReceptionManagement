# -*- coding: utf-8 -*-
{
    'name': 'J Reception - Building Invitations & Rental Management',
    'version': '15.0.1.0.0',
    'category': 'Real Estate',
    'summary': 'Manage building invitations and rental information with automated notifications',
    'description': """
        J Reception Module
        ==================
        This module provides comprehensive management for building invitations and rental information.
        
        Features:
        - Renter management with company details, communications officer, garage slots, and scheduled payments
        - Invitation management with automated email notifications
        - Role-based access control for renters and administrators
        - Settings configuration for geographical location
        - Automated email notifications for various scenarios
    """,
    'author': 'J Reception Team',
    'depends': ['base', 'mail', 'base_setup'],
    'data': [
        # Security
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence.xml',
        'data/ir_sequence.xml',
        'data/email_templates.xml',
        'data/automated_actions.xml',
        
        # Views
        'views/renter_views.xml',
        'views/invitation_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
