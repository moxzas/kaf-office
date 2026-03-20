import 'dart:convert';
import 'dart:io';
import 'package:shelf/shelf.dart';
import 'package:http/http.dart' as http;

/// Handles KAF enrollment audit logging
///
/// Accepts enrollment submission data and:
/// 1. Writes immutable JSON audit log to Airtable
/// 2. Sends notification email to Sophia
/// 3. Sends confirmation email to parent
Future<Response> kafAuditHandler(Request request) async {
  try {
    // Parse request body
    final body = await request.readAsString();
    final data = jsonDecode(body) as Map<String, dynamic>;

    // Validate required fields
    if (!data.containsKey('action') ||
        !data.containsKey('parentRecordId') ||
        !data.containsKey('parentEmail') ||
        !data.containsKey('afterState')) {
      return Response.badRequest(
        body: jsonEncode({'error': 'Missing required fields'}),
        headers: {'Content-Type': 'application/json'},
      );
    }

    final action = data['action'] as String; // 'Created' or 'Updated'
    final parentRecordId = data['parentRecordId'] as String;
    final parentEmail = data['parentEmail'] as String;
    final parentName = data['parentName'] as String? ?? '';
    final beforeState = data['beforeState']; // Can be null for new enrollments
    final afterState = data['afterState'];

    // Get environment variables
    final airtableApiKey = Platform.environment['AIRTABLE_API_KEY'];
    final airtableBaseId = Platform.environment['AIRTABLE_BASE_ID'];

    if (airtableApiKey == null || airtableBaseId == null) {
      print('ERROR: Missing Airtable credentials');
      return Response.internalServerError(
        body: jsonEncode({'error': 'Server configuration error'}),
        headers: {'Content-Type': 'application/json'},
      );
    }

    // Create complete audit data blob
    final auditData = {
      'timestamp': DateTime.now().toIso8601String(),
      'recordType': 'KAF Enrollment',
      'recordId': parentRecordId,
      'action': action,
      'parentEmail': parentEmail,
      'parentName': parentName,
      'before': beforeState,
      'after': afterState,
    };

    // Write to Airtable Audit Log (simple JSON blob)
    final auditLogData = {
      'fields': {
        'Record ID': parentRecordId == 'pending' ? 'Incomplete' : parentRecordId,
        'Record Type': 'KAF Enrollment',
        'Action': action,
        'Email': parentEmail,
        'Data': jsonEncode(auditData),
      }
    };

    final auditResponse = await http.post(
      Uri.parse('https://api.airtable.com/v0/$airtableBaseId/Audit%20Log'),
      headers: {
        'Authorization': 'Bearer $airtableApiKey',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(auditLogData),
    );

    if (auditResponse.statusCode != 200) {
      print('ERROR: Failed to create audit log: ${auditResponse.body}');
      // Don't fail the request - audit logging is non-critical
    } else {
      final auditResult = jsonDecode(auditResponse.body);
      final auditRecordId = auditResult['id'];
      print('✓ Audit log created: $auditRecordId');
    }

    // Send emails (only for completed enrollments, not incomplete ones)
    if (action != 'Incomplete') {
      try {
        final deltaSummary = _calculateDelta(beforeState, afterState, action);

        await _sendNotificationEmails(
          action: action,
          parentEmail: parentEmail,
          parentName: parentName,
          parentRecordId: parentRecordId,
          deltaSummary: deltaSummary,
          afterState: afterState,
        );

        print('✓ Emails sent successfully');
      } catch (e) {
        print('ERROR: Failed to send emails: $e');
        // Don't fail the request - email sending is non-critical
      }
    } else {
      print('Skipping emails for incomplete submission (page 1 only)');
    }

    return Response.ok(
      jsonEncode({
        'success': true,
        'message': 'Audit log created and emails sent',
      }),
      headers: {'Content-Type': 'application/json'},
    );

  } catch (e) {
    print('ERROR: Audit handler exception: $e');
    return Response.internalServerError(
      body: jsonEncode({'error': e.toString()}),
      headers: {'Content-Type': 'application/json'},
    );
  }
}

/// Calculate human-readable delta summary
String _calculateDelta(dynamic beforeState, dynamic afterState, String action) {
  final changes = <String>[];

  if (action == 'Created') {
    changes.add('New enrollment created');

    if (afterState is Map && afterState['parent'] != null) {
      final parent = afterState['parent'];
      changes.add('• Parent: ${parent['Name']}');
    }

    if (afterState is Map && afterState['students'] != null) {
      final students = afterState['students'] as List;
      final studentNames = students.map((s) => s['Name']).join(', ');
      changes.add('• Students: $studentNames (${students.length} student${students.length > 1 ? 's' : ''})');
    }
  } else {
    changes.add('Enrollment updated');

    // Compare parent fields
    if (beforeState is Map && afterState is Map) {
      final beforeParent = beforeState['parent'] as Map?;
      final afterParent = afterState['parent'] as Map?;

      if (beforeParent != null && afterParent != null) {
        beforeParent.forEach((key, beforeValue) {
          final afterValue = afterParent[key];
          if (beforeValue != afterValue && afterValue != null && beforeValue != null) {
            changes.add('• $key changed: $beforeValue → $afterValue');
          }
        });
      }

      // Compare students
      final beforeStudents = (beforeState['students'] as List?) ?? [];
      final afterStudents = (afterState['students'] as List?) ?? [];

      if (afterStudents.length > beforeStudents.length) {
        final newCount = afterStudents.length - beforeStudents.length;
        changes.add('• Added $newCount student${newCount > 1 ? 's' : ''}');
      }

      if (beforeStudents.length > afterStudents.length) {
        final removed = beforeStudents.length - afterStudents.length;
        changes.add('• Removed $removed student${removed > 1 ? 's' : ''}');
      }

      changes.add('• Total students: ${afterStudents.length}');
    }
  }

  return changes.join('\n');
}

/// Send notification emails to Sophia and parent
Future<void> _sendNotificationEmails({
  required String action,
  required String parentEmail,
  required String parentName,
  required String parentRecordId,
  required String deltaSummary,
  required dynamic afterState,
}) async {
  final resendApiKey = Platform.environment['RESEND_API_KEY'];

  if (resendApiKey == null) {
    throw Exception('RESEND_API_KEY not configured');
  }

  final editLink = 'https://app.sonzai.com/kaf/enrollment.html?parent=$parentRecordId';

  // Email to Sophia (notification)
  final sophiaEmail = {
    'from': 'Kids Art Fun <onboarding@resend.dev>',
    'to': ['anthony.f.lee@gmail.com'],
    'subject': action == 'Created'
        ? 'New Enrollment: $parentName'
        : 'Enrollment Updated: $parentName',
    'html': '''
      <h2>KAF Enrollment ${action == 'Created' ? 'Received' : 'Updated'}</h2>

      <p><strong>Parent:</strong> $parentName ($parentEmail)</p>

      <h3>Changes:</h3>
      <pre>${deltaSummary.replaceAll('\n', '<br>')}</pre>

      <p><a href="$editLink" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">View Full Enrollment</a></p>

      <hr>
      <p style="color: #666; font-size: 12px;">
        Submitted: ${DateTime.now().toString()}<br>
        Record ID: $parentRecordId
      </p>
    ''',
  };

  await http.post(
    Uri.parse('https://api.resend.com/emails'),
    headers: {
      'Authorization': 'Bearer $resendApiKey',
      'Content-Type': 'application/json',
    },
    body: jsonEncode(sophiaEmail),
  );

  // Email to parent (confirmation)
  final parentEmailContent = {
    'from': 'Kids Art Fun <onboarding@resend.dev>',
    'to': [parentEmail],
    'subject': action == 'Created'
        ? 'Welcome to Kids Art Fun!'
        : 'Your Enrollment Has Been Updated',
    'html': '''
      <h2>Thanks for enrolling with Kids Art Fun!</h2>

      <p>Hi $parentName,</p>

      <p>${action == 'Created'
          ? "We've received your enrollment and are excited to have your family join us!"
          : "Your enrollment details have been updated successfully."
      }</p>

      <h3>Your Enrollment Details:</h3>
      ${_formatEnrollmentSummary(afterState)}

      <p><strong>Need to make changes?</strong></p>
      <p>Use this link anytime to view or update your enrollment:</p>
      <p><a href="$editLink" style="background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">View/Edit Enrollment</a></p>

      <hr>
      <p style="color: #666; font-size: 12px;">
        Save this email! You'll need this link to make changes later.
      </p>

      <p>Questions? Reply to this email or contact us.</p>

      <p>See you soon!<br>
      The Kids Art Fun Team</p>
    ''',
  };

  await http.post(
    Uri.parse('https://api.resend.com/emails'),
    headers: {
      'Authorization': 'Bearer $resendApiKey',
      'Content-Type': 'application/json',
    },
    body: jsonEncode(parentEmailContent),
  );
}

/// Format enrollment data as HTML summary
String _formatEnrollmentSummary(dynamic afterState) {
  if (afterState is! Map) return '';

  final parent = afterState['parent'] as Map?;
  final students = afterState['students'] as List? ?? [];

  final parts = <String>[];

  if (parent != null) {
    parts.add('''
      <p><strong>Contact Information:</strong><br>
      ${parent['Email']}<br>
      ${parent['Mobile']}<br>
      ${parent['Address'] ?? ''}, ${parent['Suburb'] ?? ''} ${parent['Postcode'] ?? ''}</p>
    ''');
  }

  if (students.isNotEmpty) {
    parts.add('<p><strong>Students:</strong></p><ul>');
    for (final student in students) {
      parts.add('<li>${student['Name']} - ${student['School']}</li>');
    }
    parts.add('</ul>');
  }

  return parts.join('\n');
}
