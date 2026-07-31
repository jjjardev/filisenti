import 'package:flutter_test/flutter_test.dart';
import 'package:filisenti_app/models/analysis_result.dart';
import 'package:filisenti_app/models/sentence_sentiment.dart';

SentenceSentiment _s(String text, String sentiment) => SentenceSentiment(
      text: text,
      sentiment: sentiment,
      confidence: 0.9,
    );

void main() {
  test('fromSentences computes counts, percentages, and majority', () {
    final result = AnalysisResult.fromSentences([
      _s('A', 'Positive'),
      _s('B', 'Positive'),
      _s('C', 'Neutral'),
      _s('D', 'Negative'),
    ]);

    expect(result.total, 4);
    expect(result.counts, {'Positive': 2, 'Neutral': 1, 'Negative': 1});
    expect(result.percentages['Positive'], 50.0);
    expect(result.percentages['Neutral'], 25.0);
    expect(result.percentages['Negative'], 25.0);
    expect(result.majoritySentiment, 'Positive');
  });

  test('fromSentences handles a single sentence', () {
    final result = AnalysisResult.fromSentences([_s('A', 'Negative')]);
    expect(result.majoritySentiment, 'Negative');
    expect(result.percentages['Negative'], 100.0);
  });

  test('toJson serializes full result', () {
    final result = AnalysisResult.fromSentences([
      _s('A', 'Positive'),
      _s('B', 'Negative'),
    ]);

    final json = result.toJson();
    expect(json['total'], 2);
    expect(json['majority_sentiment'], 'Positive');
    expect((json['sentences'] as List).length, 2);
    expect(json['counts']['Negative'], 1);
  });
}
