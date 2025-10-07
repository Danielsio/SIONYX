# Modern Dialog System - Usage Guide

## Overview

Your app now has **beautiful, modern dialogs** with smooth animations and excellent UX! 🎉

All dialogs automatically:
- ✅ Fade in/out smoothly
- ✅ Have modern, gradient styling  
- ✅ Support keyboard shortcuts (Enter, Escape)
- ✅ Auto-focus primary action
- ✅ Look consistent across the app

---

## How to Use

### In Any Window (BaseKioskWindow)

All your windows inherit these helper methods:

```python
# Show error
self.show_error("Error Title", "Something went wrong")

# Show success
self.show_success("Success!", "Operation completed")

# Show warning
self.show_warning("Warning", "Please be careful")

# Show information
self.show_info("Info", "Here's some information")

# Ask a question (returns True/False)
if self.show_question("Delete?", "Are you sure?"):
    # User clicked Yes
    pass

# Confirmation dialog (returns True/False)
if self.show_confirm("Logout", "Are you sure?", danger=True):
    # User confirmed
    pass

# Quick notification toast (auto-dismisses)
self.show_notification("Saved successfully!", "success", duration=3000)
```

---

## Dialog Types

### 1. Information Dialog
```python
self.show_info(
    "Welcome",
    "Welcome to SIONYX!",
    "You have 60 minutes remaining"  # optional detailed text
)
```

**Appearance:**
- Blue icon (ℹ️)
- Single OK button
- Professional blue gradient

---

### 2. Success Dialog  
```python
self.show_success(
    "Purchase Complete! 🎉",
    "Your purchase was successful!",
    "Added: 60 minutes + 10 prints"
)
```

**Appearance:**
- Green checkmark (✅)
- Single OK button
- Success green gradient

---

### 3. Warning Dialog
```python
self.show_warning(
    "Low Balance",
    "You're running low on time",
    "Consider purchasing more"
)
```

**Appearance:**
- Orange warning icon (⚠️)
- Single OK button
- Warning orange gradient

---

### 4. Error Dialog
```python
self.show_error(
    "Connection Failed",
    "Could not connect to server",
    "Please check your internet connection"
)
```

**Appearance:**
- Red X icon (❌)
- Single OK button
- Error red gradient

---

### 5. Question Dialog
```python
# Returns True if user clicks "Yes"
purchase_more = self.show_question(
    "Time Expired",
    "Your session has ended",
    "Would you like to purchase more time?",
    yes_text="Buy More",
    no_text="Not Now"
)

if purchase_more:
    # Show packages page
    pass
```

**Appearance:**
- Purple question mark (❓)
- Two buttons (customizable text)
- Returns boolean

---

### 6. Confirmation Dialog
```python
# Returns True if user confirms
confirmed = self.show_confirm(
    "Confirm Logout",
    "Are you sure you want to logout?",
    confirm_text="Yes, Logout",
    cancel_text="Cancel",
    danger=False  # Set True for destructive actions
)

if confirmed:
    # Logout
    pass
```

**Appearance:**
- Question or Warning icon (depends on danger flag)
- Two buttons with custom text
- Danger mode = orange warning style

---

### 7. Notification Toast
```python
# Auto-dismissing notification (no user interaction needed)
self.show_notification(
    "Settings saved!",
    message_type="success",  # info, success, warning, error
    duration=3000  # milliseconds
)
```

**Appearance:**
- Small toast at top-right
- Auto-dismisses after duration
- Fades in and out smoothly
- Doesn't block user

---

## Keyboard Shortcuts

All dialogs support:
- **Enter/Return**: Confirms (clicks primary button)
- **Escape**: Cancels (clicks secondary button or closes)

---

## Examples from Your App

### Logout Confirmation
```python
# Before (old boring style):
reply = QMessageBox.question(
    self, "Confirm", "Are you sure?",
    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
)
if reply == QMessageBox.StandardButton.Yes:
    self.logout()

# After (modern beautiful style):
if self.show_confirm("Confirm Logout", "Are you sure you want to logout?"):
    self.logout()
```

