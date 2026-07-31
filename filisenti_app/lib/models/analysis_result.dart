import 'sentence_sentiment.dart';

class AnalysisResult {
  final List<SentenceSentiment> sentences;
  final Map<String, int> counts;
  final Map<String, double> percentages;
  final String majoritySentiment;

  AnalysisResult({
    required this.sentences,
    required this.counts,
    required this.percentages,
    required this.majoritySentiment,
  });

  int get total => sentences.length;

  factory AnalysisResult.fromSentences(List<SentenceSentiment> sentences) {
    final counts = <String, int>{'Positive': 0, 'Neutral': 0, 'Negative': 0};
    for (final s in sentences) {
      counts[s.sentiment] = (counts[s.sentiment] ?? 0) + 1;
    }
    final total = sentences.length;
    final percentages = <String, double>{};
    for (final entry in counts.entries) {
      percentages[entry.key] =
          total > 0 ? (entry.value / total) * 100 : 0.0;
    }
    final majority = counts.entries
        .reduce((a, b) => a.value >= b.value ? a : b)
        .key;

    return AnalysisResult(
      sentences: sentences,
      counts: counts,
      percentages: percentages,
      majoritySentiment: majority,
    );
  }

  Map<String, dynamic> toJson() => {
        'majority_sentiment': majoritySentiment,
        'total': total,
        'counts': counts,
        'percentages': percentages,
        'sentences': sentences.map((s) => s.toJson()).toList(),
      };
}
