import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../providers/analysis_provider.dart';
import '../services/inference_service.dart';
import '../services/tokenizer_service.dart';
import '../services/file_service.dart';
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final inference = context.watch<InferenceService>();
    final analysis = context.watch<AnalysisProvider>();

    if (!inference.isLoaded) {
      return const _ModelSetup();
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('FiliSenti'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => Navigator.pushNamed(context, '/about'),
          ),
        ],
      ),
      body: _Body(analysis: analysis),
    );
  }
}

class _ModelSetup extends StatefulWidget {
  const _ModelSetup();

  @override
  State<_ModelSetup> createState() => _ModelSetupState();
}

class _ModelSetupState extends State<_ModelSetup> {
  bool _loading = false;

  Future<void> _pickModel() async {
    try {
      setState(() => _loading = true);

      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
      );

      if (!mounted) return;

      if (result == null || result.files.isEmpty) {
        setState(() => _loading = false);
        return;
      }

      final file = File(result.files.single.path!);
      if (!await file.exists()) {
        _showError('Selected file does not exist.');
        setState(() => _loading = false);
        return;
      }

      final appDir = await getApplicationDocumentsDirectory();
      final dest = File('${appDir.path}/filisenti_int8.onnx');

      await file.copy(dest.path);

      if (!mounted) return;
      final inference = context.read<InferenceService>();
      final tokenizer = context.read<TokenizerService>();
      await inference.init(tokenizer, modelPath: dest.path);

      if (!mounted) return;
      setState(() => _loading = false);
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        _showError('Error: $e');
      }
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), duration: const Duration(seconds: 4)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('FiliSenti')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.model_training, size: 80, color: theme.colorScheme.primary),
              const SizedBox(height: 24),
              Text(
                'Model Not Found',
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Copy filisenti_int8.onnx to the app directory,\n'
                'or tap below to select the file.',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 24),
              if (_loading)
                const Column(
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 12),
                    Text('Copying and loading model...'),
                  ],
                )
              else
                FilledButton.icon(
                  onPressed: _pickModel,
                  icon: const Icon(Icons.folder_open),
                  label: const Text('Select .onnx File'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Body extends StatefulWidget {
  final AnalysisProvider analysis;

  const _Body({required this.analysis});

  @override
  State<_Body> createState() => _BodyState();
}

class _BodyState extends State<_Body> {
  final _controller = TextEditingController();
  final _fileService = FileService();
  String? _fileName;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final text = await _fileService.pickAndReadText();
    if (text != null) {
      _controller.text = text;
      setState(() {});
    } else if (text == null && _fileName == null) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('File too large or could not be read. Max 5 MB.'),
          ),
        );
      }
    }
  }

  void _analyze() {
    final text = _controller.text.trim();
    if (text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter some text or upload a file.')),
      );
      return;
    }
    widget.analysis.analyzeText(text);
    Navigator.pushNamed(context, '/analysis');
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasText = _controller.text.trim().isNotEmpty;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Paste or upload text to analyze',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            maxLines: 6,
            minLines: 4,
            decoration: InputDecoration(
              hintText: 'Paste your text here...',
              prefixIcon: const Padding(
                padding: EdgeInsets.only(top: 14),
                child: Icon(Icons.edit_note),
              ),
              alignLabelWithHint: true,
            ),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 12),
          Card(
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: _pickFile,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(Icons.upload_file, color: theme.colorScheme.primary),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Upload File',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            _fileName ?? 'TXT, MD, or CSV',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_fileName != null)
                      IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: () {
                          setState(() => _fileName = null);
                        },
                      ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: hasText ? _analyze : null,
              icon: const Icon(Icons.psychology),
              label: const Text('Analyze Text'),
            ),
          ),
          if (widget.analysis.error != null) ...[
            const SizedBox(height: 12),
            Card(
              color: theme.colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    Icon(Icons.error_outline,
                        color: theme.colorScheme.onErrorContainer),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        widget.analysis.error!,
                        style: TextStyle(
                            color: theme.colorScheme.onErrorContainer),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 24),
          Text(
            'Tagalog + Hiligaynon sentiment \u2022 On-device \u2022 No internet needed',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ).animate().fadeIn(duration: 400.ms),
    );
  }
}
