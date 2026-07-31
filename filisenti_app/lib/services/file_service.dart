import 'dart:io';
import 'package:file_picker/file_picker.dart';

class FileService {
  static const int _maxFileSize = 5 * 1024 * 1024;

  Future<String?> pickAndReadText() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['txt', 'md', 'csv'],
    );

    if (result == null || result.files.isEmpty) return null;

    final file = File(result.files.single.path!);
    final size = await file.length();

    if (size > _maxFileSize) return null;

    final ext = result.files.single.extension?.toLowerCase();

    switch (ext) {
      case 'csv':
        return _readCsv(file);
      case 'txt':
      case 'md':
      default:
        return file.readAsString();
    }
  }

  Future<String> _readCsv(File file) async {
    final lines = await file.readAsLines();
    if (lines.isEmpty) return '';

    final sentences = <String>[];
    for (final line in lines.skip(1)) {
      final cols = _parseCsvLine(line);
      if (cols.isNotEmpty) {
        sentences.add(cols.first);
      }
    }
    return sentences.join('. ');
  }

  List<String> _parseCsvLine(String line) {
    final result = <String>[];
    bool inQuotes = false;
    final current = StringBuffer();

    for (int i = 0; i < line.length; i++) {
      final char = line[i];
      if (char == '"') {
        inQuotes = !inQuotes;
      } else if (char == ',' && !inQuotes) {
        result.add(current.toString().trim());
        current.clear();
      } else {
        current.write(char);
      }
    }
    result.add(current.toString().trim());
    return result;
  }
}
