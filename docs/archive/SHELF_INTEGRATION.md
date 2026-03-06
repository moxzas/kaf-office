# Shelf Server Integration - KAF Files

## Add This Handler to ezeo_otg Server

Create: `/Users/anthonylee/Projects/ezeo_otg/packages/server/lib/handlers/web/kaf_handler.dart`

```dart
import 'dart:io';
import 'package:shelf/shelf.dart';

/// Serves KAF (Kids Art & Craft) enrollment form files
///
/// This handler serves static HTML files from /home/deploy/webremote/kaf/
/// which provides the student enrollment interface.
Future<Response> kafHandler(Request request) async {
  try {
    // Extract the requested file from the path
    // Example: /kaf/enrollment.html -> enrollment.html
    final pathSegments = request.url.pathSegments;
    final fileName = pathSegments.isNotEmpty ? pathSegments.last : 'index.html';

    // Security: Only allow .html files
    if (!fileName.endsWith('.html')) {
      return Response.notFound('Invalid file type');
    }

    // Path to KAF files
    // In development: src/enrollment.html
    // In production: /home/deploy/webremote/kaf/enrollment.html
    final htmlPath = _findKafFile(fileName);

    if (htmlPath == null) {
      return Response.notFound('KAF file not found: $fileName');
    }

    final file = File(htmlPath);
    if (!await file.exists()) {
      return Response.notFound('KAF file not found: $htmlPath');
    }

    final content = await file.readAsString();

    return Response.ok(
      content,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache', // Always serve fresh version
      },
    );
  } catch (e) {
    print('Error serving KAF file: $e');
    return Response.internalServerError(
      body: 'Failed to load KAF file',
    );
  }
}

/// Find KAF HTML files
///
/// Tries multiple locations to support both development and production:
/// 1. /home/deploy/webremote/kaf/{fileName} (production)
/// 2. src/{fileName} (development, from project root)
String? _findKafFile(String fileName) {
  final candidates = [
    '/home/deploy/webremote/kaf/$fileName',
    'src/$fileName',
  ];

  for (final path in candidates) {
    final file = File(path);
    if (file.existsSync()) {
      print('Found KAF file at: $path');
      return path;
    }
  }

  print('KAF file not found. Tried: ${candidates.join(', ')}');
  return null;
}
```

## Update ezeo_otg main.dart

Add to `/Users/anthonylee/Projects/ezeo_otg/packages/server/bin/main.dart`:

### 1. Import the handler (add near top with other imports):

```dart
import 'package:server/handlers/web/kaf_handler.dart';
```

### 2. Add routes (add after line 96, before the root route):

```dart
// KAF enrollment pages (unauthenticated)
..get('/kaf/<fileName>', kafHandler)
..get('/kaf', kafHandler)  // Default to index.html
```

## Complete Routes Section Should Look Like:

```dart
// web pages (unauthenticated)
..get('/remote', webRemoteHandler)
..get('/reset-password', resetPasswordHandler)
..get('/verify-email', verifyEmailHandler)
..get('/kaf/<fileName>', kafHandler)
..get('/kaf', kafHandler)
..get('/', (Request request) {
  return Response.ok('Ezeo OTG Server - Running\n');
});
```

## After Adding the Handler

1. **Test locally** (from ezeo_otg project):
   ```bash
   cd /Users/anthonylee/Projects/ezeo_otg/packages/server
   dart run bin/main.dart
   ```

2. **Visit**: http://localhost:8080/kaf/enrollment.html

3. **Deploy** (push to main branch or manually):
   ```bash
   cd /Users/anthonylee/Projects/ezeo_otg
   git add .
   git commit -m "Add KAF enrollment form handler"
   git push origin main
   ```

4. **Verify production**:
   - Visit: https://app.sonzai.com/kaf/enrollment.html
   - Or: http://209.38.86.222:8080/kaf/enrollment.html

## Alternative: Quick Test Without Code Changes

If you want to test the deployment without modifying the Shelf server first:

```bash
# Deploy KAF files
cd /Users/anthonylee/Projects/KAF-Office
scp src/*.html deploy@209.38.86.222:/home/deploy/webremote/kaf/

# Access directly via file path (if you have nginx/apache)
# OR add a simple symlink in your web root
```

---

## Summary

**To get KAF enrollment form live:**

1. ✅ Created GitHub Actions workflow (`.github/workflows/deploy.yml`)
2. ✅ Created deployment docs (`docs/DEPLOYMENT.md`)
3. ⏳ Add `kaf_handler.dart` to ezeo_otg server (this file)
4. ⏳ Update ezeo_otg routes in `main.dart`
5. ⏳ Deploy both projects:
   - Deploy ezeo_otg (Shelf server with new routes)
   - Deploy KAF-Office (HTML files)

**URLs after deployment:**
- Enrollment form: https://app.sonzai.com/kaf/enrollment.html
- Test form: https://app.sonzai.com/kaf/index.html
