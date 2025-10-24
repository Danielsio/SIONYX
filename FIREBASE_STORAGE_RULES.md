# Firebase Storage Rules for SIONYX

## Simple Production Rules

Update your Firebase Storage rules to:

```javascript
rules_version = '2';

service firebase.storage {
  match /b/{bucket}/o {
    // Public read access for the main installer file
    match /sionyx-installer.exe {
      allow read: if true;
      allow write: if false; // Only admin can write via service account
    }
    
    // Public read access for any other files you might need
    match /{allPaths=**} {
      allow read: if true;
      allow write: if false; // Only admin can write via service account
    }
  }
}
```

## How to Update Rules

1. Go to https://console.firebase.google.com/
2. Select your project (sionyx-19636)
3. Go to **Storage** → **Rules**
4. Replace the existing rules with the above
5. Click **Publish**

## Benefits

- ✅ **Simple**: File at root level, no folder complexity
- ✅ **Reliable**: Constant URL that never changes
- ✅ **Fast**: Direct access, no folder traversal
- ✅ **Production-ready**: Minimal failure points
- ✅ **Easy to debug**: Clear path structure

## File Structure

```
Firebase Storage Bucket:
├── sionyx-installer.exe  ← Main installer (always latest version)
└── (other files as needed)
```

## Download URL

The download URL will always be:
```
https://firebasestorage.googleapis.com/v0/b/sionyx-19636.firebasestorage.app/o/sionyx-installer.exe?alt=media
```

## Web App Configuration

Add to your web app's `.env` file:
```
VITE_INSTALLER_DOWNLOAD_URL=https://firebasestorage.googleapis.com/v0/b/sionyx-19636.firebasestorage.app/o/sionyx-installer.exe?alt=media
```

## Performance Optimizations

The web app has been optimized for better performance:
- ✅ React.memo for component memoization
- ✅ useCallback for function memoization
- ✅ useMemo for value memoization
- ✅ Reduced re-renders
- ✅ Optimized download service
- ✅ Direct environment variable usage
