import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:path_provider/path_provider.dart';
import 'services/tokenizer_service.dart';
import 'services/inference_service.dart';
import 'providers/analysis_provider.dart';
import 'providers/theme_provider.dart';
import 'theme/app_theme.dart';
import 'screens/onboarding_screen.dart';
import 'screens/home_screen.dart';
import 'screens/analysis_screen.dart';
import 'screens/results_screen.dart';
import 'screens/about_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const FiliSentiApp());
}

class FiliSentiApp extends StatefulWidget {
  const FiliSentiApp({super.key});

  @override
  State<FiliSentiApp> createState() => _FiliSentiAppState();
}

class _FiliSentiAppState extends State<FiliSentiApp> {
  final _tokenizer = TokenizerService();
  final _inference = InferenceService();
  late final _analysisProvider = AnalysisProvider(_inference);
  late final _themeProvider = ThemeProvider();
  bool _ready = false;
  bool _onboardingDone = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    if (_ready) return;

    final prefs = await SharedPreferences.getInstance();
    _onboardingDone = prefs.getBool('onboarding_done') ?? false;

    try {
      await _tokenizer.load();
    } catch (e) {
      debugPrint('Tokenizer load error: $e');
    }

    final appDir = await getApplicationDocumentsDirectory();
    final modelFile = File('${appDir.path}/filisenti_int8.onnx');
    if (await modelFile.exists()) {
      try {
        await _inference.init(_tokenizer, modelPath: modelFile.path);
      } catch (e) {
        debugPrint('Inference init error: $e');
      }
    } else {
      debugPrint('Model not found at ${modelFile.path}');
      _inference.init(_tokenizer);
    }

    await _themeProvider.init();

    if (mounted) {
      setState(() => _ready = true);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_ready) {
      return MaterialApp(
        debugShowCheckedModeBanner: false,
        home: Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.emoji_emotions,
                  size: 80,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(height: 16),
                Text(
                  'FiliSenti',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 24),
                const CircularProgressIndicator(),
              ],
            ),
          ),
        ),
      );
    }

    return MultiProvider(
      providers: [
        Provider.value(value: _tokenizer),
        ChangeNotifierProvider.value(value: _inference),
        ChangeNotifierProvider.value(value: _analysisProvider),
        ChangeNotifierProvider.value(value: _themeProvider),
      ],
      child: Consumer<ThemeProvider>(
        builder: (context, themeProvider, _) {
          return MaterialApp(
            title: 'FiliSenti',
            debugShowCheckedModeBanner: false,
            themeMode: themeProvider.themeMode,
            theme: AppTheme.light(),
            darkTheme: AppTheme.dark(),
            initialRoute: _onboardingDone ? '/home' : '/onboarding',
            routes: {
              '/onboarding': (_) => const OnboardingScreen(),
              '/home': (_) => const HomeScreen(),
              '/analysis': (_) => const AnalysisScreen(),
              '/results': (_) => const ResultsScreen(),
              '/about': (_) => const AboutScreen(),
            },
          );
        },
      ),
    );
  }
}
