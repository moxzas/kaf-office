/// KAF (Kids Art Fun) server-side handlers.
///
/// Provides a ready-to-mount [kafApiRouter] for the Sonzai Shelf server.
/// The host server only needs to mount this router — all KAF routes are
/// self-contained here.
///
/// ```dart
/// import 'package:kaf_server/kaf_server.dart';
/// router..mount('/api/kaf/', kafApiRouter);
/// ```
library kaf_server;

export 'src/kaf_router.dart' show kafApiRouter;
