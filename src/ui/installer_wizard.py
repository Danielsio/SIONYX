"""
SIONYX Installer Configuration Wizard
====================================
This module provides a GUI wizard for first-time setup of SIONYX.
It will be shown when the application is run for the first time without a .env file.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)


class InstallerWizard(QWizard):
    """Main installer wizard"""

    setup_complete = pyqtSignal(dict)  # Emits configuration when setup is complete

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SIONYX Setup Wizard")
        self.setFixedSize(600, 500)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

        # Set wizard style
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setOption(QWizard.WizardOption.HaveCustomButton1, False)
        self.setOption(QWizard.WizardOption.HaveCustomButton2, False)
        self.setOption(QWizard.WizardOption.HaveCustomButton3, False)

        # Create pages
        self.addPage(WelcomePage())
        self.addPage(OrganizationPage())
        self.addPage(FirebasePage())
        self.addPage(PaymentPage())
        self.addPage(SummaryPage())

        # Connect signals
        self.button(QWizard.WizardButton.FinishButton).clicked.connect(
            self.finish_setup
        )

        # Apply styling
        self.setStyleSheet(
            """
            QWizard {
                background-color: #f5f5f5;
            }
            QWizardPage {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #1976D2;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """
        )


class WelcomePage(QWizardPage):
    """Welcome page"""

    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to SIONYX")
        self.setSubTitle("Let's set up your SIONYX application")

        layout = QVBoxLayout()

        # Welcome message
        welcome_label = QLabel(
            """
        <h2>Welcome to SIONYX!</h2>
        <p>This wizard will help you configure your SIONYX application for first-time use.</p>
        
        <h3>What we'll set up:</h3>
        <ul>
            <li><b>Organization Configuration</b> - Your unique organization ID</li>
            <li><b>Firebase Connection</b> - Database and authentication setup</li>
            <li><b>Payment Gateway</b> - Nedarim Plus integration (optional)</li>
        </ul>
        
        <p><b>Note:</b> You'll need your Firebase project credentials and optionally your Nedarim Plus payment gateway details.</p>
        """
        )
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)

        self.setLayout(layout)


