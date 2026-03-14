import 'package:shelf_router/shelf_router.dart';
import 'audit_handler.dart';
import 'session_handler.dart';
import 'airtable_proxy_handler.dart';

/// All KAF API routes. Mount at /api/kaf/ in the host server.
///
/// Add new KAF endpoints here — the host server doesn't need to change.
final kafApiRouter = Router()
  ..post('/audit', kafAuditHandler)
  ..post('/sessions/generate', kafSessionGenerateHandler)
  ..post('/sessions/generate-term', kafSessionGenerateTermHandler)
  // Airtable proxy — keeps API key server-side
  ..get('/db/<table>', kafAirtableProxyHandler)
  ..post('/db/<table>', kafAirtableProxyHandler)
  ..get('/db/<table>/<recordId>', kafAirtableProxyHandler)
  ..patch('/db/<table>/<recordId>', kafAirtableProxyHandler)
  ..delete('/db/<table>/<recordId>', kafAirtableProxyHandler);
