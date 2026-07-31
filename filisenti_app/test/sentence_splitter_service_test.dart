import 'package:flutter_test/flutter_test.dart';
import 'package:filisenti_app/services/sentence_splitter_service.dart';

void main() {
  final splitter = SentenceSplitterService();

  test('splits on periods, question marks, and exclamations', () {
    final result = splitter.split('Ang ganda! Okay lang. Sigurado ka?');
    expect(result, ['Ang ganda!', 'Okay lang.', 'Sigurado ka?']);
  });

  test('keeps a trailing segment without a delimiter', () {
    final result = splitter.split('Mabuti naman');
    expect(result, ['Mabuti naman']);
  });

  test('trims surrounding whitespace from segments', () {
    final result = splitter.split('  Ang ganda!  ');
    expect(result, ['Ang ganda!']);
  });

  test('returns empty list for blank input', () {
    expect(splitter.split(''), isEmpty);
    expect(splitter.split('   \n  '), isEmpty);
  });

  test('treats text without delimiters as a single sentence', () {
    final result = splitter.split('Una\nPangalawa');
    expect(result, ['Una\nPangalawa']);
  });
}
