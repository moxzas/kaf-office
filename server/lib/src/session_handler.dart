import 'dart:convert';
import 'dart:io';
import 'package:shelf/shelf.dart';
import 'package:http/http.dart' as http;

/// Day-of-week name to Dart DateTime.weekday mapping
const _dayOfWeekMap = {
  'Monday': DateTime.monday,
  'Tuesday': DateTime.tuesday,
  'Wednesday': DateTime.wednesday,
  'Thursday': DateTime.thursday,
  'Friday': DateTime.friday,
  'Saturday': DateTime.saturday,
  'Sunday': DateTime.sunday,
};

/// Generates session records in Airtable for a given class.
///
/// POST /api/kaf/sessions/generate
/// Body: { "classId": "recXXXXXXXXXXXXX" }
///
/// Term classes: generates N weekly sessions from term start date.
/// Holiday programs: generates a single session.
/// Returns 409 if sessions already exist for the class.
Future<Response> kafSessionGenerateHandler(Request request) async {
  try {
    final body = await request.readAsString();
    final data = jsonDecode(body) as Map<String, dynamic>;

    final classId = data['classId'] as String?;
    if (classId == null || classId.isEmpty) {
      return _jsonResponse(400, {'error': 'Missing required field: classId'});
    }

    final airtableApiKey = Platform.environment['AIRTABLE_API_KEY'];
    final airtableBaseId = Platform.environment['AIRTABLE_BASE_ID'];

    if (airtableApiKey == null || airtableBaseId == null) {
      print('ERROR: Missing Airtable credentials');
      return _jsonResponse(500, {'error': 'Server configuration error'});
    }

    // 1. Fetch the class record
    final classResp = await _airtableGet(
      airtableBaseId,
      airtableApiKey,
      'Classes/$classId',
    );

    if (classResp.statusCode == 404) {
      return _jsonResponse(404, {'error': 'Class not found'});
    }
    if (classResp.statusCode != 200) {
      print('ERROR: Failed to fetch class: ${classResp.body}');
      return _jsonResponse(502, {'error': 'Failed to fetch class from Airtable'});
    }

    final classRecord = jsonDecode(classResp.body) as Map<String, dynamic>;
    final fields = classRecord['fields'] as Map<String, dynamic>;

    final className = fields['Name'] as String? ?? 'Unknown';
    final classType = fields['Type'] as String? ?? 'Term';
    final dayOfWeek = fields['Day of Week'] as String?;
    final termStartDate = fields['Term Start Date'] as String?;
    final sessionsInTerm = (fields['Sessions in Term'] as num?)?.toInt();

    // 2. Validate required fields
    if (termStartDate == null || termStartDate.isEmpty) {
      return _jsonResponse(400, {
        'error': 'Class is missing Term Start Date',
        'classId': classId,
      });
    }

    if (classType == 'Term') {
      if (dayOfWeek == null || !_dayOfWeekMap.containsKey(dayOfWeek)) {
        return _jsonResponse(400, {
          'error': 'Class is missing or has invalid Day of Week',
          'classId': classId,
        });
      }
      if (sessionsInTerm == null || sessionsInTerm <= 0) {
        return _jsonResponse(400, {
          'error': 'Class is missing Sessions in Term',
          'classId': classId,
        });
      }
    }

    // 3. Check for existing sessions (duplicate prevention)
    final existingResp = await _airtableGet(
      airtableBaseId,
      airtableApiKey,
      'Sessions?filterByFormula=${Uri.encodeComponent("FIND('$classId', ARRAYJOIN({Class}))")}&maxRecords=1',
    );

    if (existingResp.statusCode == 200) {
      final existingData = jsonDecode(existingResp.body) as Map<String, dynamic>;
      final existingRecords = existingData['records'] as List;
      if (existingRecords.isNotEmpty) {
        return _jsonResponse(409, {
          'error': 'Sessions already exist for this class. Delete existing sessions first.',
          'classId': classId,
          'className': className,
        });
      }
    }

    // 4. Generate session dates
    final startDate = DateTime.parse(termStartDate);
    final List<Map<String, dynamic>> sessionFields;

    if (classType == 'Holiday Program') {
      // Single session for holiday programs
      sessionFields = [
        {
          'Class': [classId],
          'Session Date': _formatDate(startDate),
          'Week Number': 1,
          'Status': 'Scheduled',
        }
      ];
    } else {
      // Term classes: find first day-of-week, generate weekly sessions
      final targetDay = _dayOfWeekMap[dayOfWeek]!;
      final firstSession = _findFirstDayOfWeek(startDate, targetDay);

      sessionFields = List.generate(sessionsInTerm!, (i) {
        final sessionDate = firstSession.add(Duration(days: 7 * i));
        return {
          'Class': [classId],
          'Session Date': _formatDate(sessionDate),
          'Week Number': i + 1,
          'Status': 'Scheduled',
        };
      });
    }

    // 5. POST to Airtable in batches of 10
    int created = 0;
    for (var i = 0; i < sessionFields.length; i += 10) {
      final batch = sessionFields.sublist(
        i,
        i + 10 > sessionFields.length ? sessionFields.length : i + 10,
      );

      final batchPayload = {
        'records': batch.map((f) => {'fields': f}).toList(),
      };

      final batchResp = await http.post(
        Uri.parse('https://api.airtable.com/v0/$airtableBaseId/Sessions'),
        headers: {
          'Authorization': 'Bearer $airtableApiKey',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(batchPayload),
      );

      if (batchResp.statusCode != 200) {
        print('ERROR: Failed to create sessions batch: ${batchResp.body}');
        return _jsonResponse(502, {
          'error': 'Failed to create sessions in Airtable',
          'detail': batchResp.body,
          'sessionsCreatedBeforeError': created,
        });
      }

      final batchResult = jsonDecode(batchResp.body) as Map<String, dynamic>;
      created += (batchResult['records'] as List).length;

      // Rate limit: 250ms delay between batches
      if (i + 10 < sessionFields.length) {
        await Future.delayed(Duration(milliseconds: 250));
      }
    }

    print('✓ Created $created sessions for class: $className ($classId)');

    return _jsonResponse(200, {
      'success': true,
      'classId': classId,
      'className': className,
      'sessionsCreated': created,
      'firstDate': sessionFields.first['Session Date'],
      'lastDate': sessionFields.last['Session Date'],
    });
  } catch (e) {
    print('ERROR: Session generate exception: $e');
    return _jsonResponse(500, {'error': e.toString()});
  }
}

/// Generates sessions for ALL active classes in a given term.
///
/// POST /api/kaf/sessions/generate-term
/// Body: { "term": "Term 2 2026" }
///
/// Skips classes that already have sessions. Returns summary.
Future<Response> kafSessionGenerateTermHandler(Request request) async {
  try {
    final body = await request.readAsString();
    final data = jsonDecode(body) as Map<String, dynamic>;

    final term = data['term'] as String?;
    if (term == null || term.isEmpty) {
      return _jsonResponse(400, {'error': 'Missing required field: term'});
    }

    final airtableApiKey = Platform.environment['AIRTABLE_API_KEY'];
    final airtableBaseId = Platform.environment['AIRTABLE_BASE_ID'];

    if (airtableApiKey == null || airtableBaseId == null) {
      print('ERROR: Missing Airtable credentials');
      return _jsonResponse(500, {'error': 'Server configuration error'});
    }

    // Fetch all active classes for this term
    final filter = Uri.encodeComponent(
      "AND({Term}='$term', {Status}='Active')",
    );
    final classesResp = await _airtableGet(
      airtableBaseId,
      airtableApiKey,
      'Classes?filterByFormula=$filter',
    );

    if (classesResp.statusCode != 200) {
      print('ERROR: Failed to fetch classes: ${classesResp.body}');
      return _jsonResponse(502, {'error': 'Failed to fetch classes from Airtable'});
    }

    final classesData = jsonDecode(classesResp.body) as Map<String, dynamic>;
    final classes = classesData['records'] as List;

    if (classes.isEmpty) {
      return _jsonResponse(200, {
        'success': true,
        'term': term,
        'message': 'No active classes found for this term',
        'results': [],
      });
    }

    // Generate sessions for each class by delegating to the single-class handler logic
    final results = <Map<String, dynamic>>[];

    for (final classRecord in classes) {
      final classId = classRecord['id'] as String;
      final className = classRecord['fields']['Name'] as String? ?? 'Unknown';

      // Check for existing sessions
      final existingResp = await _airtableGet(
        airtableBaseId,
        airtableApiKey,
        'Sessions?filterByFormula=${Uri.encodeComponent("FIND('$classId', ARRAYJOIN({Class}))")}&maxRecords=1',
      );

      if (existingResp.statusCode == 200) {
        final existingData = jsonDecode(existingResp.body) as Map<String, dynamic>;
        if ((existingData['records'] as List).isNotEmpty) {
          results.add({
            'classId': classId,
            'className': className,
            'status': 'skipped',
            'reason': 'Sessions already exist',
          });
          await Future.delayed(Duration(milliseconds: 250));
          continue;
        }
      }

      // Build a fake request to reuse the generate handler
      // Instead, inline the generation logic
      final fields = classRecord['fields'] as Map<String, dynamic>;
      final dayOfWeek = fields['Day of Week'] as String?;
      final termStartDate = fields['Term Start Date'] as String?;
      final sessionsInTerm = (fields['Sessions in Term'] as num?)?.toInt();
      final classType = fields['Type'] as String? ?? 'Term';

      if (termStartDate == null) {
        results.add({
          'classId': classId,
          'className': className,
          'status': 'skipped',
          'reason': 'Missing Term Start Date',
        });
        continue;
      }

      final startDate = DateTime.parse(termStartDate);
      final List<Map<String, dynamic>> sessionFields;

      if (classType == 'Holiday Program') {
        sessionFields = [
          {
            'Class': [classId],
            'Session Date': _formatDate(startDate),
            'Week Number': 1,
            'Status': 'Scheduled',
          }
        ];
      } else {
        if (dayOfWeek == null || !_dayOfWeekMap.containsKey(dayOfWeek)) {
          results.add({
            'classId': classId,
            'className': className,
            'status': 'skipped',
            'reason': 'Missing or invalid Day of Week',
          });
          continue;
        }
        if (sessionsInTerm == null || sessionsInTerm <= 0) {
          results.add({
            'classId': classId,
            'className': className,
            'status': 'skipped',
            'reason': 'Missing Sessions in Term',
          });
          continue;
        }

        final targetDay = _dayOfWeekMap[dayOfWeek]!;
        final firstSession = _findFirstDayOfWeek(startDate, targetDay);

        sessionFields = List.generate(sessionsInTerm, (i) {
          final sessionDate = firstSession.add(Duration(days: 7 * i));
          return {
            'Class': [classId],
            'Session Date': _formatDate(sessionDate),
            'Week Number': i + 1,
            'Status': 'Scheduled',
          };
        });
      }

      // POST in batches
      int created = 0;
      bool failed = false;
      for (var i = 0; i < sessionFields.length; i += 10) {
        final batch = sessionFields.sublist(
          i,
          i + 10 > sessionFields.length ? sessionFields.length : i + 10,
        );

        final batchResp = await http.post(
          Uri.parse('https://api.airtable.com/v0/$airtableBaseId/Sessions'),
          headers: {
            'Authorization': 'Bearer $airtableApiKey',
            'Content-Type': 'application/json',
          },
          body: jsonEncode({
            'records': batch.map((f) => {'fields': f}).toList(),
          }),
        );

        if (batchResp.statusCode != 200) {
          print('ERROR: Failed to create sessions for $className: ${batchResp.body}');
          results.add({
            'classId': classId,
            'className': className,
            'status': 'error',
            'reason': 'Airtable API error',
            'sessionsCreated': created,
          });
          failed = true;
          break;
        }

        final batchResult = jsonDecode(batchResp.body) as Map<String, dynamic>;
        created += (batchResult['records'] as List).length;
        await Future.delayed(Duration(milliseconds: 250));
      }

      if (!failed) {
        results.add({
          'classId': classId,
          'className': className,
          'status': 'created',
          'sessionsCreated': created,
          'firstDate': sessionFields.first['Session Date'],
          'lastDate': sessionFields.last['Session Date'],
        });
        print('✓ Created $created sessions for: $className');
      }
    }

    final totalCreated = results
        .where((r) => r['status'] == 'created')
        .fold<int>(0, (sum, r) => sum + (r['sessionsCreated'] as int));

    return _jsonResponse(200, {
      'success': true,
      'term': term,
      'classesProcessed': classes.length,
      'totalSessionsCreated': totalCreated,
      'results': results,
    });
  } catch (e) {
    print('ERROR: Session generate-term exception: $e');
    return _jsonResponse(500, {'error': e.toString()});
  }
}

// --- Helpers ---

/// Find the first occurrence of [targetDay] on or after [startDate].
DateTime _findFirstDayOfWeek(DateTime startDate, int targetDay) {
  var date = startDate;
  while (date.weekday != targetDay) {
    date = date.add(Duration(days: 1));
  }
  return date;
}

/// Format a DateTime as ISO date string (YYYY-MM-DD).
String _formatDate(DateTime date) {
  return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
}

/// Convenience GET request to Airtable.
Future<http.Response> _airtableGet(
  String baseId,
  String apiKey,
  String path,
) {
  return http.get(
    Uri.parse('https://api.airtable.com/v0/$baseId/$path'),
    headers: {
      'Authorization': 'Bearer $apiKey',
    },
  );
}

/// Build a JSON shelf Response.
Response _jsonResponse(int statusCode, Map<String, dynamic> body) {
  return Response(
    statusCode,
    body: jsonEncode(body),
    headers: {'Content-Type': 'application/json'},
  );
}
