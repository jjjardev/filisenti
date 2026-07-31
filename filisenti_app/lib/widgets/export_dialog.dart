import 'package:flutter/material.dart';
import '../models/analysis_result.dart';
import '../services/export_service.dart';

class ExportDialog extends StatelessWidget {
  final AnalysisResult result;

  const ExportDialog({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: Row(
        children: [
          Icon(Icons.file_download, color: theme.colorScheme.primary),
          const SizedBox(width: 8),
          Text('Export Results'),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          _option(
            context,
            Icons.table_chart_outlined,
            'CSV',
            'Open in spreadsheet apps',
            () => _export(context, ExportType.csv),
          ),
          const Divider(height: 1),
          _option(
            context,
            Icons.code_outlined,
            'JSON',
            'Machine-readable format',
            () => _export(context, ExportType.json),
          ),
          const Divider(height: 1),
          _option(
            context,
            Icons.share_outlined,
            'Share as text',
            'Copy or send via messaging apps',
            () => _shareText(context),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
      ],
    );
  }

  Widget _option(
    BuildContext context,
    IconData icon,
    String title,
    String subtitle,
    VoidCallback onTap,
  ) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(subtitle),
      onTap: onTap,
      contentPadding: EdgeInsets.zero,
    );
  }

  Future<void> _export(BuildContext context, ExportType type) async {
    Navigator.pop(context);
    final export = ExportService();
    try {
      final file = type == ExportType.csv
          ? await export.toCsv(result)
          : await export.toJson(result);
      await export.shareFile(file);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Export failed: $e')),
        );
      }
    }
  }

  Future<void> _shareText(BuildContext context) async {
    Navigator.pop(context);
    final export = ExportService();
    await export.shareText(result);
  }
}
