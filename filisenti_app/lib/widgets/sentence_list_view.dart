import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/sentence_sentiment.dart';
import '../theme/app_theme.dart';
import 'sentiment_badge.dart';

class SentenceListView extends StatelessWidget {
  final List<SentenceSentiment> sentences;

  const SentenceListView({super.key, required this.sentences});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      itemCount: sentences.length,
      itemBuilder: (context, index) {
        final s = sentences[index];
        final color = AppTheme.sentimentColor(s.sentiment);

        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          clipBehavior: Clip.antiAlias,
          child: Container(
            decoration: BoxDecoration(
              border: Border(
                left: BorderSide(color: color, width: 4),
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      s.text,
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                  const SizedBox(width: 8),
                  SentimentBadge(
                    sentiment: s.sentiment,
                    confidence: s.confidence,
                  ),
                ],
              ),
            ),
          ),
        ).animate().fadeIn(
          duration: 300.ms,
          delay: (index * 50).ms,
        );
      },
    );
  }
}
