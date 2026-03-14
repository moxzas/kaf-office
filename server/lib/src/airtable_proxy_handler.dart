import 'dart:convert';
import 'dart:io';
import 'package:shelf/shelf.dart';
import 'package:http/http.dart' as http;

/// Allowed tables and methods for the Airtable proxy.
/// Anything not on this list is rejected.
const _allowedTables = {
  'Parents': {'GET', 'POST', 'PATCH'},
  'Students': {'GET', 'POST', 'PATCH', 'DELETE'},
  'Classes': {'GET', 'POST', 'PATCH', 'DELETE'},
  'Bookings': {'GET', 'POST', 'PATCH', 'DELETE'},
  'Venues': {'GET', 'POST', 'PATCH'},
  'Teachers': {'GET'},
  'Sessions': {'GET', 'POST', 'PATCH'},
  'Attendance': {'GET', 'POST', 'PATCH'},
  'Admins': {'GET'},
  'Audit%20Log': {'GET', 'POST'},
  'Audit Log': {'GET', 'POST'},
};

/// Normalise table name for lookup (handle URL-encoded spaces).
String _normaliseTable(String table) {
  return Uri.decodeComponent(table);
}

/// Check if a table + method combination is allowed.
bool _isAllowed(String table, String method) {
  final decoded = _normaliseTable(table);
  final encoded = Uri.encodeComponent(decoded);

  // Check both encoded and decoded forms
  final methods = _allowedTables[decoded] ?? _allowedTables[encoded];
  if (methods == null) return false;
  return methods.contains(method.toUpperCase());
}

/// Proxies requests to Airtable, adding the API key server-side.
///
/// Routes:
///   GET/POST    /api/kaf/db/<table>
///   GET/PATCH/DELETE  /api/kaf/db/<table>/<recordId>
///
/// Query parameters are forwarded as-is (filterByFormula, sort, etc.)
Future<Response> kafAirtableProxyHandler(Request request) async {
  try {
    final airtableApiKey = Platform.environment['AIRTABLE_API_KEY'];
    final airtableBaseId = Platform.environment['AIRTABLE_BASE_ID'];

    if (airtableApiKey == null || airtableBaseId == null) {
      print('ERROR: Missing Airtable credentials');
      return Response.internalServerError(
        body: jsonEncode({'error': 'Server configuration error'}),
        headers: {'Content-Type': 'application/json'},
      );
    }

    // Parse the path: /api/kaf/db/<table>[/<recordId>]
    // shelf_router gives us the path after the mount point
    final segments = request.url.pathSegments;

    if (segments.isEmpty) {
      return Response(400,
        body: jsonEncode({'error': 'Missing table name'}),
        headers: {'Content-Type': 'application/json'},
      );
    }

    final table = segments[0];
    final recordId = segments.length > 1 ? segments[1] : null;
    final method = request.method.toUpperCase();

    // Check allowlist
    if (!_isAllowed(table, method)) {
      print('BLOCKED: $method on table "$table"');
      return Response(403,
        body: jsonEncode({'error': 'Operation not allowed'}),
        headers: {'Content-Type': 'application/json'},
      );
    }

    // Build Airtable URL
    final encodedTable = Uri.encodeComponent(_normaliseTable(table));
    var airtablePath = encodedTable;
    if (recordId != null) {
      airtablePath += '/$recordId';
    }

    var airtableUrl = 'https://api.airtable.com/v0/$airtableBaseId/$airtablePath';

    // Forward query parameters
    if (request.url.query.isNotEmpty) {
      airtableUrl += '?${request.url.query}';
    }

    final uri = Uri.parse(airtableUrl);

    final headers = {
      'Authorization': 'Bearer $airtableApiKey',
      'Content-Type': 'application/json',
    };

    // Forward the request to Airtable
    http.Response airtableResp;

    switch (method) {
      case 'GET':
        airtableResp = await http.get(uri, headers: headers);
        break;
      case 'POST':
        final body = await request.readAsString();
        airtableResp = await http.post(uri, headers: headers, body: body);
        break;
      case 'PATCH':
        final body = await request.readAsString();
        airtableResp = await http.patch(uri, headers: headers, body: body);
        break;
      case 'DELETE':
        airtableResp = await http.delete(uri, headers: headers);
        break;
      default:
        return Response(405,
          body: jsonEncode({'error': 'Method not allowed'}),
          headers: {'Content-Type': 'application/json'},
        );
    }

    // Forward the response back to the client
    return Response(
      airtableResp.statusCode,
      body: airtableResp.body,
      headers: {'Content-Type': 'application/json'},
    );
  } catch (e) {
    print('ERROR: Airtable proxy exception: $e');
    return Response.internalServerError(
      body: jsonEncode({'error': e.toString()}),
      headers: {'Content-Type': 'application/json'},
    );
  }
}
