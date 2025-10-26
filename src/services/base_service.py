"""
Base Service Class - Common functionality for all services.

This module provides a base class that eliminates code duplication
across all service classes and provides consistent error handling,
logging, and response formatting.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.services.firebase_client import FirebaseClient
from src.utils.logger import get_logger


logger = get_logger(__name__)


class BaseService(ABC):
    """Base service class with common functionality"""

    def __init__(self, firebase_client: FirebaseClient):
        self.firebase = firebase_client
        self.logger = get_logger(self.__class__.__name__)

    def create_success_response(
        self, data: Any = None, message: str = "Success"
    ) -> Dict[str, Any]:
        """Create standardized success response"""
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

    def create_error_response(
        self, error: str, error_code: str = None
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        response = {
            "success": False,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

        if error_code:
            response["error_code"] = error_code

        return response

    def handle_firebase_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Handle Firebase errors consistently"""
        error_msg = str(error)
        self.logger.error(f"Firebase error during {operation}: {error_msg}")

        # Map common Firebase errors to user-friendly messages
        if "permission-denied" in error_msg.lower():
            return self.create_error_response(
                "אין הרשאה לבצע פעולה זו", "PERMISSION_DENIED"
            )
        elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
            return self.create_error_response(
                "שגיאת רשת - נסה שוב מאוחר יותר", "NETWORK_ERROR"
            )
        elif "not-found" in error_msg.lower():
            return self.create_error_response("הנתונים לא נמצאו", "NOT_FOUND")
        else:
            return self.create_error_response(
                f"שגיאה ב{operation}: {error_msg}", "UNKNOWN_ERROR"
            )

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> Optional[str]:
        """Validate that all required fields are present in data"""
        missing_fields = [
            field
            for field in required_fields
            if field not in data or data[field] is None
        ]

        if missing_fields:
            return f"שדות חסרים: {', '.join(missing_fields)}"

        return None

    def safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely get value from dictionary with default"""
        return data.get(key, default)

    def safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to integer"""
        if value is None:
            return default

        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            self.logger.warning(
                f"Could not convert '{value}' to int, using default {default}"
            )
            return default

    def safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float"""
        if value is None:
            return default

        try:
            return float(str(value))
        except (ValueError, TypeError):
            self.logger.warning(
                f"Could not convert '{value}' to float, using default {default}"
            )
            return default

    def format_timestamp(self, timestamp: Optional[str] = None) -> str:
        """Format timestamp for consistent use across services"""
        if timestamp:
            return timestamp
        return datetime.now().isoformat()

    def is_authenticated(self) -> bool:
        """Check if Firebase client is authenticated"""
        return bool(self.firebase.id_token)

    def require_authentication(self) -> Optional[Dict[str, Any]]:
        """Check authentication and return error if not authenticated"""
        if not self.is_authenticated():
            return self.create_error_response(
                "נדרשת התחברות", "AUTHENTICATION_REQUIRED"
            )
        return None

    def log_operation(self, operation: str, details: str = ""):
        """Log service operation with consistent format"""
        self.logger.info(f"{operation}: {details}")

    def log_error(self, operation: str, error: str):
        """Log service error with consistent format"""
        self.logger.error(f"{operation} failed: {error}")

    @abstractmethod
    def get_service_name(self) -> str:
        """Return the name of the service for logging purposes"""


class DatabaseService(BaseService):
    """Base service for database operations"""

    def __init__(self, firebase_client: FirebaseClient):
        super().__init__(firebase_client)
        self.collection_name = self.get_collection_name()

    @abstractmethod
    def get_collection_name(self) -> str:
        """Return the collection name for this service"""

    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Get a single document by ID"""
        self.log_operation("get_document", f"ID: {doc_id}")

        auth_error = self.require_authentication()
        if auth_error:
            return auth_error

        try:
            result = self.firebase.db_get(f"{self.collection_name}/{doc_id}")

            if result.get("success"):
                return self.create_success_response(result.get("data"))
            else:
                return self.create_error_response(result.get("error", "Unknown error"))

        except Exception as e:
            return self.handle_firebase_error(e, f"get document {doc_id}")

    def get_all_documents(self) -> Dict[str, Any]:
        """Get all documents in collection"""
        self.log_operation("get_all_documents", f"Collection: {self.collection_name}")

        auth_error = self.require_authentication()
        if auth_error:
            return auth_error

        try:
            result = self.firebase.db_get(self.collection_name)

            if result.get("success"):
                data = result.get("data", {})
                # Convert Firebase dict to list with IDs
                documents = []
                for doc_id, doc_data in data.items():
                    doc_data["id"] = doc_id
                    documents.append(doc_data)

                return self.create_success_response(documents)
            else:
                return self.create_error_response(result.get("error", "Unknown error"))

        except Exception as e:
            return self.handle_firebase_error(
                e, f"get all documents from {self.collection_name}"
            )

    def create_document(
        self, data: Dict[str, Any], doc_id: str = None
    ) -> Dict[str, Any]:
        """Create a new document"""
        self.log_operation("create_document", f"Collection: {self.collection_name}")

        auth_error = self.require_authentication()
        if auth_error:
            return auth_error

        try:
            # Add timestamp
            data["createdAt"] = self.format_timestamp()
            data["updatedAt"] = self.format_timestamp()

            if doc_id:
                path = f"{self.collection_name}/{doc_id}"
                result = self.firebase.db_set(path, data)
            else:
                path = f"{self.collection_name}"
                result = self.firebase.db_push(path, data)

            if result.get("success"):
                created_id = result.get("name") if not doc_id else doc_id
                return self.create_success_response({"id": created_id, "data": data})
            else:
                return self.create_error_response(result.get("error", "Unknown error"))

        except Exception as e:
            return self.handle_firebase_error(
                e, f"create document in {self.collection_name}"
            )

    def update_document(self, doc_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing document"""
        self.log_operation("update_document", f"ID: {doc_id}")

        auth_error = self.require_authentication()
        if auth_error:
            return auth_error

        try:
            # Add update timestamp
            updates["updatedAt"] = self.format_timestamp()

            result = self.firebase.db_update(
                f"{self.collection_name}/{doc_id}", updates
            )

            if result.get("success"):
                return self.create_success_response({"id": doc_id, "updates": updates})
            else:
                return self.create_error_response(result.get("error", "Unknown error"))

        except Exception as e:
            return self.handle_firebase_error(e, f"update document {doc_id}")

    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete a document"""
        self.log_operation("delete_document", f"ID: {doc_id}")

        auth_error = self.require_authentication()
        if auth_error:
            return auth_error

        try:
            result = self.firebase.db_delete(f"{self.collection_name}/{doc_id}")

            if result.get("success"):
                return self.create_success_response({"id": doc_id})
            else:
                return self.create_error_response(result.get("error", "Unknown error"))

        except Exception as e:
            return self.handle_firebase_error(e, f"delete document {doc_id}")

    def query_documents(self, field: str, value: Any) -> Dict[str, Any]:
        """Query documents by field value"""
        self.log_operation("query_documents", f"Field: {field}, Value: {value}")

        auth_error = self.require_authentication()
        if auth_error:
            return auth_error

        try:
            # Get all documents and filter
            result = self.get_all_documents()

            if not result.get("success"):
                return result

            documents = result.get("data", [])
            filtered = [doc for doc in documents if doc.get(field) == value]

            return self.create_success_response(filtered)

        except Exception as e:
            return self.handle_firebase_error(e, f"query documents by {field}")

    def get_service_name(self) -> str:
        """Return service name for logging"""
        return f"{self.__class__.__name__} ({self.collection_name})"
