import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:filisenti_app/models/sentence_sentiment.dart';

void main() {
  const positive = SentenceSentiment(
    text: 'Ang ganda!',
    sentiment: 'Positive',
    confidence: 0.95,
  );

  test('toJson produces expected map', () {
    expect(positive.toJson(), {
      'text': 'Ang ganda!',
      'sentiment': 'Positive',
      'confidence': 0.95,
    });
  });

  test('fromJson round-trips', () {
    final restored = SentenceSentiment.fromJson(positive.toJson());
    expect(restored.text, positive.text);
    expect(restored.sentiment, positive.sentiment);
    expect(restored.confidence, positive.confidence);
  });

  test('fromJson accepts int-like confidence', () {
    final restored = SentenceSentiment.fromJson({
      'text': 'ok',
      'sentiment': 'Neutral',
      'confidence': 1,
    });
    expect(restored.confidence, 1.0);
  });

  test('color maps per sentiment', () {
    expect(
      const SentenceSentiment(
        text: 'a',
        sentiment: 'Positive',
        confidence: 0.5,
      ).color,
      const Color(0xFF4CAF50),
    );
    expect(
      const SentenceSentiment(
        text: 'a',
        sentiment: 'Negative',
        confidence: 0.5,
      ).color,
      const Color(0xFFF44336),
    );
  });
}
