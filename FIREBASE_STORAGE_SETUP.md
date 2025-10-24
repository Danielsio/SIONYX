# Firebase Storage Setup for SIONYX

This guide explains how to set up Firebase Storage for automatic uploads of your built executables.

## Overview

The build system can automatically upload your built executables to Firebase Storage, making them available for download through the web interface.

## Prerequisites

1. **Firebase Project** - You need a Firebase project with Storage enabled
2. **Service Account Key** - Download the service account JSON file
3. **Firebase Admin SDK** - Install the Python package

## Setup Steps

### 1. Enable Firebase Storage

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Storage** in the left sidebar
4. Click **Get Started**
5. Choose **Start in test mode** (for now)
6. Select a location for your storage bucket

### 2. Create Service Account

1. Go to **Project Settings** → **Service Accounts**
2. Click **Generate New Private Key**
3. Download the JSON file
4. Rename it to `serviceAccountKey.json`
5. Place it in your SIONYX project root directory

### 3. Install Firebase Admin SDK

```bash
pip install firebase-admin
```

### 4. Configure Storage Rules

Update your Firebase Storage rules to allow public read access:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /releases/{allPaths=**} {
      allow read: if true;  // Public read access for releases
      allow write: if false; // Only admin can write
    }
  }
}
```

## Usage

### Basic Upload

```bash
# Build and upload executable
build.bat --upload

# Build and upload both executable and installer
build.bat --upload --upload-installer
```

### Custom Bucket

```bash
# Use a different bucket
build.bat --upload --bucket my-custom-bucket
```

### Upload Only (if already built)

```bash
# Upload existing executable
python -c "
from build import upload_to_firebase_storage
upload_to_firebase_storage('dist/SIONYX.exe', 'sionyx-19636')
"
```

## File Organization

Uploaded files are organized as:

```
releases/
├── SIONYX_20241201_143022.exe          # Executable with timestamp
├── SIONYX-Setup-1.0.0.exe              # Installer
└── SIONYX_20241201_143022.exe_old      # Previous version
```

## Download URLs

After upload, you'll get:

- **Public URL** - Direct download link
- **Upload Info** - Saved to `upload_info.json`

Example `upload_info.json`:
```json
{
  "file_name": "SIONYX.exe",
  "file_size": 45678912,
  "upload_time": "2024-12-01T14:30:22.123456",
  "download_url": "https://firebasestorage.googleapis.com/v0/b/sionyx-19636.appspot.com/o/releases%2FSIONYX_20241201_143022.exe?alt=media",
  "destination_path": "releases/SIONYX_20241201_143022.exe"
}
```

## Integration with Web App

### 1. Add Download Service

Create `sionyx-web/src/services/downloadService.js`:

```javascript
import { getStorage, ref, getDownloadURL } from 'firebase/storage';

const storage = getStorage();

export const getLatestRelease = async () => {
  try {
    // Get the latest release info from your database
    const response = await fetch('/api/latest-release');
    const releaseInfo = await response.json();
    
    return {
      downloadUrl: releaseInfo.download_url,
      version: releaseInfo.version,
      releaseDate: releaseInfo.upload_time
    };
  } catch (error) {
    console.error('Failed to get latest release:', error);
    throw error;
  }
};

export const downloadFile = async (url, filename) => {
  try {
    const response = await fetch(url);
    const blob = await response.blob();
    
    // Create download link
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
};
```

### 2. Add Download Component

Create `sionyx-web/src/components/DownloadButton.jsx`:

```jsx
import React, { useState, useEffect } from 'react';
import { Button, Spin, message } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { getLatestRelease, downloadFile } from '../services/downloadService';

const DownloadButton = () => {
  const [loading, setLoading] = useState(false);
  const [releaseInfo, setReleaseInfo] = useState(null);

  useEffect(() => {
    // Load release info on component mount
    loadReleaseInfo();
  }, []);

  const loadReleaseInfo = async () => {
    try {
      const info = await getLatestRelease();
      setReleaseInfo(info);
    } catch (error) {
      console.error('Failed to load release info:', error);
    }
  };

  const handleDownload = async () => {
    if (!releaseInfo) return;

    setLoading(true);
    try {
      await downloadFile(releaseInfo.downloadUrl, 'SIONYX-Setup.exe');
      message.success('Download started!');
    } catch (error) {
      message.error('Download failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!releaseInfo) {
    return <Spin size="small" />;
  }

  return (
    <Button
      type="primary"
      icon={<DownloadOutlined />}
      loading={loading}
      onClick={handleDownload}
      size="large"
    >
      Download SIONYX {releaseInfo.version}
    </Button>
  );
};

export default DownloadButton;
```

### 3. Add to Your Pages

```jsx
import DownloadButton from '../components/DownloadButton';

// In your component
<DownloadButton />
```

## Security Considerations

1. **Service Account Key** - Keep `serviceAccountKey.json` secure
2. **Storage Rules** - Only allow public read for releases folder
3. **Access Control** - Consider adding authentication for downloads
4. **File Validation** - Validate uploaded files before making them public

## Troubleshooting

### Common Issues

**"Firebase Admin SDK not installed"**
```bash
pip install firebase-admin
```

**"Service account key not found"**
- Ensure `serviceAccountKey.json` is in the project root
- Check the file name is exactly correct

**"Permission denied"**
- Check Firebase Storage rules
- Ensure service account has Storage Admin role

**"Upload failed"**
- Check internet connection
- Verify bucket name is correct
- Check Firebase project permissions

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Automation

### GitHub Actions (Optional)

Create `.github/workflows/build-and-upload.yml`:

```yaml
name: Build and Upload

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-upload:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r build-requirements.txt
        npm install -g npm
    
    - name: Build and upload
      run: |
        python build.py --upload --upload-installer
      env:
        GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
```

## File Structure

```
SIONYX/
├── serviceAccountKey.json          # Firebase service account (DO NOT COMMIT)
├── upload_info.json               # Generated after upload
├── build.py                       # Build script with upload
├── sionyx-web/
│   └── src/
│       ├── services/
│       │   └── downloadService.js  # Download service
│       └── components/
│           └── DownloadButton.jsx  # Download component
└── FIREBASE_STORAGE_SETUP.md      # This file
```

## Next Steps

1. Set up Firebase Storage in your project
2. Download and place the service account key
3. Test the upload functionality
4. Integrate download functionality in your web app
5. Set up automated builds (optional)

Your users will now be able to download the latest SIONYX executable directly from your web interface! 🎉
