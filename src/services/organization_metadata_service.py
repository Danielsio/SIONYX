"""
Organization Metadata Service
Fetches organization-specific configuration from Firebase database
"""

import base64
import json
from typing import Dict, Optional, Any
from services.firebase_client import FirebaseClient
from utils.logger import get_logger

logger = get_logger(__name__)


class OrganizationMetadataService:
    """Service for fetching organization metadata from database"""

    def __init__(self, firebase_client: FirebaseClient):
        self.firebase = firebase_client

    def decode_data(self, encoded_data: str) -> Optional[str]:
        """Decode base64 encoded data"""
        try:
            decoded_bytes = base64.b64decode(encoded_data)
            return json.loads(decoded_bytes.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error decoding data: {e}")
            return None

    def get_organization_metadata(self, org_id: str) -> Dict[str, Any]:
        """
        Get organization metadata from database
        
        Args:
            org_id: Organization ID
            
        Returns:
            Dict with success status and metadata or error
        """
        try:
            # Fetch metadata from organizations/{orgId}/metadata
            result = self.firebase.db_get("metadata")
            
            if not result['success']:
                logger.error(f"Failed to fetch organization metadata: {result.get('error')}")
                return {
                    'success': False,
                    'error': f"Failed to fetch organization metadata: {result.get('error')}"
                }

            metadata = result.get('data')
            if not metadata:
                return {
                    'success': False,
                    'error': 'Organization metadata not found'
                }

            # Decode sensitive data
            nedarim_mosad_id = self.decode_data(metadata.get('nedarim_mosad_id', ''))
            nedarim_api_valid = self.decode_data(metadata.get('nedarim_api_valid', ''))

            if not nedarim_mosad_id or not nedarim_api_valid:
                return {
                    'success': False,
                    'error': 'NEDARIM credentials not found in organization metadata'
                }

            return {
                'success': True,
                'metadata': {
                    'name': metadata.get('name', ''),
                    'nedarim_mosad_id': nedarim_mosad_id,
                    'nedarim_api_valid': nedarim_api_valid,
                    'created_at': metadata.get('created_at', ''),
                    'status': metadata.get('status', 'active')
                }
            }

        except Exception as e:
            logger.error(f"Error getting organization metadata: {e}")
            return {
                'success': False,
                'error': f"Error getting organization metadata: {str(e)}"
            }

    def get_nedarim_credentials(self, org_id: str) -> Dict[str, Any]:
        """
        Get NEDARIM credentials for the organization
        
        Args:
            org_id: Organization ID
            
        Returns:
            Dict with success status and credentials or error
        """
        metadata_result = self.get_organization_metadata(org_id)
        
        if not metadata_result['success']:
            return metadata_result

        metadata = metadata_result['metadata']
        
        return {
            'success': True,
            'credentials': {
                'mosad_id': metadata['nedarim_mosad_id'],
                'api_valid': metadata['nedarim_api_valid']
            }
        }
