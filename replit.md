# J Reception - Building Invitations & Rental Management

## Overview

J Reception is an Odoo module designed for comprehensive management of building invitations and rental information. The system provides automated email notifications, role-based access control, and streamlined management of renter information including company details, garage slots, and scheduled payments.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Framework and Platform
- **Platform**: Odoo 15.0 (Enterprise Resource Planning framework)
- **Language**: Python 3
- **Architecture Pattern**: MVC (Model-View-Controller) following Odoo's standard structure
- **Database**: PostgreSQL (standard for Odoo installations)
- **ORM**: Odoo's built-in ORM for database operations

### Module Structure
The module follows Odoo's standard addon structure:
- `__manifest__.py` - Module configuration and dependencies
- `models/` - Business logic and data models
- `security/` - Access control and permissions
- `data/` - Initial data, sequences, and email templates
- `views/` - User interface definitions

## Key Components

### 1. Data Models

#### Building Renter Model (`building.renter`)
- **Purpose**: Manages building tenant information
- **Field Prefix**: `br_` (Building Renter)
- **Features**: Company details, communications officer, garage slots, scheduled payments
- **Inheritance**: Extends `mail.thread` and `mail.activity.mixin` for communication tracking

#### Reception Invitation Model (`reception.invitation`)
- **Purpose**: Manages building invitations with automated workflows
- **Field Prefix**: `ri_` (Reception Invitation)
- **States**: Scheduled, Attended, Overdue, Cancelled
- **Features**: State tracking, responsible user assignment, automated notifications
- **Inheritance**: Extends `mail.thread` and `mail.activity.mixin` for activity tracking

#### Garage Slot Model (`garage.slot`)
- **Purpose**: Manages garage slot assignments for renters
- **Field Prefix**: `gs_` (Garage Slot)
- **Features**: Unique slot numbering, descriptions, validation constraints
- **Relationship**: Many-to-One with Building Renter model

#### Scheduled Payment Model (`scheduled.payment`)
- **Purpose**: Manages scheduled payments for renters
- **Field Prefix**: `sp_` (Scheduled Payment)
- **Features**: Payment tracking, due date notifications, amount validation
- **Relationship**: Many-to-One with Building Renter model

### 2. Configuration Management

#### Settings Model (`res.config.settings`)
- **Purpose**: Extends Odoo's configuration system
- **Features**: Geographical location URL configuration for email templates
- **Storage**: Uses Odoo's `ir.config_parameter` for persistent configuration

### 3. Security Framework

#### Access Control
- **Groups**: Role-based access control for renters and administrators
- **Permissions**: Model-level access rights defined in `ir.model.access.csv`
- **Security Groups**: Defined in `security/security_groups.xml`

### 4. Communication System

#### Email Templates
- **Automated Notifications**: Email templates for various invitation scenarios
- **Template Engine**: Uses Odoo's QWeb templating system
- **Personalization**: Templates include renter-specific information and location URLs

#### Automated Actions
- **Triggers**: Automated actions based on invitation state changes
- **Workflow**: Handles state transitions and notification scheduling

## Data Flow

### Invitation Workflow
1. **Creation**: Invitation created with 'scheduled' state
2. **Assignment**: Responsible user assigned to invitation
3. **Notification**: Automated email sent to renter
4. **State Management**: Manual or automated state transitions (attended/overdue/cancelled)
5. **Tracking**: All changes logged through mail.thread inheritance

### Renter Management
1. **Registration**: Renter created with company and contact details
2. **Garage Assignment**: Garage slots assigned with validation
3. **Communication**: Integration with Odoo's communication tools
4. **Payment Tracking**: Scheduled payment information management

## External Dependencies

### Odoo Core Modules
- **base**: Core Odoo functionality
- **mail**: Email and communication features
- **base_setup**: Configuration and setup utilities

### Third-party Integrations
- **Email Service**: Relies on Odoo's email infrastructure
- **Database**: PostgreSQL for data persistence
- **Web Framework**: Odoo's web client for user interface

## Deployment Strategy

### Installation Requirements
- Odoo 15.0 platform
- PostgreSQL database
- SMTP server for email notifications
- Web server (typically nginx or Apache)

### Configuration Steps
1. Install module dependencies
2. Configure email server settings
3. Set up geographical location URL
4. Configure security groups and permissions
5. Initialize sequence numbers and email templates

### Maintenance Considerations
- Regular backup of renter and invitation data
- Email template updates for business changes
- Security group review for access control
- Performance monitoring for database queries

## Architecture Decisions

### Field Naming Convention
- **Problem**: Need consistent, readable field naming across models
- **Solution**: Prefix-based naming (ri_ for reception invitations, br_ for building renters, gs_ for garage slots, sp_ for scheduled payments)
- **Rationale**: Improves code readability and prevents naming conflicts

### State Management
- **Problem**: Track invitation lifecycle with clear states
- **Solution**: Selection fields with predefined states and tracking
- **Rationale**: Provides clear workflow visibility and audit trail

### Email Integration
- **Problem**: Automated communication with renters
- **Solution**: Odoo's mail.thread inheritance and email templates
- **Rationale**: Leverages proven email infrastructure with tracking capabilities

### Security Model
- **Problem**: Control access to sensitive renter information
- **Solution**: Odoo's group-based security with custom groups
- **Rationale**: Provides flexible, role-based access control