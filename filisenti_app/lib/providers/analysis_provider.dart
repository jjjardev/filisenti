import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/sentence_sentiment.dart';
import '../models/analysis_result.dart';
import '../services/inference_service.dart';
import '../services/sentence_splitter_service.dart';

class AnalysisProvider extends ChangeNotifier {
  final InferenceService _inference;
  final SentenceSplitterService _splitter = SentenceSplitterService();

  AnalysisResult? _result;
  bool _isLoading = false;
  bool _isCancelled = false;
  int _processed = 0;
  int _total = 0;
  String? _error;

  AnalysisResult? get result => _result;
  bool get isLoading => _isLoading;
  int get processed => _processed;
  int get total => _total;
  String? get error => _error;
  double get progress => _total > 0 ? _processed / _total : 0.0;

  AnalysisProvider(this._inference);

  void clearResult() {
    _result = null;
    _error = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> analyzeText(String text) async {
    if (text.trim().isEmpty) {
      _error = 'Please enter some text.';
      notifyListeners();
      return;
    }

    final sentences = _splitter.split(text);
    if (sentences.isEmpty) {
      _error = 'No sentences found in the text.';
      notifyListeners();
      return;
    }

    _isLoading = true;
    _isCancelled = false;
    _processed = 0;
    _total = sentences.length;
    _result = null;
    _error = null;
    notifyListeners();

    final results = <SentenceSentiment>[];

    for (int i = 0; i < sentences.length; i++) {
      if (_isCancelled) break;

      try {
        final prediction = await _inference.predict(sentences[i]);
        if (prediction != null) {
          final (label, confidence) = prediction;
          results.add(SentenceSentiment(
            text: sentences[i],
            sentiment: label,
            confidence: confidence,
          ));
        }
      } catch (e, stack) {
        _error = 'Error at sentence ${i + 1}: $e';
        debugPrint('Error analyzing sentence $i: $e\n$stack');
        notifyListeners();
        break;
      }

      _processed = i + 1;
      notifyListeners();
    }

    _isLoading = false;

    if (!_isCancelled && results.isNotEmpty) {
      _result = AnalysisResult.fromSentences(results);
    } else if (results.isEmpty) {
      _error = 'Could not analyze any sentences. Make sure the model file is placed correctly.';
    }

    notifyListeners();
  }

  void cancel() {
    _isCancelled = true;
    _isLoading = false;
    notifyListeners();
  }
}
