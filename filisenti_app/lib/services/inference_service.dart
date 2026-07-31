import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:flutter_onnxruntime/flutter_onnxruntime.dart';
import 'tokenizer_service.dart';

class InferenceService extends ChangeNotifier {
  static const List<String> _labels = ['Negative', 'Neutral', 'Positive'];

  OrtSession? _session;
  late TokenizerService _tokenizer;
  bool _isLoaded = false;
  String? _error;

  bool get isLoaded => _isLoaded;
  String? get error => _error;

  Future<void> init(TokenizerService tokenizer, {String? modelPath}) async {
    _tokenizer = tokenizer;

    if (modelPath == null) {
      _isLoaded = false;
      _error = 'No model path provided.';
      notifyListeners();
      return;
    }

    try {
      debugPrint('InferenceService: creating session from $modelPath');
      final ort = OnnxRuntime();
      _session = await ort.createSession(
        modelPath,
        options: OrtSessionOptions(intraOpNumThreads: 2),
      );
      _isLoaded = true;
      _error = null;
      debugPrint('InferenceService: session created successfully');
    } catch (e) {
      debugPrint('InferenceService init error: $e');
      _isLoaded = false;
      _error = 'Failed to load model: $e';
    }
    notifyListeners();
  }

  Future<(String label, double confidence)?> predict(String text) async {
    if (!_isLoaded || _session == null) {
      debugPrint('predict called but model not loaded');
      return null;
    }

    try {
      final result = _tokenizer.tokenize(text);

      final inputIds = result.inputIds.toList();
      final attnMask = result.attentionMask.toList();

      debugPrint('predict: inputIds length=${inputIds.length}, '
          'first few=${inputIds.take(10).toList()}');

      final inputIdsTensor = await OrtValue.fromList(
        Int64List.fromList(inputIds),
        [1, inputIds.length],
      );
      final attnMaskTensor = await OrtValue.fromList(
        Int64List.fromList(attnMask),
        [1, attnMask.length],
      );

      debugPrint('predict: tensors created, running inference...');

      final outputs = await _session!.run({
        'input_ids': inputIdsTensor,
        'attention_mask': attnMaskTensor,
      }).timeout(const Duration(seconds: 30));

      debugPrint('predict: inference completed, output keys=${outputs.keys}');

      final logitsValue = outputs['logits'];
      if (logitsValue == null) {
        debugPrint('predict: no "logits" output, available: ${outputs.keys}');
        return null;
      }

      final logitsFlat = await logitsValue.asFlattenedList();
      debugPrint('predict: logits flat length=${logitsFlat.length}, '
          'type=${logitsFlat.runtimeType}, first=${logitsFlat.isNotEmpty ? logitsFlat.first : "empty"}');

      final logitRow = logitsFlat.cast<double>();
      debugPrint('predict: logitRow=$logitRow');

      final maxLogit = logitRow.reduce(max);
      final expSum = logitRow.fold<double>(
        0,
        (sum, l) => sum + exp(l - maxLogit),
      );
      final probs = logitRow.map((l) => exp(l - maxLogit) / expSum).toList();

      final predIdx = probs.indexOf(probs.reduce(max));
      debugPrint('predict: result=${_labels[predIdx]} conf=${probs[predIdx]}');
      return (_labels[predIdx], probs[predIdx]);
    } on TimeoutException {
      debugPrint('predict timed out after 30s');
      return null;
    } catch (e, stack) {
      debugPrint('predict error: $e\n$stack');
      return null;
    }
  }

  @override
  void dispose() {
    _session?.close();
    _session = null;
    _isLoaded = false;
    notifyListeners();
    super.dispose();
  }
}