### Time Expiration
```python
# Before:
msg = QMessageBox(self)
msg.setIcon(QMessageBox.Icon.Warning)
msg.setWindowTitle("Time Expired")
msg.setText("Your time has expired!")
# ... lots of setup code ...

# After:
if self.show_question(
    "Time Expired",
    "Your session has expired!",
    "Would you like to purchase more time?",
    yes_text="Buy More",
    no_text="Not Now"
):
    self.show_packages()
```

### Purchase Success
```python
# Before:
QMessageBox.information(self, "Success", "Purchase complete!")

# After:
self.show_success(
    "Purchase Complete! 🎉",
    "Your purchase was successful!",
    f"Added: {minutes} minutes + {prints} prints"
)
```

### Quick Notifications
```python
# For non-blocking quick feedback:
self.show_notification("⏰ 5 minutes remaining!", "warning", 4000)
self.show_notification("🚨 URGENT: 1 minute left!", "error", 6000)
self.show_notification("✅ Settings saved!", "success", 3000)
```

---

## Advanced: Direct Usage

If you need more control, you can use the dialog classes directly:

```python
from ui.modern_dialogs import ModernMessageBox, ModernConfirmDialog, ModernNotification

# Custom message box
dialog = ModernMessageBox(
    parent=self,
    message_type=ModernMessageBox.SUCCESS,
    title="Custom Title",
    message="Custom message",
    detailed_text="Optional details",
    buttons=["OK", "Cancel", "More Info"]
)
dialog.show_animated()
result = dialog.exec()
clicked_button = dialog.get_result()  # "OK", "Cancel", or "More Info"

# Custom notification
notification = ModernNotification(
    parent=self,
    message="Custom notification",
    message_type="info",
    duration=5000
)
notification.show_notification()
```

---

## Styling

All dialogs use:
- **Modern gradient backgrounds**
- **Smooth fade animations** (200ms in, 150ms out)
- **Rounded corners** (20px container, 22px buttons)
- **Emoji icons** for visual communication
- **Color-coded by type** (blue, green, orange, red, purple)
- **Hover effects** on buttons
- **Focus states** for accessibility
- **Responsive sizing**

---

## Best Practices

### ✅ DO

```python
# Use clear, actionable titles
self.show_confirm("Confirm Logout", "...")

# Provide helpful details
self.show_error("Connection Failed", "...", "Check your internet")

# Use appropriate types
self.show_success("Purchase Complete!", "...")  # positive action
self.show_error("Payment Failed", "...")  # problem
self.show_warning("Low Balance", "...")  # caution
self.show_info("How to use", "...")  # neutral info

# Use notifications for non-critical feedback
self.show_notification("Saved!", "success")
```

### ❌ DON'T

```python
# Don't use vague titles
self.show_error("Error", "An error occurred")

# Don't overuse dialogs
# (use notifications for quick feedback instead)

# Don't nest dialogs
# (finish one before showing another)

# Don't use the wrong type
self.show_success("Error", "Something failed")  # confusing!
```

---

## Migration Checklist

All old QMessageBox calls have been updated to use modern dialogs:

- ✅ Login window - forgot password
- ✅ Main window - logout confirmation
- ✅ Main window - session expired
- ✅ Main window - time warnings (now notifications)
- ✅ Packages page - purchase success/error
- ✅ Base window - error/success helpers
- ✅ Admin exit - access denied

---

## Summary

Your app now has **world-class UI/UX** for all dialogs! 🚀

**Features:**
- Modern, beautiful design
- Smooth animations
- Consistent styling
- Great accessibility
- Easy to use
- Professional appearance

**Result:**
- Better user experience
- More polished app
- Easier maintenance
- Consistent look & feel

Enjoy your beautiful dialogs! 🎉