class OrganizationPage(QWizardPage):
    """Organization configuration page"""

    def __init__(self):
        super().__init__()
        self.setTitle("Organization Setup")
        self.setSubTitle("Configure your organization details")

        layout = QVBoxLayout()

        # Organization ID
        org_group = QGroupBox("Organization Details")
        org_layout = QFormLayout()

        self.org_id_edit = QLineEdit()
        self.org_id_edit.setPlaceholderText("e.g., tech-lab, school123, mycompany")
        self.org_id_edit.textChanged.connect(self.validate_org_id)
        org_layout.addRow("Organization ID:", self.org_id_edit)

        self.org_name_edit = QLineEdit()
        self.org_name_edit.setPlaceholderText("e.g., Tech Lab, School 123, My Company")
        org_layout.addRow("Organization Name:", self.org_name_edit)

        org_group.setLayout(org_layout)
        layout.addWidget(org_group)

        # Help text
        help_label = QLabel(
            """
        <b>Organization ID:</b> A unique identifier for your organization (lowercase, letters/numbers/hyphens only)<br>
        <b>Organization Name:</b> Display name for your organization<br><br>
        <i>Note: The Organization ID cannot be changed after setup!</i>
        """
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(help_label)

        self.setLayout(layout)

        # Register fields
        self.registerField("org_id", self.org_id_edit)
        self.registerField("org_name", self.org_name_edit)

    def validate_org_id(self):
        """Validate organization ID format"""
        org_id = self.org_id_edit.text()
        if not org_id:
            return

        import re

        if not re.match(r"^[a-z0-9-]+$", org_id):
            self.org_id_edit.setStyleSheet("border-color: #f44336;")
        elif len(org_id) < 3:
            self.org_id_edit.setStyleSheet("border-color: #ff9800;")
        elif org_id.startswith("-") or org_id.endswith("-"):
            self.org_id_edit.setStyleSheet("border-color: #f44336;")
        else:
            self.org_id_edit.setStyleSheet("border-color: #4caf50;")

    def validatePage(self):
        """Validate page before proceeding"""
        org_id = self.org_id_edit.text().strip()
        org_name = self.org_name_edit.text().strip()

        if not org_id or not org_name:
            QMessageBox.warning(
                self, "Validation Error", "Please fill in both Organization ID and Name"
            )
            return False

        import re

        if not re.match(r"^[a-z0-9-]+$", org_id):
            QMessageBox.warning(
                self,
                "Invalid Organization ID",
                "Organization ID must contain only lowercase letters, numbers, and hyphens",
            )
            return False

        if len(org_id) < 3:
            QMessageBox.warning(
                self,
                "Invalid Organization ID",
                "Organization ID must be at least 3 characters long",
            )
            return False

        if org_id.startswith("-") or org_id.endswith("-"):
            QMessageBox.warning(
                self,
                "Invalid Organization ID",
                "Organization ID cannot start or end with a hyphen",
            )
            return False

        return True


class FirebasePage(QWizardPage):
    """Firebase configuration page"""

    def __init__(self):
        super().__init__()
        self.setTitle("Firebase Configuration")
        self.setSubTitle("Connect to your Firebase project")

        layout = QVBoxLayout()

        # Firebase credentials
        firebase_group = QGroupBox("Firebase Project Credentials")
        firebase_layout = QFormLayout()

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("AIza...")
        firebase_layout.addRow("API Key:", self.api_key_edit)

        self.auth_domain_edit = QLineEdit()
        self.auth_domain_edit.setPlaceholderText("your-project.firebaseapp.com")
        firebase_layout.addRow("Auth Domain:", self.auth_domain_edit)

        self.database_url_edit = QLineEdit()
        self.database_url_edit.setPlaceholderText("https://your-project.firebaseio.com")
        firebase_layout.addRow("Database URL:", self.database_url_edit)

        self.project_id_edit = QLineEdit()
        self.project_id_edit.setPlaceholderText("your-project-id")
        firebase_layout.addRow("Project ID:", self.project_id_edit)

        firebase_group.setLayout(firebase_layout)
        layout.addWidget(firebase_group)

        # Help text
        help_label = QLabel(
            """
        <b>Where to find these credentials:</b><br>
        1. Go to <a href="https://console.firebase.google.com/">Firebase Console</a><br>
        2. Select your project<br>
        3. Go to Project Settings → General<br>
        4. Scroll down to "Your apps" section<br>
        5. Copy the configuration values<br><br>
        <i>These credentials are shared across all organizations in your Firebase project.</i>
        """
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        help_label.setOpenExternalLinks(True)
        layout.addWidget(help_label)

        self.setLayout(layout)

        # Register fields
        self.registerField("firebase_api_key", self.api_key_edit)
        self.registerField("firebase_auth_domain", self.auth_domain_edit)
        self.registerField("firebase_database_url", self.database_url_edit)
        self.registerField("firebase_project_id", self.project_id_edit)

    def validatePage(self):
        """Validate Firebase configuration"""
        fields = [
            (self.api_key_edit, "API Key"),
            (self.auth_domain_edit, "Auth Domain"),
            (self.database_url_edit, "Database URL"),
            (self.project_id_edit, "Project ID"),
        ]

        for field, name in fields:
            if not field.text().strip():
                QMessageBox.warning(self, "Validation Error", f"Please fill in {name}")
                return False

        return True


class PaymentPage(QWizardPage):
    """Payment gateway configuration page"""

    def __init__(self):
        super().__init__()
        self.setTitle("Payment Gateway (Optional)")
        self.setSubTitle("Configure Nedarim Plus payment integration")

        layout = QVBoxLayout()

        # Payment configuration
        payment_group = QGroupBox("Nedarim Plus Configuration")
        payment_layout = QFormLayout()

        self.enable_payment_checkbox = QCheckBox("Enable payment gateway")
        self.enable_payment_checkbox.toggled.connect(self.toggle_payment_fields)
        payment_layout.addRow(self.enable_payment_checkbox)

        self.mosad_id_edit = QLineEdit()
        self.mosad_id_edit.setPlaceholderText("Your Nedarim Mosad ID")
        self.mosad_id_edit.setEnabled(False)
        payment_layout.addRow("Mosad ID:", self.mosad_id_edit)

        self.api_valid_edit = QLineEdit()
        self.api_valid_edit.setPlaceholderText("Your Nedarim API Valid Key")
        self.api_valid_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_valid_edit.setEnabled(False)
        payment_layout.addRow("API Valid Key:", self.api_valid_edit)

        self.callback_url_edit = QLineEdit()
        self.callback_url_edit.setPlaceholderText(
            "https://us-central1-sionyx-19636.cloudfunctions.net/nedarimCallback"
        )
        self.callback_url_edit.setEnabled(False)
        payment_layout.addRow("Callback URL:", self.callback_url_edit)

        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)

        # Help text
        help_label = QLabel(
            """
        <b>Payment Gateway:</b> Optional integration with Nedarim Plus for handling payments<br>
        <b>Callback URL:</b> Pre-configured for SIONYX Firebase Functions<br><br>
        <i>You can skip this step and configure payment later in the application settings.</i>
        """
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(help_label)

        self.setLayout(layout)

        # Register fields
        self.registerField("enable_payment", self.enable_payment_checkbox)
        self.registerField("nedarim_mosad_id", self.mosad_id_edit)
        self.registerField("nedarim_api_valid", self.api_valid_edit)
        self.registerField("nedarim_callback_url", self.callback_url_edit)

    def toggle_payment_fields(self, enabled):
        """Toggle payment field availability"""
        self.mosad_id_edit.setEnabled(enabled)
        self.api_valid_edit.setEnabled(enabled)
        self.callback_url_edit.setEnabled(enabled)

        if enabled:
            # Set default callback URL
            self.callback_url_edit.setText(
                "https://us-central1-sionyx-19636.cloudfunctions.net/nedarimCallback"
            )


class SummaryPage(QWizardPage):
    """Summary and confirmation page"""

    def __init__(self):
        super().__init__()
        self.setTitle("Setup Summary")
        self.setSubTitle("Review your configuration before completing setup")

        layout = QVBoxLayout()

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(300)
        layout.addWidget(self.summary_text)

        # Warning
        warning_label = QLabel(
            """
        <b style="color: #f44336;">⚠️ Important:</b> Make sure all information is correct before proceeding.
        The Organization ID cannot be changed after setup!
        """
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            "background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px;"
        )
        layout.addWidget(warning_label)

        self.setLayout(layout)

    def initializePage(self):
        """Initialize page with summary"""
        # Get all field values
        org_id = self.field("org_id")
        org_name = self.field("org_name")
        firebase_api_key = self.field("firebase_api_key")
        firebase_auth_domain = self.field("firebase_auth_domain")
        firebase_database_url = self.field("firebase_database_url")
        firebase_project_id = self.field("firebase_project_id")
        enable_payment = self.field("enable_payment")
        nedarim_mosad_id = self.field("nedarim_mosad_id")
        nedarim_callback_url = self.field("nedarim_callback_url")

        # Create summary
        summary = f"""
<h3>Configuration Summary</h3>

<h4>Organization</h4>
• <b>ID:</b> {org_id}<br>
• <b>Name:</b> {org_name}<br>

<h4>Firebase</h4>
• <b>Project ID:</b> {firebase_project_id}<br>
• <b>Database URL:</b> {firebase_database_url}<br>
• <b>Auth Domain:</b> {firebase_auth_domain}<br>
• <b>API Key:</b> {firebase_api_key[:10]}...<br>

<h4>Payment Gateway</h4>
"""

        if enable_payment:
            summary += f"""
• <b>Status:</b> Enabled<br>
• <b>Mosad ID:</b> {nedarim_mosad_id}<br>
• <b>Callback URL:</b> {nedarim_callback_url}<br>
"""
        else:
            summary += "• <b>Status:</b> Disabled (can be configured later)<br>"

        summary += f"""
<h4>Next Steps</h4>
After completing setup, you'll need to:
1. Create an admin user account
2. Configure your organization in Firebase
3. Test the application connection

<i>This configuration will be saved to a .env file in the application directory.</i>
"""

        self.summary_text.setHtml(summary)


def create_env_file(config):
    """Create .env file from configuration"""
    env_path = Path(".env")

    # Create backup if exists
    if env_path.exists():
        backup_path = env_path.with_suffix(".env.backup")
        env_path.rename(backup_path)

    # Create .env content
    env_content = f"""# SIONYX Configuration
# Generated by Setup Wizard on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# DO NOT COMMIT THIS FILE TO VERSION CONTROL!

# ============================================================================
# Organization Configuration
# ============================================================================
ORG_ID={config['org_id']}

# ============================================================================
# Firebase Configuration
# ============================================================================
FIREBASE_API_KEY={config['firebase_api_key']}
FIREBASE_AUTH_DOMAIN={config['firebase_auth_domain']}
FIREBASE_DATABASE_URL={config['firebase_database_url']}
FIREBASE_PROJECT_ID={config['firebase_project_id']}

# ============================================================================
# Payment Gateway Configuration (Nedarim Plus)
# ============================================================================
NEDARIM_MOSAD_ID={config.get('nedarim_mosad_id', '')}
NEDARIM_API_VALID={config.get('nedarim_api_valid', '')}
NEDARIM_CALLBACK_URL={config.get('nedarim_callback_url', '')}

# ============================================================================
# Notes:
# - Keep this file secure and never share it publicly
# - Make sure .env is in your .gitignore
# - To change organization, you must reinstall or manually edit this file
# ============================================================================
"""

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    return env_path
