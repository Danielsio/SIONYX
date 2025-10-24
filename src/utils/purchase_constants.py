"""
Purchase Status Constants
Unified constants for purchase status values across the application
Database stores English values, UI displays Hebrew labels
"""

# Database values (English) - used in Firebase and all services
PURCHASE_STATUS = {"PENDING": "pending", "COMPLETED": "completed", "FAILED": "failed"}

# Display labels (Hebrew) - used in UI
PURCHASE_STATUS_LABELS = {
    PURCHASE_STATUS["PENDING"]: "ממתין",
    PURCHASE_STATUS["COMPLETED"]: "הושלם",
    PURCHASE_STATUS["FAILED"]: "נכשל",
}

# Status colors for UI components
PURCHASE_STATUS_COLORS = {
    PURCHASE_STATUS["PENDING"]: "processing",
    PURCHASE_STATUS["COMPLETED"]: "success",
    PURCHASE_STATUS["FAILED"]: "error",
}


def get_status_label(status):
    """Get Hebrew label for status"""
    return PURCHASE_STATUS_LABELS.get(status, status)


def get_status_color(status):
    """Get color for status"""
    return PURCHASE_STATUS_COLORS.get(status, "default")


def is_final_status(status):
    """Check if status is final (completed or failed)"""
    return status in [PURCHASE_STATUS["COMPLETED"], PURCHASE_STATUS["FAILED"]]


def get_status_from_nedarim(nedarim_status):
    """Get the appropriate status value based on Nedarim response"""
    return (
        PURCHASE_STATUS["FAILED"]
        if nedarim_status == "Error"
        else PURCHASE_STATUS["COMPLETED"]
    )
