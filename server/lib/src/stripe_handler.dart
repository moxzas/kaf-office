import 'dart:convert';
import 'dart:io';
import 'package:shelf/shelf.dart';
import 'package:http/http.dart' as http;
import 'package:crypto/crypto.dart';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/// Makes an authenticated request to the Stripe API.
///
/// [method] — HTTP method (GET, POST, etc.)
/// [path]   — path after `https://api.stripe.com` (e.g. `/v1/checkout/sessions`)
/// [params] — form-encoded body params (POST only)
Future<http.Response> _stripeRequest(
  String method,
  String path, {
  Map<String, String>? params,
}) async {
  final stripeKey = Platform.environment['KAF_STRIPE_SECRET_KEY']!;
  final uri = Uri.parse('https://api.stripe.com$path');
  final headers = {
    'Authorization': 'Bearer $stripeKey',
  };

  switch (method.toUpperCase()) {
    case 'GET':
      return http.get(uri, headers: headers);
    case 'POST':
      // Stripe expects application/x-www-form-urlencoded
      return http.post(uri, headers: headers, body: params ?? {});
    default:
      throw ArgumentError('Unsupported Stripe HTTP method: $method');
  }
}

/// Makes an authenticated request to the Airtable API.
///
/// [method] — HTTP method
/// [table]  — table name (URL-encoded if needed)
/// [body]   — JSON string body (for POST/PATCH)
/// [query]  — optional query string (filterByFormula, etc.)
Future<http.Response> _airtableRequest(
  String method,
  String table, {
  String? body,
  String? query,
}) async {
  final apiKey = Platform.environment['AIRTABLE_API_KEY']!;
  final baseId = Platform.environment['AIRTABLE_BASE_ID']!;
  final encodedTable = Uri.encodeComponent(table);
  var url = 'https://api.airtable.com/v0/$baseId/$encodedTable';
  if (query != null && query.isNotEmpty) {
    url += '?$query';
  }
  final uri = Uri.parse(url);
  final headers = {
    'Authorization': 'Bearer $apiKey',
    'Content-Type': 'application/json',
  };

  switch (method.toUpperCase()) {
    case 'GET':
      return http.get(uri, headers: headers);
    case 'POST':
      return http.post(uri, headers: headers, body: body);
    case 'PATCH':
      return http.patch(uri, headers: headers, body: body);
    default:
      throw ArgumentError('Unsupported Airtable HTTP method: $method');
  }
}

/// Verify a Stripe webhook signature.
///
/// Returns `true` when the HMAC-SHA256 signature is valid and the timestamp
/// is within the tolerance window (5 minutes).
bool _verifyWebhookSignature(
    String payload, String sigHeader, String secret) {
  // Parse header: t=...,v1=...,v1=...
  String? timestamp;
  final signatures = <String>[];

  for (final part in sigHeader.split(',')) {
    final kv = part.trim().split('=');
    if (kv.length < 2) continue;
    final key = kv[0];
    final value = kv.sublist(1).join('=');
    if (key == 't') {
      timestamp = value;
    } else if (key == 'v1') {
      signatures.add(value);
    }
  }

  if (timestamp == null || signatures.isEmpty) return false;

  // Reject timestamps older than 5 minutes
  final ts = int.tryParse(timestamp);
  if (ts == null) return false;
  final eventTime = DateTime.fromMillisecondsSinceEpoch(ts * 1000);
  if (DateTime.now().difference(eventTime).inMinutes > 5) return false;

  // Compute expected signature
  final signedPayload = '$timestamp.$payload';
  final hmac = Hmac(sha256, utf8.encode(secret));
  final expected = hmac.convert(utf8.encode(signedPayload)).toString();

  return signatures.any((sig) => sig == expected);
}

/// JSON response helper.
Response _jsonResponse(int status, Object body) {
  return Response(status,
      body: jsonEncode(body),
      headers: {'Content-Type': 'application/json'});
}

// ---------------------------------------------------------------------------
// 1. POST /api/kaf/checkout/create-session
// ---------------------------------------------------------------------------

