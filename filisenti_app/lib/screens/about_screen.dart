import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../providers/theme_provider.dart';
import '../theme/app_theme.dart';
import '../utils/links.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('About')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Column(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: Image.asset(
                  'assets/images/logo.png',
                  width: 100,
                  height: 100,
                  fit: BoxFit.cover,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'FiliSenti',
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Sentiment Analysis for Tagalog & Hiligaynon',
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Text(
                'Version 1.0.0',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ).animate().fadeIn(duration: 400.ms),
          const SizedBox(height: 32),
          _section(
            theme,
            Icons.model_training,
            'Model',
            'XLM-RoBERTa-large fine-tuned on TagaSenti + HiliSenti\n'
            '355M parameters, INT8 quantized (ONNX)\n'
            '89.1% F1 Macro on test set',
          ),
          const SizedBox(height: 12),
          _section(
            theme,
            Icons.dataset,
            'Datasets',
            'TagaSenti: 35,686 Tagalog sentences\n'
            'HiliSenti: 21,095 Hiligaynon sentences\n'
            '56,781 total \u2014 Negative / Neutral / Positive',
          ),
          const SizedBox(height: 12),
          _section(
            theme,
            Icons.speed,
            'Performance',
            'Hiligaynon: 91.7% F1\n'
            'Tagalog: 88.1% F1\n'
            'First model combining both languages',
          ),
          const SizedBox(height: 12),
          _section(
            theme,
            Icons.person,
            'Developer',
            'Jessie James T. Jarder\n'
            'Central Philippines State University\n'
            '${AppLinks.github}',
          ),
          const SizedBox(height: 12),
          _section(
            theme,
            Icons.link,
            'Links',
            'GitHub: ${AppLinks.github}\n'
            'Hugging Face: ${AppLinks.huggingFace}\n'
            'Datasets: ${AppLinks.tagasenti} · ${AppLinks.hilisenti}',
          ),
          const SizedBox(height: 16),
          Card(
            child: Consumer<ThemeProvider>(
              builder: (context, themeProvider, _) {
                return SwitchListTile(
                  title: const Text('Dark Mode'),
                  subtitle: Text(
                    themeProvider.isDark ? 'Dark theme active' : 'Light theme active',
                  ),
                  secondary: Icon(
                    themeProvider.isDark ? Icons.dark_mode : Icons.light_mode,
                    color: AppTheme.primary,
                  ),
                  value: themeProvider.isDark,
                  onChanged: (_) => themeProvider.toggle(),
                );
              },
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Built with Flutter \u2022 ONNX Runtime \u2022 SentencePiece',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _section(ThemeData theme, IconData icon, String title, String body) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: AppTheme.primary, size: 24),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(body, style: theme.textTheme.bodyMedium),
                ],
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(duration: 300.ms).slideX(begin: 0.05);
  }
}
