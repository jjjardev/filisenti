import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class SentimentBadge extends StatelessWidget {
  final String sentiment;
  final double confidence;

  const SentimentBadge({
    super.key,
    required this.sentiment,
    required this.confidence,
  });

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.sentimentColor(sentiment);
    final pct = (confidence * 100).toStringAsFixed(0);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            '$sentiment $pct%',
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w600,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}