/// Creates a Stripe Checkout Session for class registration payment.
///
/// Body JSON:
/// ```json
/// {
///   "classId": "recXXX",
///   "parentId": "recYYY",
///   "studentIds": ["recA", "recB"],
///   "studentNames": ["Alice", "Bob"],
///   "oshcSelections": {"recA": true, "recB": false},
///   "parentEmail": "parent@example.com",
///   "isNewParent": true
/// }
/// ```
Future<Response> kafCheckoutCreateSessionHandler(Request request) async {
  try {
    // --- Validate environment ---
    final stripeKey = Platform.environment['KAF_STRIPE_SECRET_KEY'];
    final airtableKey = Platform.environment['AIRTABLE_API_KEY'];
    final airtableBase = Platform.environment['AIRTABLE_BASE_ID'];

    if (stripeKey == null || airtableKey == null || airtableBase == null) {
      print('ERROR: Missing Stripe/Airtable credentials');
      return _jsonResponse(500, {'error': 'Server configuration error'});
    }

    // --- Parse request body ---
    final body = await request.readAsString();
    final data = jsonDecode(body) as Map<String, dynamic>;

    final classId = data['classId'] as String?;
    final parentId = data['parentId'] as String?;
    final studentIds = (data['studentIds'] as List?)?.cast<String>();
    final studentNames = (data['studentNames'] as List?)?.cast<String>();
    final oshcSelections =
        (data['oshcSelections'] as Map<String, dynamic>?) ?? {};
    final parentEmail = data['parentEmail'] as String?;
    final isNewParent = data['isNewParent'] == true;

    if (classId == null ||
        parentId == null ||
        studentIds == null ||
        studentIds.isEmpty ||
        studentNames == null ||
        studentNames.length != studentIds.length ||
        parentEmail == null) {
      return _jsonResponse(400, {'error': 'Missing required fields'});
    }

    // --- Fetch class record from Airtable (server-side price) ---
    final classResp = await _airtableRequest('GET', 'Classes',
        query: 'filterByFormula=RECORD_ID()%3D%22$classId%22');

    if (classResp.statusCode != 200) {
      print('ERROR: Failed to fetch class $classId: ${classResp.body}');
      return _jsonResponse(502, {'error': 'Failed to fetch class details'});
    }

    final classData = jsonDecode(classResp.body) as Map<String, dynamic>;
    final classRecords = classData['records'] as List;
    if (classRecords.isEmpty) {
      return _jsonResponse(404, {'error': 'Class not found'});
    }

    final classFields =
        classRecords[0]['fields'] as Map<String, dynamic>;
    final className = classFields['Name'] as String? ?? 'Class';
    final price = classFields['Price'];
    if (price == null) {
      return _jsonResponse(400, {'error': 'Class has no price configured'});
    }

    // Price is stored as dollars (e.g. 150), convert to cents
    final unitAmount = ((price as num) * 100).round();

    // --- Fetch venue OSHC fee if any students selected OSHC ---
    final hasOshc = oshcSelections.values.any((v) => v == true);
    int oshcAmountCents = 0;
    if (hasOshc) {
      final venueIds = classFields['Venue'] as List?;
      if (venueIds != null && venueIds.isNotEmpty) {
        final venueId = venueIds[0] as String;
        final venueResp = await _airtableRequest('GET', 'Venues',
            query: 'filterByFormula=RECORD_ID()%3D%22$venueId%22');
        if (venueResp.statusCode == 200) {
          final venueData =
              jsonDecode(venueResp.body) as Map<String, dynamic>;
          final venueRecords = venueData['records'] as List;
          if (venueRecords.isNotEmpty) {
            final venueFields =
                venueRecords[0]['fields'] as Map<String, dynamic>;
            final oshcFee = venueFields['OSHC Fee'];
            if (oshcFee != null) {
              oshcAmountCents = ((oshcFee as num) * 100).round();
            }
          }
        }
      }
    }

    // --- Build Stripe form params ---
    final params = <String, String>{};
    params['mode'] = 'payment';
    params['customer_email'] = parentEmail;
    params['success_url'] =
        'https://app.sonzai.com/kaf/register.html?class=$classId&payment=success&session_id={CHECKOUT_SESSION_ID}';
    params['cancel_url'] =
        'https://app.sonzai.com/kaf/register.html?class=$classId&payment=cancelled';

    // Metadata
    params['metadata[class_id]'] = classId;
    params['metadata[parent_id]'] = parentId;
    params['metadata[student_ids]'] = studentIds.join(',');
    params['metadata[is_new_parent]'] = isNewParent.toString();

    // OSHC metadata: comma-separated id:bool pairs
    final oshcPairs = studentIds
        .map((id) => '$id:${oshcSelections[id] == true}')
        .toList();
    params['metadata[oshc]'] = oshcPairs.join(',');

    // Line items: class fee per student + OSHC fee where selected
    var lineIndex = 0;
    for (var i = 0; i < studentIds.length; i++) {
      final prefix = 'line_items[$lineIndex]';
      params['$prefix[price_data][currency]'] = 'aud';
      params['$prefix[price_data][unit_amount]'] = unitAmount.toString();
      params['$prefix[price_data][product_data][name]'] =
          '$className \u2014 ${studentNames[i]}';
      params['$prefix[quantity]'] = '1';
      lineIndex++;

      // Add OSHC line item if selected for this student
      if (oshcAmountCents > 0 && oshcSelections[studentIds[i]] == true) {
        final oshcPrefix = 'line_items[$lineIndex]';
        params['$oshcPrefix[price_data][currency]'] = 'aud';
        params['$oshcPrefix[price_data][unit_amount]'] =
            oshcAmountCents.toString();
        params['$oshcPrefix[price_data][product_data][name]'] =
            'OSHC Collection \u2014 ${studentNames[i]}';
        params['$oshcPrefix[quantity]'] = '1';
        lineIndex++;
      }
    }

    // --- Create Stripe Checkout Session ---
    final stripeResp =
        await _stripeRequest('POST', '/v1/checkout/sessions', params: params);

    if (stripeResp.statusCode != 200) {
      print('ERROR: Stripe create-session failed: ${stripeResp.body}');
      return _jsonResponse(502, {'error': 'Failed to create checkout session'});
    }

    final session = jsonDecode(stripeResp.body) as Map<String, dynamic>;
    final sessionUrl = session['url'] as String?;

    if (sessionUrl == null) {
      return _jsonResponse(502, {'error': 'No session URL returned'});
    }

    return _jsonResponse(200, {'sessionUrl': sessionUrl});
  } catch (e) {
    print('ERROR: checkout/create-session exception: $e');
    return _jsonResponse(500, {'error': e.toString()});
  }
}

