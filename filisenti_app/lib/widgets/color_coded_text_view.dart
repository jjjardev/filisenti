import 'package:flutter/material.dart';
import '../models/sentence_sentiment.dart';
import '../theme/app_theme.dart';

class ColorCodedTextView extends StatelessWidget {
  final List<SentenceSentiment> sentences;

  const ColorCodedTextView({super.key, required this.sentences});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.palette_outlined,
                size: 18, color: theme.colorScheme.onSurfaceVariant),
              const SizedBox(width: 6),
              Text(
                'Sentiment-colored highlights',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SelectableText.rich(
            TextSpan(
              children: sentences.map((s) {
                final bg = AppTheme.sentimentBg(s.sentiment);
                return TextSpan(
                  text: '${s.text} ',
                  style: TextStyle(
                    backgroundColor: bg,
                    height: 1.8,
                    color: theme.colorScheme.onSurface,
                  ),
                );
              }).toList(),
            ),
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 16,
            runSpacing: 8,
            children: ['Positive', 'Neutral', 'Negative'].map((s) {
              final color = AppTheme.sentimentColor(s);
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 12, height: 12,
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.15),
                      border: Border.all(color: color, width: 1),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(s, style: theme.textTheme.bodySmall),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}
