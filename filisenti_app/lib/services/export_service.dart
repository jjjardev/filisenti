import 'dart:convert';
import 'dart:io';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import '../models/analysis_result.dart';

enum ExportType { csv, json }

class ExportService {
  Future<File> toCsv(AnalysisResult result) async {
    final buffer = StringBuffer();
    buffer.writeln('Sentence,Sentiment,Confidence');
    for (final s in result.sentences) {
      final escaped = s.text.replaceAll('"', '""');
      buffer.writeln('"$escaped",${s.sentiment},${s.confidence.toStringAsFixed(4)}');
    }
    final dir = await getApplicationDocumentsDirectory();
    final timestamp = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
    final file = File('${dir.path}/filisenti_$timestamp.csv');
    await file.writeAsString(buffer.toString());
    return file;
  }

  Future<File> toJson(AnalysisResult result) async {
    final dir = await getApplicationDocumentsDirectory();
    final timestamp = DateFormat('yyyyMMdd_HHmmss').format(DateTime.now());
    final file = File('${dir.path}/filisenti_$timestamp.json');
    final encoder = const JsonEncoder.withIndent('  ');
    await file.writeAsString(encoder.convert(result.toJson()));
    return file;
  }

  Future<void> shareFile(File file) async {
    final xFile = XFile(file.path);
    await Share.shareXFiles([xFile], text: 'FiliSenti Analysis Results');
  }

  Future<void> shareText(AnalysisResult result) async {
    final buffer = StringBuffer();
    buffer.writeln('FiliSenti Analysis Results');
    buffer.writeln('========================');
    buffer.writeln('Majority: ${result.majoritySentiment}');
    buffer.writeln('Total sentences: ${result.total}');
    buffer.writeln();
    for (final entry in result.percentages.entries) {
      buffer.writeln('${entry.key}: ${entry.value.toStringAsFixed(1)}%');
    }
    buffer.writeln();
    buffer.writeln('--- Sentence Breakdown ---');
    for (final s in result.sentences) {
      buffer.writeln('[${s.sentiment}] (${(s.confidence * 100).toStringAsFixed(0)}%) ${s.text}');
    }
    await Share.share(buffer.toString(), subject: 'FiliSenti Results');
  }
}
