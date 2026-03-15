import 'dart:convert';
import 'dart:io';
import 'package:shelf/shelf.dart';
import 'package:http/http.dart' as http;
import 'package:crypto/crypto.dart';

/// Session cookie name.
const _cookieName = 'kaf_session';

/// Session duration: 24 hours.
const _sessionDuration = Duration(hours: 24);

/// HMAC secret derived from AIRTABLE_API_KEY.
String get _secret =>
    Platform.environment['AIRTABLE_API_KEY'] ?? 'kaf-fallback-secret';

/// Sign a session value: name|expiry -> hex HMAC.
String _sign(String payload) {
  final hmac = Hmac(sha256, utf8.encode(_secret));
  return hmac.convert(utf8.encode(payload)).toString();
}

/// Build a signed session cookie value.
String _buildCookie(String adminName) {
  final expiry =
      DateTime.now().add(_sessionDuration).millisecondsSinceEpoch ~/ 1000;
  final payload = '$adminName|$expiry';
  final sig = _sign(payload);
  return '$payload|$sig';
}

/// Validate a session cookie. Returns the admin name or null.
String? validateKafSession(Request request) {
  final cookieHeader = request.headers['cookie'];
  if (cookieHeader == null) return null;

  // Parse cookies
  for (final part in cookieHeader.split(';')) {
    final trimmed = part.trim();
    if (!trimmed.startsWith('$_cookieName=')) continue;
    final value = trimmed.substring(_cookieName.length + 1);

    // Format: name|expiry|signature
    final segments = value.split('|');
    if (segments.length != 3) return null;

    final name = Uri.decodeComponent(segments[0]);
    final expiryStr = segments[1];
    final sig = segments[2];

    // Verify signature
    final payload = '${segments[0]}|$expiryStr';
    if (_sign(payload) != sig) return null;

    // Check expiry
    final expiry = int.tryParse(expiryStr);
    if (expiry == null) return null;
    final expiryTime = DateTime.fromMillisecondsSinceEpoch(expiry * 1000);
    if (DateTime.now().isAfter(expiryTime)) return null;

    return name;
  }
  return null;
}

/// POST /api/kaf/auth/login
/// Body: {"pin": "212455"}
/// Sets a signed session cookie on success.
Future<Response> kafAuthLoginHandler(Request request) async {
  try {
    final body = await request.readAsString();
    final data = jsonDecode(body) as Map<String, dynamic>;
    final pin = data['pin'] as String?;

    if (pin == null || pin.isEmpty) {
      return Response(400,
          body: jsonEncode({'error': 'PIN required'}),
          headers: {'Content-Type': 'application/json'});
    }

    // Validate against Admins table
    final airtableApiKey = Platform.environment['AIRTABLE_API_KEY'];
    final airtableBaseId = Platform.environment['AIRTABLE_BASE_ID'];

    if (airtableApiKey == null || airtableBaseId == null) {
      return Response.internalServerError(
          body: jsonEncode({'error': 'Server configuration error'}),
          headers: {'Content-Type': 'application/json'});
    }

    final url = Uri.parse(
        'https://api.airtable.com/v0/$airtableBaseId/Admins?filterByFormula=AND(Active%3DTRUE())');
    final resp = await http.get(url,
        headers: {'Authorization': 'Bearer $airtableApiKey'});

    if (resp.statusCode != 200) {
      return Response.internalServerError(
          body: jsonEncode({'error': 'Failed to verify PIN'}),
          headers: {'Content-Type': 'application/json'});
    }

    final records = jsonDecode(resp.body)['records'] as List;
    final match = records.cast<Map<String, dynamic>>().firstWhere(
        (r) => (r['fields'] as Map<String, dynamic>)['PIN'] == pin,
        orElse: () => <String, dynamic>{});

    if (match.isEmpty) {
      return Response(401,
          body: jsonEncode({'error': 'Incorrect PIN'}),
          headers: {'Content-Type': 'application/json'});
    }

    final adminName = (match['fields'] as Map<String, dynamic>)['Name'] as String;
    final encodedName = Uri.encodeComponent(adminName);
    final cookieValue = _buildCookie(encodedName);

    return Response.ok(
      jsonEncode({'ok': true, 'name': adminName}),
      headers: {
        'Content-Type': 'application/json',
        'Set-Cookie':
            '$_cookieName=$cookieValue; Path=/; HttpOnly; SameSite=Strict; Max-Age=${_sessionDuration.inSeconds}',
      },
    );
  } catch (e) {
    print('KAF auth error: $e');
    return Response.internalServerError(
        body: jsonEncode({'error': 'Auth error'}),
        headers: {'Content-Type': 'application/json'});
  }
}

