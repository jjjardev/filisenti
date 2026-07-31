import 'package:flutter/material.dart';

class SentenceSentiment {
  final String text;
  final String sentiment;
  final double confidence;

  const SentenceSentiment({
    required this.text,
    required this.sentiment,
    required this.confidence,
  });

  Color get color {
    switch (sentiment) {
      case 'Positive':
        return const Color(0xFF4CAF50);
      case 'Neutral':
        return const Color(0xFFFFC107);
      case 'Negative':
        return const Color(0xFFF44336);
      default:
        return Colors.grey;
    }
  }

  Color get bgColor => color.withAlpha(75);

  Map<String, dynamic> toJson() => {
        'text': text,
        'sentiment': sentiment,
        'confidence': confidence,
      };

  factory SentenceSentiment.fromJson(Map<String, dynamic> json) =>
      SentenceSentiment(
        text: json['text'] as String,
        sentiment: json['sentiment'] as String,
        confidence: (json['confidence'] as num).toDouble(),
      );
}
