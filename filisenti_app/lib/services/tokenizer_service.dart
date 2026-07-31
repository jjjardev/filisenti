import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/services.dart';

class TokenizerService {
  static const int _maxLength = 128;
  static const int _padTokenId = 1;
  static const int _bosTokenId = 0;
  static const int _eosTokenId = 2;

  Map<String, int>? _vocab;
  List<String>? _idToToken;

  bool get isLoaded => _vocab != null;

  Future<void> load() async {
    final jsonStr = await rootBundle.loadString('assets/tokenizer/tokenizer.json');
    final data = json.decode(jsonStr) as Map<String, dynamic>;
    final model = data['model'] as Map<String, dynamic>;
    final vocabList = model['vocab'] as List<dynamic>;

    _vocab = {};
    _idToToken = List.filled(vocabList.length, '');

    for (int i = 0; i < vocabList.length; i++) {
      final piece = vocabList[i][0] as String;
      _vocab![piece] = i;
      _idToToken![i] = piece;
    }
  }

  static String _normalize(String s) {
    return s.toLowerCase();
  }

  List<int> _tokenizeWord(String word) {
    final pieces = <int>[];
    final text = '▁${_normalize(word)}';
    int start = 0;
    while (start < text.length) {
      int end = text.length;
      int? found;
      while (end > start) {
        final sub = text.substring(start, end);
        if (_vocab!.containsKey(sub)) {
          found = _vocab![sub];
          break;
        }
        end--;
      }
      if (found != null) {
        pieces.add(found);
        start = end;
      } else {
        pieces.add(_vocab!['<unk>']!);
        start++;
      }
    }
    return pieces;
  }

  ({Uint64List inputIds, Uint64List attentionMask, Int64List tokenized}) tokenize(
      String text) {
    final pieces = <int>[_bosTokenId];
    final words = text.trim().split(RegExp(r'\s+'));

    for (final word in words) {
      if (word.isEmpty) continue;
      final wordPieces = _tokenizeWord(word);
      if (pieces.length + wordPieces.length > _maxLength - 1) break;
      pieces.addAll(wordPieces);
    }
    pieces.add(_eosTokenId);

    final seqLen = pieces.length > _maxLength ? _maxLength : pieces.length;
    final trimmed = pieces.sublist(0, seqLen);

    final inputIds = Uint64List(_maxLength);
    final attentionMask = Uint64List(_maxLength);

    for (int i = 0; i < _maxLength; i++) {
      if (i < trimmed.length) {
        inputIds[i] = trimmed[i];
        attentionMask[i] = 1;
      } else {
        inputIds[i] = _padTokenId;
        attentionMask[i] = 0;
      }
    }

    return (
      inputIds: inputIds,
      attentionMask: attentionMask,
      tokenized: Int64List.fromList(trimmed),
    );
  }
}