/// POST /api/kaf/auth/logout
/// Clears the session cookie.
Future<Response> kafAuthLogoutHandler(Request request) async {
  return Response.ok(
    jsonEncode({'ok': true}),
    headers: {
      'Content-Type': 'application/json',
      'Set-Cookie':
          '$_cookieName=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0',
    },
  );
}

/// HTML login page served when an unauthenticated user hits an admin page.
String kafLoginPageHtml(String redirectPath) {
  final escapedPath = htmlEscape(redirectPath);
  return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KAF - Admin Login</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            min-height: 100vh;
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            color: white;
            -webkit-user-select: none; user-select: none;
        }
        .login-title { font-size: 28px; font-weight: 700; margin-bottom: 8px; }
        .login-subtitle { font-size: 16px; opacity: 0.8; margin-bottom: 40px; }
        .pin-display { display: flex; gap: 12px; margin-bottom: 30px; }
        .pin-dot {
            width: 18px; height: 18px; border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.6);
            background: transparent; transition: background 0.15s;
        }
        .pin-dot.filled { background: white; border-color: white; }
        .pin-pad { display: grid; grid-template-columns: repeat(3, 80px); gap: 12px; }
        .pin-btn {
            width: 80px; height: 80px; border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.4);
            background: rgba(255,255,255,0.1);
            color: white; font-size: 28px; font-weight: 500;
            cursor: pointer; display: flex; align-items: center; justify-content: center;
            -webkit-tap-highlight-color: transparent;
        }
        .pin-btn:active { background: rgba(255,255,255,0.3); }
        .pin-btn.fn { font-size: 14px; border-color: transparent; background: transparent; }
        .pin-error { color: #fca5a5; font-size: 14px; margin-top: 16px; min-height: 20px; }
    </style>
</head>
<body>
    <img src="/kaf/logo.png" alt="Kids Art Fun" style="width:120px;height:120px;margin-bottom:16px;border-radius:50%;">
    <div class="login-subtitle">Admin Login</div>
    <div class="pin-display">
        <div class="pin-dot" id="dot0"></div>
        <div class="pin-dot" id="dot1"></div>
        <div class="pin-dot" id="dot2"></div>
        <div class="pin-dot" id="dot3"></div>
        <div class="pin-dot" id="dot4"></div>
        <div class="pin-dot" id="dot5"></div>
    </div>
    <div class="pin-pad">
        <button class="pin-btn" onclick="pinPress('1')">1</button>
        <button class="pin-btn" onclick="pinPress('2')">2</button>
        <button class="pin-btn" onclick="pinPress('3')">3</button>
        <button class="pin-btn" onclick="pinPress('4')">4</button>
        <button class="pin-btn" onclick="pinPress('5')">5</button>
        <button class="pin-btn" onclick="pinPress('6')">6</button>
        <button class="pin-btn" onclick="pinPress('7')">7</button>
        <button class="pin-btn" onclick="pinPress('8')">8</button>
        <button class="pin-btn" onclick="pinPress('9')">9</button>
        <button class="pin-btn fn"></button>
        <button class="pin-btn" onclick="pinPress('0')">0</button>
        <button class="pin-btn fn" onclick="pinDelete()">Del</button>
    </div>
    <div class="pin-error" id="pinError"></div>
    <script>
        let pin = '';
        function pinPress(d) {
            if (pin.length >= 6) return;
            pin += d;
            updateDots();
            if (pin.length === 6) setTimeout(submit, 150);
        }
        function pinDelete() {
            pin = pin.slice(0, -1);
            updateDots();
            document.getElementById('pinError').textContent = '';
        }
        function updateDots() {
            for (let i = 0; i < 6; i++)
                document.getElementById('dot' + i).classList.toggle('filled', i < pin.length);
        }
        async function submit() {
            try {
                const r = await fetch('/api/kaf/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({pin})
                });
                if (r.ok) {
                    window.location.href = '$escapedPath';
                } else {
                    document.getElementById('pinError').textContent = 'Incorrect PIN';
                    pin = '';
                    updateDots();
                }
            } catch(e) {
                document.getElementById('pinError').textContent = 'Connection error';
                pin = '';
                updateDots();
            }
        }
    </script>
</body>
</html>''';
}

/// Escape HTML entities.
String htmlEscape(String s) =>
    s.replaceAll('&', '&amp;').replaceAll('<', '&lt;')
     .replaceAll('>', '&gt;').replaceAll('"', '&quot;')
     .replaceAll("'", '&#39;');