// ---------------------------------------------------------------------------
// 2. POST /api/kaf/checkout/webhook
// ---------------------------------------------------------------------------

/// Handles Stripe webhook events (raw POST body, signature verified).
Future<Response> kafCheckoutWebhookHandler(Request request) async {
  try {
    final webhookSecret = Platform.environment['KAF_STRIPE_WEBHOOK_SECRET'];
    if (webhookSecret == null) {
      print('ERROR: Missing KAF_STRIPE_WEBHOOK_SECRET');
      return _jsonResponse(500, {'error': 'Server configuration error'});
    }

    // MUST read raw body FIRST before any parsing
    final rawBody = await request.readAsString();

    // Verify signature
    final sigHeader = request.headers['stripe-signature'] ?? '';
    if (!_verifyWebhookSignature(rawBody, sigHeader, webhookSecret)) {
      print('WARN: Stripe webhook signature verification failed');
      return _jsonResponse(400, {'error': 'Invalid signature'});
    }

    // Parse event
    final event = jsonDecode(rawBody) as Map<String, dynamic>;
    final eventType = event['type'] as String?;

    // Only handle checkout.session.completed
    if (eventType != 'checkout.session.completed') {
      return _jsonResponse(200, {'received': true});
    }

    final sessionObj =
        (event['data'] as Map<String, dynamic>)['object'] as Map<String, dynamic>;
    final metadata = sessionObj['metadata'] as Map<String, dynamic>? ?? {};
    final stripeSessionId = sessionObj['id'] as String;

    final classId = metadata['class_id'] as String?;
    final parentId = metadata['parent_id'] as String?;
    final studentIdsStr = metadata['student_ids'] as String? ?? '';
    final oshcStr = metadata['oshc'] as String? ?? '';

    if (classId == null || parentId == null || studentIdsStr.isEmpty) {
      print('WARN: Webhook missing metadata: $metadata');
      return _jsonResponse(200, {'received': true, 'skipped': 'missing metadata'});
    }

    final studentIds = studentIdsStr.split(',');

    // Parse OSHC selections: "recA:true,recB:false"
    final oshcMap = <String, bool>{};
    for (final pair in oshcStr.split(',')) {
      final parts = pair.split(':');
      if (parts.length == 2) {
        oshcMap[parts[0]] = parts[1] == 'true';
      }
    }

    // --- Check for existing bookings (idempotency) ---
    // Fetch ALL existing bookings for this session to handle partial writes
    final dupCheckResp = await _airtableRequest('GET', 'Bookings',
        query:
            'filterByFormula=%7BStripe%20Session%20ID%7D%3D%22$stripeSessionId%22');

    final existingStudentIds = <String>{};
    if (dupCheckResp.statusCode == 200) {
      final dupData = jsonDecode(dupCheckResp.body) as Map<String, dynamic>;
      final dupRecords = dupData['records'] as List;
      for (final rec in dupRecords) {
        final fields = rec['fields'] as Map<String, dynamic>;
        final stuList = fields['Student'] as List?;
        if (stuList != null && stuList.isNotEmpty) {
          existingStudentIds.add(stuList[0] as String);
        }
      }
    }

    // Filter out students who already have bookings (partial retry)
    final remainingStudentIds =
        studentIds.where((id) => !existingStudentIds.contains(id)).toList();

    if (remainingStudentIds.isEmpty) {
      print('INFO: All bookings already exist for session $stripeSessionId, skipping');
      return _jsonResponse(200, {'received': true, 'skipped': 'duplicate'});
    }

    if (existingStudentIds.isNotEmpty) {
      print('INFO: Partial retry for session $stripeSessionId — '
          '${existingStudentIds.length} existing, '
          '${remainingStudentIds.length} remaining');
    }

    // --- Create Booking records in Airtable (batch of up to 10) ---
    final today = DateTime.now().toIso8601String().substring(0, 10);

    final bookingRecords = remainingStudentIds.map((studentId) {
      return {
        'fields': {
          'Student': [studentId],
          'Class': [classId],
          'Booking Date': today,
          'Payment Status': 'Paid',
          'OSHC Collection': oshcMap[studentId] == true,
          'Stripe Session ID': stripeSessionId,
        },
      };
    }).toList();

    // Airtable batch limit is 10 records per request
    for (var i = 0; i < bookingRecords.length; i += 10) {
      final batch = bookingRecords.sublist(
          i,
          i + 10 > bookingRecords.length
              ? bookingRecords.length
              : i + 10);
      final batchBody = jsonEncode({'records': batch});

      final batchResp =
          await _airtableRequest('POST', 'Bookings', body: batchBody);
      if (batchResp.statusCode != 200) {
        print(
            'ERROR: Airtable booking batch failed (${batchResp.statusCode}): ${batchResp.body}');
        // Return 500 so Stripe retries — partial writes are safe due to
        // per-student idempotency check above
        return _jsonResponse(500, {'error': 'Booking creation failed'});
      }

      // Respect Airtable rate limit (5 req/sec)
      if (i + 10 < bookingRecords.length) {
        await Future.delayed(Duration(milliseconds: 250));
      }
    }

    // --- Notify Sophia via email ---
    try {
      final resendApiKey = Platform.environment['RESEND_API_KEY'];
      if (resendApiKey != null) {
        // Fetch class name and student names for the email
        final classResp = await _airtableRequest('GET', 'Classes',
            query: 'filterByFormula=RECORD_ID()%3D%22$classId%22');
        var className = 'Unknown class';
        if (classResp.statusCode == 200) {
          final classData = jsonDecode(classResp.body) as Map<String, dynamic>;
          final classRecords = classData['records'] as List;
          if (classRecords.isNotEmpty) {
            className = (classRecords[0]['fields'] as Map<String, dynamic>)['Name'] as String? ?? className;
          }
        }

        // Fetch student names
        final studentNames = <String>[];
        for (final studentId in remainingStudentIds) {
          final stuResp = await _airtableRequest('GET', 'Students',
              query: 'filterByFormula=RECORD_ID()%3D%22$studentId%22');
          if (stuResp.statusCode == 200) {
            final stuData = jsonDecode(stuResp.body) as Map<String, dynamic>;
            final stuRecords = stuData['records'] as List;
            if (stuRecords.isNotEmpty) {
              final name = (stuRecords[0]['fields'] as Map<String, dynamic>)['Name'] as String?;
              if (name != null) studentNames.add(name);
            }
          }
        }

        final parentEmail = sessionObj['customer_email'] as String? ?? 'unknown';
        final amountTotal = sessionObj['amount_total'] as num? ?? 0;
        final amountStr = '\$${(amountTotal / 100).toStringAsFixed(2)}';

        final emailBody = {
          'from': 'Kids Art Fun <onboarding@resend.dev>',
          'to': ['anthony.f.lee@gmail.com'],
          'subject': 'New Booking: ${studentNames.isNotEmpty ? studentNames.join(", ") : "New student"} — $className',
          'html': '''
            <h2>New Booking Received</h2>
            <p><strong>Class:</strong> $className</p>
            <p><strong>Students:</strong> ${studentNames.isNotEmpty ? studentNames.join(', ') : remainingStudentIds.join(', ')}</p>
            <p><strong>Parent email:</strong> $parentEmail</p>
            <p><strong>Amount paid:</strong> $amountStr</p>
            <p><strong>OSHC:</strong> ${oshcMap.values.any((v) => v) ? 'Yes' : 'No'}</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
              Stripe Session: $stripeSessionId<br>
              ${DateTime.now().toString()}
            </p>
          ''',
        };

        await http.post(
          Uri.parse('https://api.resend.com/emails'),
          headers: {
            'Authorization': 'Bearer $resendApiKey',
            'Content-Type': 'application/json',
          },
          body: jsonEncode(emailBody),
        );
      }
    } catch (e) {
      // Don't fail the webhook over a notification email
      print('WARN: Failed to send booking notification email: $e');
    }

    return _jsonResponse(200, {'received': true});
  } catch (e) {
    print('ERROR: checkout/webhook exception: $e');
    // Return 500 so Stripe retries the webhook
    return _jsonResponse(500, {'error': 'Webhook processing failed'});
  }
}

