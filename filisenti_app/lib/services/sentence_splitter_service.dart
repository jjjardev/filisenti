class SentenceSplitterService {
  List<String> split(String text) {
    if (text.trim().isEmpty) return [];

    final sentences = <String>[];
    final buffer = StringBuffer();
    final delimiters = <int>{'.'.codeUnitAt(0), '?'.codeUnitAt(0), '!'.codeUnitAt(0)};

    for (int i = 0; i < text.length; i++) {
      buffer.writeCharCode(text.codeUnitAt(i));
      if (delimiters.contains(text.codeUnitAt(i))) {
        final sentence = buffer.toString().trim();
        if (sentence.isNotEmpty) {
          sentences.add(sentence);
        }
        buffer.clear();
      }
    }

    final remaining = buffer.toString().trim();
    if (remaining.isNotEmpty) {
      sentences.add(remaining);
    }

    return sentences.where((s) => s.isNotEmpty).toList();
  }
}