// ---------------------------------------------------------------------------
// 3. GET /api/kaf/checkout/success?session_id=...
// ---------------------------------------------------------------------------

/// Returns the status and metadata of a completed Stripe Checkout Session.
Future<Response> kafCheckoutSuccessHandler(Request request) async {
  try {
    final stripeKey = Platform.environment['KAF_STRIPE_SECRET_KEY'];
    if (stripeKey == null) {
      return _jsonResponse(500, {'error': 'Server configuration error'});
    }

    final sessionId = request.url.queryParameters['session_id'];
    if (sessionId == null || sessionId.isEmpty) {
      return _jsonResponse(400, {'error': 'Missing session_id'});
    }

    // Fetch session from Stripe
    final encodedId = Uri.encodeComponent(sessionId);
    final resp = await _stripeRequest('GET', '/v1/checkout/sessions/$encodedId');

    if (resp.statusCode != 200) {
      print('ERROR: Stripe session fetch failed: ${resp.body}');
      return _jsonResponse(502, {'error': 'Failed to fetch session'});
    }

    final session = jsonDecode(resp.body) as Map<String, dynamic>;
    final paymentStatus = session['payment_status'] as String? ?? 'unpaid';
    final metadata = session['metadata'] as Map<String, dynamic>? ?? {};

    return _jsonResponse(200, {
      'status': paymentStatus == 'paid' ? 'paid' : 'unpaid',
      'metadata': metadata,
    });
  } catch (e) {
    print('ERROR: checkout/success exception: $e');
    return _jsonResponse(500, {'error': e.toString()});
  }
}
