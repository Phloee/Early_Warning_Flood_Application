import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:video_player/video_player.dart';

class SimVideoPlayer extends StatefulWidget {
  final String url;
  const SimVideoPlayer({super.key, required this.url});
  @override
  State<SimVideoPlayer> createState() => _SimVideoPlayerState();
}

class _SimVideoPlayerState extends State<SimVideoPlayer> {
  late VideoPlayerController _controller;
  @override
  void initState() {
    super.initState();
    String effectiveUrl = widget.url;
    if (effectiveUrl.startsWith('http://')) {
      effectiveUrl = effectiveUrl.replaceFirst('http://', 'https://');
    }
    
    if (effectiveUrl.contains('balitower.co.id') && effectiveUrl.endsWith('embed.html')) {
      effectiveUrl = effectiveUrl.replaceAll('embed.html', 'index.m3u8');
    }

    String referer = 'https://cctv.balitower.co.id/';
    if (effectiveUrl.contains('balitower.co.id')) {
      referer = effectiveUrl.replaceAll('index.m3u8', 'embed.html');
    }
    
    _controller = VideoPlayerController.networkUrl(
      Uri.parse(effectiveUrl),
      httpHeaders: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': referer,
      },
    )..initialize().then((_) {
        if (mounted) {
          setState(() {});
          _controller.play();
          _controller.setLooping(true);
        }
      }).catchError((error) {
        debugPrint("Video error ($effectiveUrl): $error");
        if (mounted) setState(() {});
      });
  }
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
  @override
  Widget build(BuildContext context) {
    if (_controller.value.hasError) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.white, size: 30),
            const SizedBox(height: 8),
            Text("Gagal memuat stream", 
              style: TextStyle(color: Colors.white.withOpacity(0.7), fontSize: 10)),
            const SizedBox(height: 4),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              child: Text(widget.url, 
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 8)),
            ),
          ],
        ),
      );
    }
    return _controller.value.isInitialized
        ? SizedBox.expand(child: FittedBox(fit: BoxFit.cover, child: SizedBox(width: _controller.value.size.width, height: _controller.value.size.height, child: VideoPlayer(_controller))))
        : const Center(child: CircularProgressIndicator(color: Colors.white));
  }
}

void main() {
  runApp(const JakairtaApp());
}

class JakairtaApp extends StatefulWidget {
  const JakairtaApp({super.key});

  @override
  State<JakairtaApp> createState() => _JakairtaAppState();
}

class _JakairtaAppState extends State<JakairtaApp> {
  bool _isDark = false;

  void toggleTheme() {
    setState(() {
      _isDark = !_isDark;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Jakairta',
      debugShowCheckedModeBanner: false,
      themeMode: _isDark ? ThemeMode.dark : ThemeMode.light,
      theme: ThemeData(
        brightness: Brightness.light,
        primaryColor: const Color(0xFF3478F6),
        scaffoldBackgroundColor: const Color(0xFFF5F5F7),
        cardColor: Colors.white,
        colorScheme: const ColorScheme.light(
          primary: Color(0xFF3478F6),
          secondary: Color(0xFF3478F6),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFFF5F5F7),
          foregroundColor: Colors.black,
          elevation: 0,
        ),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: const Color(0xFF3478F6),
        scaffoldBackgroundColor: const Color(0xFF1C1C1E),
        cardColor: const Color(0xFF2C2C2E),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF3478F6),
          secondary: Color(0xFF3478F6),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1C1C1E),
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        useMaterial3: true,
      ),
      home: JakairtaMainContainer(
        isDark: _isDark,
        onToggleTheme: toggleTheme,
      ),
    );
  }
}

class JakairtaMainContainer extends StatefulWidget {
  final bool isDark;
  final VoidCallback onToggleTheme;

  const JakairtaMainContainer({
    super.key,
    required this.isDark,
    required this.onToggleTheme,
  });

  @override
  State<JakairtaMainContainer> createState() => _JakairtaMainContainerState();
}

class _JakairtaMainContainerState extends State<JakairtaMainContainer> with TickerProviderStateMixin {
  String _screen = 'splash';
  String _selectedLoc = '';
  final List<String> _history = [];

  // Theme Constants
  final Color primaryColor = const Color(0xFF3478F6);
  final Color safeColor = const Color(0xFF22C55E);
  final Color warningColor = const Color(0xFFF59E0B);
  final Color criticalColor = const Color(0xFFEF4444);

  // Controllers
  late AnimationController _splashAnimCtrl;
  late PageController _pageController;

  // States
  int _onboardingPage = 0;
  bool _obscureLoginPass = true;
  bool _obscureRegPass = true;
  String _searchFilter = 'All Areas';
  bool _detailBookmarked = false;
  bool _showSafetyBanner = true;

  // Profile notification states
  bool _notifPush = true;
  bool _notifEmail = false;
  bool _notifSms = true;

  // Weather States
  List<dynamic> _weatherForecast = [];
  bool _isLoadingWeather = false;
  String _weatherPoints = "";
  String _weatherGeneratedAt = "";
  String _weatherSource = "";

  // Auth Controllers & State
  final TextEditingController _loginEmailCtrl = TextEditingController();
  final TextEditingController _loginPassCtrl = TextEditingController();
  final TextEditingController _regNameCtrl = TextEditingController();
  final TextEditingController _regEmailCtrl = TextEditingController();
  final TextEditingController _regPassCtrl = TextEditingController();
  bool _isAuthLoading = false;
  Map<String, dynamic>? _userData;
  String? _authToken;

  // CCTV States
  List<dynamic> _cctvList = [];
  bool _isLoadingMedia = false;

  List<dynamic> _areasList = [];
  List<dynamic> _notifsList = [];
  int _lastNotifId = -1;
  Timer? _pollingTimer;

  Map<String, dynamic>? _liveWeather;
  bool _isLoadingLiveWeather = false;

  Future<void> _fetchLiveWeather(double lat, double lon) async {
    if (mounted) setState(() => _isLoadingLiveWeather = true);
    try {
      final res = await http.get(Uri.parse(
          'http://localhost:8080/api/weather/live/?lat=$lat&lon=$lon'));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        if (data['success'] == true && mounted) {
          setState(() => _liveWeather = data);
        }
      }
    } catch (e) {
      debugPrint('Gagal fetch live weather: $e');
    } finally {
      if (mounted) setState(() => _isLoadingLiveWeather = false);
    }
  }

  Future<void> _fetchAreasAndNotifs() async {
    try {
      var res = await http.get(Uri.parse('http://localhost:8080/api/areas/'));
      if (res.statusCode == 200) {
        final decoded = json.decode(res.body);
        if (mounted) setState(() => _areasList = decoded is Map<String, dynamic> && decoded.containsKey('results') ? decoded['results'] : decoded);
      }
    } catch(e) { debugPrint("Gagal fetch Areas: $e"); }
    
    try {
      var res = await http.get(Uri.parse('http://localhost:8080/api/notifications/'));
      if (res.statusCode == 200) {
        final decoded = json.decode(res.body);
        final List<dynamic> list = decoded is Map<String, dynamic> && decoded.containsKey('results') ? decoded['results'] : decoded;
        if (mounted) {
          // Check for new notification
          if (list.isNotEmpty) {
            final latestId = list[0]['id'] as int? ?? -1;
            if (_lastNotifId == -1) {
              // First load — just record, don't popup
              setState(() { _notifsList = list; _lastNotifId = latestId; });
            } else if (latestId > _lastNotifId) {
              // NEW notification arrived from admin!
              setState(() { _notifsList = list; _lastNotifId = latestId; });
              _showAlertDialog(list[0]);
            } else {
              setState(() => _notifsList = list);
            }
          } else {
            setState(() => _notifsList = list);
          }
        }
      }
    } catch(e) { debugPrint("Gagal fetch Notifs: $e"); }
  }

  void _showAlertDialog(Map<String, dynamic> notif) {
    final title = notif['title'] ?? '⚠️ Peringatan';
    final body  = notif['body']  ?? '';
    final areaName = notif['area_name'] ?? '';
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          constraints: const BoxConstraints(maxWidth: 400),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF7F1D1D), Color(0xFF991B1B)],
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [BoxShadow(color: Colors.red.withOpacity(0.4), blurRadius: 30, spreadRadius: 2)],
          ),
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 56, height: 56,
                decoration: BoxDecoration(color: Colors.red.withOpacity(0.3), shape: BoxShape.circle),
                child: const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 32),
              ),
              const SizedBox(height: 16),
              Text(title, textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
              if (areaName.isNotEmpty) ...[const SizedBox(height: 4),
                Text('📍 $areaName', textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.red.shade200, fontSize: 13))],
              const SizedBox(height: 12),
              Text(body, textAlign: TextAlign.center,
                style: TextStyle(color: Colors.red.shade100, fontSize: 14, height: 1.4)),
              const SizedBox(height: 24),
              SizedBox(width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: const Color(0xFF991B1B),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  onPressed: () {
                    Navigator.pop(ctx);
                    navigate('notifications');
                  },
                  child: const Text('Lihat Detail', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: Text('Tutup', style: TextStyle(color: Colors.red.shade200, fontSize: 13)),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Saved Data
  List<Map<String, dynamic>> savedPlaces = [
    {"name": "Sudirman Area", "status": "Normal", "type": "safe"},
    {"name": "Office / Kemang", "status": "WARNING", "type": "warning"},
    {"name": "Pancoran / Cikoko", "status": "CRITICAL", "type": "critical"},
  ];

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    _splashAnimCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1000))..repeat();

    _fetchWeatherPrediction();
    _fetchCCTVAndSimulations();
    _fetchAreasAndNotifs();
    _pollingTimer = Timer.periodic(const Duration(seconds: 8), (timer) {
      if (mounted) {
        _fetchAreasAndNotifs();
        _fetchCCTVAndSimulations();
      }
    });
    // Refresh weather every 30 seconds
    Timer.periodic(const Duration(seconds: 30), (timer) {
      if (mounted) _fetchWeatherPrediction();
    });

    if (_screen == 'splash') {
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted && _screen == 'splash') {
          navigate('onboarding', clearHistory: true);
        }
      });
    }
  }

  Future<void> _login() async {
    setState(() => _isAuthLoading = true);
    try {
      final String baseUrl = 'http://localhost:8080/api/auth/login/';
      
      final body = json.encode({
        'email': _loginEmailCtrl.text.trim(),
        'password': _loginPassCtrl.text
      });
      
      var res = await http.post(Uri.parse(baseUrl), headers: {'Content-Type': 'application/json'}, body: body);
          
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        setState(() {
          _userData = data['user'];
          _authToken = data['access'];
        });
        navigate('home', clearHistory: true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Login failed: ${res.body}')));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to connect to server')));
    } finally {
      if (mounted) setState(() => _isAuthLoading = false);
    }
  }

  Future<void> _register() async {
    setState(() => _isAuthLoading = true);
    try {
      final String baseUrl = 'http://localhost:8080/api/auth/register/';
      
      final body = json.encode({
        'name': _regNameCtrl.text.trim(),
        'email': _regEmailCtrl.text.trim(),
        'password': _regPassCtrl.text,
        'password_confirm': _regPassCtrl.text
      });
      
      var res = await http.post(Uri.parse(baseUrl), headers: {'Content-Type': 'application/json'}, body: body);
          
      if (res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Registration successful!')));
        navigate('login', clearHistory: true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Registration failed: ${res.body}')));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to connect to server')));
    } finally {
      if (mounted) setState(() => _isAuthLoading = false);
    }
  }

  Future<void> _fetchCCTVAndSimulations() async {
    setState(() => _isLoadingMedia = true);
    try {
      final String baseUrl = 'http://localhost:8080/api/cctv/';
      
      var cctvRes = await http.get(Uri.parse(baseUrl));
      if (cctvRes.statusCode == 200) {
        final decoded = json.decode(cctvRes.body);
        setState(() => _cctvList = decoded is Map<String, dynamic> && decoded.containsKey('results') ? decoded['results'] : decoded);
      }
    } catch (e) {
      debugPrint("Gagal fetch CCTV: $e");
    } finally {
      if (mounted) setState(() => _isLoadingMedia = false);
    }
  }

  Future<void> _fetchWeatherPrediction() async {
    setState(() => _isLoadingWeather = true);
    try {
      var response = await http.get(Uri.parse('http://localhost:8080/api/weather/forecast/'));
          
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          setState(() {
            _weatherForecast = data['data'];
            _weatherGeneratedAt = data['generated_at'] ?? '';
            _weatherSource = data['source'] ?? '';
          });
        }
      }
    } catch (e) {
      debugPrint("Gagal fetch API prakiraan: $e");
    } finally {
      setState(() => _isLoadingWeather = false);
    }
  }

  @override
  void dispose() {
    _splashAnimCtrl.dispose();
    _pageController.dispose();
    super.dispose();
  }

  void navigate(String screen, {String loc = '', bool clearHistory = false, bool replace = false}) {
    setState(() {
      if (clearHistory) {
        _history.clear();
      } else if (!replace && _screen != 'splash') {
        _history.add(_screen);
      }
      _screen = screen;
      if (loc.isNotEmpty) _selectedLoc = loc;
      // Reset live weather so fresh data loads for each area
      if (screen == 'detail') _liveWeather = null;
    });
  }

  void goBack() {
    setState(() {
      if (_history.isNotEmpty) {
        _screen = _history.removeLast();
      } else {
        _screen = 'home';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    Widget content;
    switch (_screen) {
      case 'splash':
        content = _buildSplash();
        break;
      case 'onboarding':
        content = _buildOnboarding();
        break;
      case 'login':
        content = _buildLogin();
        break;
      case 'register':
        content = _buildRegister();
        break;
      case 'home':
        content = _buildHome();
        break;
      case 'search':
        content = _buildSearch();
        break;
      case 'saved':
        content = _buildSaved();
        break;
      case 'profile':
        content = _buildProfile();
        break;
      case 'detail':
        content = _buildDetail();
        break;
      case 'notifications':
        content = _buildNotifications();
        break;
      case 'community':
        content = _buildCommunity();
        break;
      default:
        content = _buildSplash();
    }

    return Scaffold(
      body: content,
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget? _buildBottomNav() {
    final mainTabs = ['home', 'search', 'saved', 'profile'];
    if (!mainTabs.contains(_screen)) return null;

    return BottomNavigationBar(
      currentIndex: mainTabs.indexOf(_screen),
      onTap: (idx) => navigate(mainTabs[idx], clearHistory: true),
      type: BottomNavigationBarType.fixed,
      selectedItemColor: primaryColor,
      unselectedItemColor: Colors.grey,
      backgroundColor: Theme.of(context).cardColor,
      items: const [
        BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
        BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Search'),
        BottomNavigationBarItem(icon: Icon(Icons.bookmark), label: 'Saved'),
        BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
      ],
    );
  }

  // ============== SCREENS ==============

  Widget _buildSplash() {
    return Stack(
      children: [
        Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: primaryColor,
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Icon(Icons.water_drop, color: Colors.white, size: 60),
              ),
              const SizedBox(height: 24),
              const Text("Jakairta", style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text("Jakarta Flood Monitor", style: TextStyle(fontSize: 16, color: Colors.grey)),
              const SizedBox(height: 32),
              AnimatedBuilder(
                  animation: _splashAnimCtrl,
                  builder: (context, child) {
                    return Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(3, (index) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 4),
                          child: Opacity(
                            opacity: ((_splashAnimCtrl.value * 3).floor() == index) ? 1.0 : 0.3,
                            child: const CircleAvatar(radius: 5, backgroundColor: Colors.grey),
                          ),
                        );
                      }),
                    );
                  })
            ],
          ),
        ),
        Positioned(
            right: 24,
            bottom: 32,
            child: IconButton(
              icon: Icon(widget.isDark ? Icons.light_mode : Icons.dark_mode, size: 32),
              onPressed: widget.onToggleTheme,
            ))
      ],
    );
  }

  Widget _buildOnboarding() {
    return SafeArea(
      child: Column(
        children: [
          Align(
            alignment: Alignment.topRight,
            child: TextButton(
              onPressed: () => navigate('login', clearHistory: true),
              child: const Text("Skip Intro"),
            ),
          ),
          Expanded(
            child: PageView(
              controller: _pageController,
              onPageChanged: (val) => setState(() => _onboardingPage = val),
              children: [
                _buildOnboardingSlide(
                  Icons.location_city,
                  "Real-time Flood Alerts",
                  "Stay updated with real-time risk alerts and water levels.",
                  chips: ["Live CCTV", "Sensor Data", "Safe Zones"],
                ),
                _buildOnboardingSlide(
                  Icons.people,
                  "Community Awareness",
                  "Learn crucial steps to protect yourself and your family before, during, and after a flood.",
                ),
                _buildOnboardingSlide(
                  Icons.bookmark,
                  "Save Your Locations",
                  "Bookmark your home, office, or parents' house for instant personalized status updates.",
                ),
              ],
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
                3,
                (index) => Container(
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _onboardingPage == index ? primaryColor : Colors.grey,
                      ),
                    )),
          ),
          Padding(
            padding: const EdgeInsets.all(24.0),
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
                backgroundColor: primaryColor,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () {
                if (_onboardingPage < 2) {
                  _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
                } else {
                  navigate('login', clearHistory: true);
                }
              },
              child: Text(
                _onboardingPage < 2 ? "Next →" : "Dive in!",
                style: const TextStyle(color: Colors.white, fontSize: 16),
              ),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildOnboardingSlide(IconData icon, String title, String desc, {List<String>? chips}) {
    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 120, color: primaryColor),
          const SizedBox(height: 32),
          Text(title, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
          const SizedBox(height: 16),
          Text(desc, style: const TextStyle(fontSize: 16, color: Colors.grey), textAlign: TextAlign.center),
          const SizedBox(height: 24),
          if (chips != null)
            Wrap(
              spacing: 8,
              children: chips.map((c) => Chip(label: Text(c))).toList(),
            )
        ],
      ),
    );
  }

  Widget _buildLogin() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 48),
            Center(
              child: Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: primaryColor,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Icon(Icons.water_drop, color: Colors.white, size: 48),
              ),
            ),
            const SizedBox(height: 16),
            const Center(child: Text("Jakairta", style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold))),
            const SizedBox(height: 48),
            TextField(
              controller: _loginEmailCtrl,
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.email),
                labelText: "Email",
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _loginPassCtrl,
              obscureText: _obscureLoginPass,
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.lock),
                suffixIcon: IconButton(
                  icon: Icon(_obscureLoginPass ? Icons.visibility_off : Icons.visibility),
                  onPressed: () => setState(() => _obscureLoginPass = !_obscureLoginPass),
                ),
                labelText: "Password",
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Reset link sent to your email")));
                },
                child: const Text("Forgot Password?"),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: primaryColor,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: _isAuthLoading ? null : _login,
              child: _isAuthLoading
                  ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text("Dive in!", style: TextStyle(fontSize: 16, color: Colors.white, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => navigate('register'),
              child: const Text("Sign Up"),
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.fingerprint, size: 32),
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Biometric not available in demo")));
                  },
                ),
                const SizedBox(width: 16),
                IconButton(
                  icon: const Icon(Icons.face, size: 32),
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Biometric not available in demo")));
                  },
                ),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildRegister() {
    return Column(
      children: [
        AppBar(
          leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: goBack),
          title: const Text("Register"),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Chip(label: Text("Real-time Alerts")),
                    SizedBox(width: 8),
                    Chip(label: Text("Live CCTV")),
                  ],
                ),
                const SizedBox(height: 24),
                TextField(
                  controller: _regNameCtrl,
                  decoration: InputDecoration(
                    prefixIcon: const Icon(Icons.person),
                    labelText: "Full Name",
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _regEmailCtrl,
                  decoration: InputDecoration(
                    prefixIcon: const Icon(Icons.email),
                    labelText: "Email",
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _regPassCtrl,
                  obscureText: _obscureRegPass,
                  decoration: InputDecoration(
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(_obscureRegPass ? Icons.visibility_off : Icons.visibility),
                      onPressed: () => setState(() => _obscureRegPass = !_obscureRegPass),
                    ),
                    labelText: "Password",
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  decoration: InputDecoration(
                    prefixIcon: const Icon(Icons.phone),
                    labelText: "Phone (+62)",
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: primaryColor,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  onPressed: _isAuthLoading ? null : _register,
                  child: _isAuthLoading
                      ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text("Create Account", style: TextStyle(fontSize: 16, color: Colors.white, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: goBack,
                  child: const Text("Already have an account? Login"),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildHome() {
    return SingleChildScrollView(
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // HEADER
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.pin_drop, size: 16, color: primaryColor),
                          const SizedBox(width: 4),
                          Text("Jakarta Pusat", style: TextStyle(color: primaryColor, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 4),
                      const Text("Jakairta", style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  GestureDetector(
                    onTap: () => navigate('notifications'),
                    child: Stack(
                      children: [
                        Icon(Icons.notifications_outlined, size: 26, color: widget.isDark ? Colors.white : Colors.black),
                        Positioned(
                          right: 0,
                          top: 0,
                          child: Container(
                            width: 8,
                            height: 8,
                            decoration: const BoxDecoration(color: Colors.red, shape: BoxShape.circle),
                          ),
                        )
                      ],
                    ),
                  )
                ],
              ),
              const SizedBox(height: 24),
              // BANNER
              GestureDetector(
                onTap: () => navigate('community'),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1DB954),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text("Community Awareness", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                            const SizedBox(height: 4),
                            Text("Learn what to do before, during, and after a flood.", style: TextStyle(color: Colors.white.withOpacity(0.9), fontSize: 12)),
                            const SizedBox(height: 12),
                            OutlinedButton(
                              onPressed: () => navigate('community'),
                              style: OutlinedButton.styleFrom(
                                side: const BorderSide(color: Colors.white),
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ),
                              child: const Text("Learn More", style: TextStyle(color: Colors.white, fontSize: 12)),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.menu_book, color: Colors.white, size: 48),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Text("Danger Zones", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              // Danger Zone Card
              if (_areasList.where((a) => a['status'] == 'banjir').isEmpty)
                 const Padding(padding: EdgeInsets.only(bottom: 12), child: Text("Semua aman, tidak ada area kritis saat ini.", style: TextStyle(color: Colors.grey))),
              ..._areasList.where((a) => a['status'] == 'banjir').map((a) => GestureDetector(
                onTap: () => navigate('detail', loc: a['name']),
                child: Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                    border: Border.all(color: widget.isDark ? Colors.grey.shade800 : const Color(0xFFEEEEEE)),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFEBEB),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.warning_amber_rounded, color: Color(0xFFEF4444), size: 24),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(a['name'] ?? '', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: widget.isDark ? Colors.white : Colors.black)),
                            Text("Water level ${a['water_level_cm'] ?? 0} cm", style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(color: const Color(0xFFEF4444), borderRadius: BorderRadius.circular(20)),
                        child: const Text("CRITICAL", style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                ),
              )),

              const SizedBox(height: 24),
              const Text("Potential Risk", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              if (_areasList.where((a) => a['status'] == 'potensial').isEmpty)
                 const Padding(padding: EdgeInsets.only(bottom: 12), child: Text("Tidak ada wilayah dengan risiko potensial.", style: TextStyle(color: Colors.grey))),
              Row(
                children: _areasList.where((a) => a['status'] == 'potensial').take(2).map<Widget>((a) => Expanded(child: _buildRiskCard(a['name'], 'WARNING', warningColor, "Water level ${a['water_level_cm']} cm"))).toList(),
              ),
              const SizedBox(height: 24),
              _buildWeatherForecastSection(),
              const SizedBox(height: 24),
              const Text("Safe Zones", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              if (_areasList.where((a) => a['status'] == 'aman').isEmpty)
                 const Padding(padding: EdgeInsets.only(bottom: 12), child: Text("Tidak ada data wilayah aman.", style: TextStyle(color: Colors.grey))),
              ..._areasList.where((a) => a['status'] == 'aman').map((a) => Card(
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: ListTile(
                  onTap: () => navigate('detail', loc: a['name']),
                  leading: Icon(Icons.check_circle, color: safeColor, size: 36),
                  title: Text(a['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text("Water level ${a['water_level_cm'] ?? 0} cm"),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(color: safeColor, borderRadius: BorderRadius.circular(8)),
                    child: const Text("SAFE", style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                ),
              )),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildWeatherForecastSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: const Text("Cuaca di Jakarta",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            if (_isLoadingWeather)
              const SizedBox(width: 16, height: 16,
                child: CircularProgressIndicator(strokeWidth: 2)),
            if (!_isLoadingWeather)
              GestureDetector(
                onTap: () {
                  setState(() => _weatherForecast = []);
                  _fetchWeatherPrediction();
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: const Color(0xFF3478F6).withOpacity(0.12),
                    borderRadius: BorderRadius.circular(20)),
                  child: const Row(mainAxisSize: MainAxisSize.min, children: [
                    Icon(Icons.refresh, size: 13, color: Color(0xFF3478F6)),
                    SizedBox(width: 4),
                    Text("Refresh", style: TextStyle(fontSize: 11, color: Color(0xFF3478F6), fontWeight: FontWeight.w600)),
                  ]),
                ),
              ),
          ],
        ),
        const SizedBox(height: 12),
        if (!_isLoadingWeather && _weatherForecast.isEmpty)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: widget.isDark ? Colors.grey.shade800 : Colors.grey.shade200)),
            child: const Row(children: [
              Icon(Icons.cloud_off, color: Colors.grey, size: 18),
              SizedBox(width: 8),
              Text("Data cuaca belum tersedia.", style: TextStyle(color: Colors.grey, fontSize: 13)),
            ]),
          ),
        if (_weatherForecast.isNotEmpty)
          SizedBox(
            height: 178,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _weatherForecast.length,
              itemBuilder: (context, index) {
                final forecast = _weatherForecast[index];
                final type = forecast['type'] as String? ?? 'safe';
                final isCritical = type == 'critical';
                final isWarning  = type == 'warning';
                final cardColor  = isCritical
                    ? const Color(0xFFEF4444)
                    : isWarning ? Colors.orange : const Color(0xFF22C55E);
                final bgColor   = cardColor.withOpacity(0.08);
                final borderCol = cardColor.withOpacity(0.3);
                final rainfall  = forecast['rainfall'];
                final temp      = forecast['temperature'];
                final humidity  = forecast['humidity'];
                final dayLabel  = forecast['day'] as String? ?? '';
                final dateLabel = forecast['date'] as String? ?? '';
                return Container(
                  width: 116,
                  margin: const EdgeInsets.only(right: 10),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                    border: Border.all(color: borderCol, width: 1.2),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.center,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (dayLabel.isNotEmpty)
                        Text(dayLabel,
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: cardColor),
                          overflow: TextOverflow.ellipsis),
                      if (dateLabel.isNotEmpty)
                        Text(dateLabel,
                          style: const TextStyle(fontSize: 10, color: Colors.grey),
                          overflow: TextOverflow.ellipsis),
                      Text(forecast['time'] ?? '',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                        overflow: TextOverflow.ellipsis),
                      const SizedBox(height: 4),
                      Icon(
                        isCritical ? Icons.thunderstorm
                            : isWarning ? Icons.water_drop
                            : Icons.wb_sunny,
                        color: cardColor, size: 22),
                      const SizedBox(height: 4),
                      Text(
                        (rainfall as num) <= 0 ? 'Tidak ada hujan' : '$rainfall mm',
                        style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: cardColor),
                        overflow: TextOverflow.ellipsis, textAlign: TextAlign.center),
                      Text('$temp\u00b0C  ${humidity?.toInt()}%',
                        style: const TextStyle(fontSize: 9, color: Colors.grey),
                        overflow: TextOverflow.ellipsis, textAlign: TextAlign.center),
                      const SizedBox(height: 3),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                        decoration: BoxDecoration(
                          color: bgColor,
                          borderRadius: BorderRadius.circular(5)),
                        child: Text(
                          isCritical ? 'KRITIS' : isWarning ? 'SIAGA' : 'AMAN',
                          style: TextStyle(fontSize: 8, fontWeight: FontWeight.bold, color: cardColor),
                          overflow: TextOverflow.ellipsis),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        if (_weatherGeneratedAt.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Row(children: [
              Icon(Icons.update, size: 11, color: Colors.grey.shade500),
              const SizedBox(width: 4),
              Expanded(child: Text(
                '$_weatherGeneratedAt  •  ${_weatherSource == "openweather_forecast" ? "OpenWeather Forecast" : "ARIMA Fallback"}',
                style: TextStyle(fontSize: 10, color: Colors.grey.shade500),
                overflow: TextOverflow.ellipsis)),
            ]),
          ),
      ],
    );
  }

  Widget _buildRiskCard(String name, String badge, Color badgeColor, String subtitle) {
    return GestureDetector(
      onTap: () => navigate('detail', loc: name),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
          border: Border.all(color: widget.isDark ? Colors.grey.shade800 : Colors.grey.shade300, width: 0.5),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(color: const Color(0xFFFFF3CD), borderRadius: BorderRadius.circular(8)),
              child: const Text("WARNING", style: TextStyle(color: Color(0xFFB45309), fontSize: 10, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 12),
            Text(name, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: widget.isDark ? Colors.white : Colors.black)),
            const SizedBox(height: 4),
            Text(subtitle, style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
          ],
        ),
      ),
    );
  }

  Widget _buildSearch() {
    List<Map<String, dynamic>> allAreas = [
      {"name": "Kemang", "status": "Warning: High tide expected", "type": "warning"},
      {"name": "Sudirman", "status": "Safe: Normal conditions", "type": "safe"},
      {"name": "Pluit", "status": "Critical: Pumping station error", "type": "critical"},
      {"name": "Senayan", "status": "Safe: Normal conditions", "type": "safe"},
      {"name": "Tebet", "status": "Warning: Heavy rains incoming", "type": "warning"},
    ];

    List<Map<String, dynamic>> displayed = _searchFilter == 'All Areas'
        ? allAreas
        : allAreas.where((a) {
            if (_searchFilter == 'JakSel') return ['Kemang', 'Tebet'].contains(a['name']);
            if (_searchFilter == 'JakUt') return ['Pluit'].contains(a['name']);
            if (_searchFilter == 'JakBar') return false;
            if (_searchFilter == 'JakPus') return ['Sudirman', 'Senayan'].contains(a['name']);
            return false;
          }).toList();

    return SingleChildScrollView(
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 16),
              const Text("Search", style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: "Search locations...",
                        prefixIcon: const Icon(Icons.search),
                        filled: true,
                        fillColor: Theme.of(context).cardColor,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: () {
                      showModalBottomSheet(context: context, builder: (ctx) => const Padding(padding: EdgeInsets.all(24), child: Text("Filter Options Example")));
                    },
                    child: Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(color: const Color(0xFF3478F6), borderRadius: BorderRadius.circular(12)),
                      child: const Icon(Icons.tune, color: Colors.white),
                    ),
                  )
                ],
              ),
              const SizedBox(height: 16),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: ['All Areas', 'JakSel', 'JakUt', 'JakBar', 'JakPus']
                      .map((f) => Padding(
                            padding: const EdgeInsets.only(right: 8.0),
                            child: FilterChip(
                              label: Text(f),
                              selected: _searchFilter == f,
                              selectedColor: primaryColor.withOpacity(0.2),
                              onSelected: (val) => setState(() => _searchFilter = f),
                            ),
                          ))
                      .toList(),
                ),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: widget.isDark ? Colors.green.withOpacity(0.1) : const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: Colors.green, size: 18),
                    const SizedBox(width: 8),
                    Expanded(child: Text("2 areas newly marked as safe in the last hour.", style: TextStyle(color: widget.isDark ? Colors.green : const Color(0xFF2E7D32), fontSize: 13))),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: displayed.length,
                itemBuilder: (ctx, i) {
                  var a = displayed[i];
                  Color dotColor = a['type'] == 'warning' ? warningColor : a['type'] == 'critical' ? criticalColor : safeColor;
                  return GestureDetector(
                    onTap: () => navigate('detail', loc: a['name']),
                    child: Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: widget.isDark ? Colors.grey.shade800 : Colors.grey.shade300, width: 0.5),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(a['name'], style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: widget.isDark ? Colors.white : Colors.black)),
                                const SizedBox(height: 4),
                                Text(a['status'], style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
                              ],
                            ),
                          ),
                          const Icon(Icons.chevron_right, color: Colors.grey),
                        ],
                      ),
                    ),
                  );
                },
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSaved() {
    return Stack(
      children: [
        SingleChildScrollView(
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 16),
                  const Text("Saved Places", style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  GestureDetector(
                    onTap: () {
                      showModalBottomSheet(
                          context: context,
                          builder: (ctx) => Container(
                                padding: const EdgeInsets.all(24),
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.admin_panel_settings, size: 64, color: primaryColor),
                                    const SizedBox(height: 16),
                                    const Text("Flood Insurance Info", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                                    const SizedBox(height: 8),
                                    const Text("Protect your assets with our insurance partners. Contact support for more details.",
                                        textAlign: TextAlign.center),
                                    const SizedBox(height: 24),
                                    ElevatedButton(
                                      style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(50), backgroundColor: primaryColor),
                                      onPressed: () => Navigator.pop(ctx),
                                      child: const Text("Close", style: TextStyle(color: Colors.white)),
                                    )
                                  ],
                                ),
                              ));
                    },
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF3478F6),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.shield, color: Colors.white, size: 28),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text("Protect Your Assets", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
                                const SizedBox(height: 4),
                                Text("Get flood insurance for your saved properties today.", style: TextStyle(color: Colors.white.withOpacity(0.85), fontSize: 12)),
                              ],
                            )
                          ),
                          const Icon(Icons.chevron_right, color: Colors.white),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: savedPlaces.length,
                    itemBuilder: (ctx, i) {
                      var sp = savedPlaces[i];
                      Color c = sp['type'] == 'warning' ? warningColor : sp['type'] == 'critical' ? criticalColor : safeColor;
                      return Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: widget.isDark ? Colors.grey.shade800 : Colors.grey.shade300, width: 0.5),
                        ),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(child: Text(sp['name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15))),
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                      decoration: BoxDecoration(color: c, borderRadius: BorderRadius.circular(12)),
                                      child: Text((sp['status'] as String).toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                                    ),
                                    const SizedBox(width: 8),
                                    GestureDetector(
                                      onTap: () {
                                        TextEditingController tc = TextEditingController(text: sp['name']);
                                        showDialog(
                                          context: context,
                                          builder: (ctx) => AlertDialog(
                                                title: const Text("Rename"),
                                                content: TextField(controller: tc),
                                                actions: [
                                                  TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
                                                  TextButton(
                                                      onPressed: () {
                                                        setState(() {
                                                          sp['name'] = tc.text;
                                                        });
                                                        Navigator.pop(ctx);
                                                      },
                                                      child: const Text("Save")),
                                                ],
                                              ));
                                      },
                                      child: const Icon(Icons.edit, size: 18, color: Colors.grey),
                                    ),
                                    const SizedBox(width: 8),
                                    GestureDetector(
                                      onTap: () {
                                        showDialog(
                                          context: context,
                                          builder: (ctx) => AlertDialog(
                                                title: const Text("Confirm Delete"),
                                                content: const Text("Remove this saved location?"),
                                                actions: [
                                                  TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
                                                  TextButton(
                                                      onPressed: () {
                                                        setState(() {
                                                          savedPlaces.removeAt(i);
                                                        });
                                                        Navigator.pop(ctx);
                                                      },
                                                      child: const Text("Delete", style: TextStyle(color: Colors.red))),
                                                ],
                                              ));
                                      },
                                      child: const Icon(Icons.delete_outline, size: 18, color: Colors.red),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                const Icon(Icons.location_on_outlined, size: 14, color: Colors.grey),
                                const SizedBox(width: 4),
                                Expanded(child: Text("${sp['name']} Area, Jakarta", style: const TextStyle(color: Colors.grey, fontSize: 12))),
                              ],
                            ),
                            const SizedBox(height: 12),
                            const Divider(height: 1, thickness: 0.5),
                            const SizedBox(height: 12),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text("WATER LEVEL", style: TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.bold)),
                                    const SizedBox(height: 4),
                                    Text(sp['type'] == 'critical' ? "185 cm" : (sp['type'] == 'warning' ? "95 cm" : "40 cm"), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                  ],
                                ),
                                const SizedBox(width: 24),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text("STATUS", style: TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.bold)),
                                    const SizedBox(height: 4),
                                    Text((sp['status'] as String).toUpperCase(), style: TextStyle(color: c, fontWeight: FontWeight.bold, fontSize: 14)),
                                  ],
                                ),
                                const Spacer(),
                                IconButton(
                                  onPressed: () {},
                                  icon: const Icon(Icons.videocam_outlined, color: Colors.grey, size: 20),
                                  constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                                  style: IconButton.styleFrom(shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8), side: BorderSide(color: widget.isDark ? Colors.grey.shade800 : Colors.grey.shade300))),
                                ),
                                const SizedBox(width: 8),
                                IconButton(
                                  onPressed: () {},
                                  icon: const Icon(Icons.directions, color: Color(0xFF3478F6), size: 20),
                                  constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                                  style: IconButton.styleFrom(backgroundColor: const Color(0xFF3478F6).withOpacity(0.1), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
                                ),
                              ],
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 100), // padding for FAB
                ],
              ),
            ),
          ),
        ),
        Positioned(
          bottom: 16,
          right: 16,
          child: FloatingActionButton.extended(
            backgroundColor: primaryColor,
            onPressed: () {
              TextEditingController tc = TextEditingController();
              showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  builder: (ctx) => Padding(
                        padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 24, right: 24, top: 24),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text("Add New Location", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 16),
                            TextField(
                              controller: tc,
                              decoration: const InputDecoration(labelText: "Location Name", border: OutlineInputBorder()),
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton(
                              style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(50), backgroundColor: primaryColor),
                              onPressed: () {
                                if (tc.text.isNotEmpty) {
                                  setState(() => savedPlaces.add({"name": tc.text, "status": "Normal", "type": "safe"}));
                                  Navigator.pop(ctx);
                                }
                              },
                              child: const Text("Save", style: TextStyle(color: Colors.white)),
                            ),
                            const SizedBox(height: 24),
                          ],
                        ),
                      ));
            },
            icon: const Icon(Icons.add, color: Colors.white),
            label: const Text("Add New Location", style: TextStyle(color: Colors.white)),
          ),
        ),
      ],
    );
  }

  Widget _buildProfileItem({required IconData icon, required String label, required String value, required VoidCallback onTap, bool isEmail = false}) {
    return ListTile(
      onTap: onTap,
      leading: Container(
        width: 40, height: 40,
        decoration: BoxDecoration(color: widget.isDark ? const Color(0xFF3478F6).withOpacity(0.2) : const Color(0xFFE8F0FE), borderRadius: BorderRadius.circular(10)),
        child: Icon(icon, color: const Color(0xFF3478F6), size: 20),
      ),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          const SizedBox(height: 2),
          Row(
            children: [
              Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: widget.isDark ? Colors.white : Colors.black)),
              if (isEmail) ...[const SizedBox(width: 4), const Icon(Icons.verified, color: Colors.blue, size: 16)],
            ],
          )
        ],
      ),
      trailing: const Icon(Icons.chevron_right, color: Colors.grey),
    );
  }

  Widget _buildProfile() {
    final String name = _userData?['name'] ?? 'Guest User';
    final String email = _userData?['email'] ?? 'No Email';
    final String phone = _userData?['phone'] ?? 'No Phone';
    final String initials = name.split(' ').where((e) => e.isNotEmpty).map((e) => e[0]).take(2).join().toUpperCase();

    return SingleChildScrollView(
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              const SizedBox(height: 16),
              CircleAvatar(
                  radius: 50,
                  backgroundColor: Colors.lightBlueAccent,
                  child: Text(initials.isEmpty ? "U" : initials, style: const TextStyle(fontSize: 32, color: Colors.white, fontWeight: FontWeight.bold))),
              const SizedBox(height: 16),
              Text(name, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(color: warningColor.withOpacity(0.2), borderRadius: BorderRadius.circular(16)),
                child: Text("PLATINUM MEMBER", style: TextStyle(color: warningColor, fontWeight: FontWeight.bold, fontSize: 12)),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.location_on, color: primaryColor, size: 16),
                  const SizedBox(width: 4),
                  const Text("Jakarta Selatan", style: TextStyle(color: Colors.grey)),
                ],
              ),
              const SizedBox(height: 32),
              const Align(alignment: Alignment.centerLeft, child: Text("Personal Information", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18))),
              const SizedBox(height: 8),
              Card(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    children: [
                      _buildProfileItem(
                        icon: Icons.person_outline,
                        label: "FULL NAME",
                        value: name,
                        onTap: () => showDialog(
                            context: context,
                            builder: (ctx) => AlertDialog(
                                  title: const Text("Edit Name"),
                                  content: const TextField(),
                                  actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Save"))],
                                )),
                      ),
                      const Divider(height: 1),
                      _buildProfileItem(
                        icon: Icons.mail_outline,
                        label: "EMAIL ADDRESS",
                        value: email,
                        isEmail: true,
                        onTap: () => showDialog(
                            context: context,
                            builder: (ctx) => AlertDialog(
                                    title: const Text("Email"),
                                    content: const Text("Email is verified."),
                                    actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("OK"))])),
                      ),
                      const Divider(height: 1),
                      _buildProfileItem(
                        icon: Icons.smartphone,
                        label: "PHONE NUMBER",
                        value: phone,
                        onTap: () => showDialog(
                            context: context,
                            builder: (ctx) => AlertDialog(
                                  title: const Text("Edit Phone"),
                                  content: const TextField(),
                                  actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Save"))],
                                )),
                      ),
                    ],
                  )),
              const SizedBox(height: 24),
              const Align(alignment: Alignment.centerLeft, child: Text("Security & Preferences", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18))),
              const SizedBox(height: 8),
              Card(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    children: [
                      ListTile(
                        title: const Text("Notification Settings"),
                        leading: const Icon(Icons.notifications),
                        onTap: () => showModalBottomSheet(
                            context: context,
                            builder: (ctx) => StatefulBuilder(builder: (BuildContext context, StateSetter setModalState) {
                                  return Container(
                                      padding: const EdgeInsets.all(24),
                                      child: Column(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          const Text("Notification Settings", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                                          SwitchListTile(
                                              title: const Text("Push Notifications"),
                                              value: _notifPush,
                                              onChanged: (v) {
                                                setModalState(() => _notifPush = v);
                                                setState(() {});
                                              }),
                                          SwitchListTile(
                                              title: const Text("Email Notifications"),
                                              value: _notifEmail,
                                              onChanged: (v) {
                                                setModalState(() => _notifEmail = v);
                                                setState(() {});
                                              }),
                                          SwitchListTile(
                                              title: const Text("SMS Notifications"),
                                              value: _notifSms,
                                              onChanged: (v) {
                                                setModalState(() => _notifSms = v);
                                                setState(() {});
                                              }),
                                        ],
                                      ));
                                })),
                      ),
                      const Divider(height: 1),
                      ListTile(
                        title: const Text("Language"),
                        leading: const Icon(Icons.language),
                        trailing: const Text("English"),
                        onTap: () => showDialog(
                            context: context,
                            builder: (ctx) => AlertDialog(
                                  title: const Text("Select Language"),
                                  content: Column(mainAxisSize: MainAxisSize.min, children: [
                                    ListTile(title: const Text("English"), onTap: () => Navigator.pop(ctx)),
                                    ListTile(title: const Text("Bahasa Indonesia"), onTap: () => Navigator.pop(ctx)),
                                  ]),
                                )),
                      ),
                      const Divider(height: 1),
                      ListTile(
                        title: const Text("Change Password"),
                        leading: const Icon(Icons.lock),
                        onTap: () => showDialog(
                            context: context,
                            builder: (ctx) => AlertDialog(
                                    title: const Text("Change Password"),
                                    content: const Column(mainAxisSize: MainAxisSize.min, children: [
                                      TextField(decoration: InputDecoration(labelText: "Old Password"), obscureText: true),
                                      TextField(decoration: InputDecoration(labelText: "New Password"), obscureText: true),
                                      TextField(decoration: InputDecoration(labelText: "Confirm Password"), obscureText: true),
                                    ]),
                                    actions: [
                                      TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
                                      TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Save"))
                                    ])),
                      ),
                      const Divider(height: 1),
                      ListTile(
                        title: const Text("Dark Mode"),
                        leading: const Icon(Icons.dark_mode),
                        trailing: Switch(value: widget.isDark, onChanged: (v) => widget.onToggleTheme()),
                      )
                    ],
                  )),
              const SizedBox(height: 24),
              TextButton(
                onPressed: () => showDialog(
                    context: context,
                    builder: (ctx) => AlertDialog(
                            title: const Text("Confirm Log Out"),
                            content: const Text("Are you sure you want to log out?"),
                            actions: [
                              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
                              TextButton(
                                  onPressed: () {
                                    Navigator.pop(ctx);
                                    setState(() {
                                      _userData = null;
                                      _authToken = null;
                                    });
                                    navigate('login', clearHistory: true);
                                  },
                                  child: const Text("Log Out", style: TextStyle(color: Colors.red))),
                            ])),
                child: const Text("Log Out", style: TextStyle(color: Colors.red, fontSize: 16, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(height: 48),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetail() {
    var areaData = _areasList.firstWhere((a) => a['name'] == _selectedLoc, orElse: () => null);
    double waterLevel = areaData != null ? (areaData['water_level_cm'] as num).toDouble() : 0.0;
    String areaStatus = areaData != null ? areaData['status'] : "aman";
    String wlColor = areaStatus == 'banjir' ? "critical" : (areaStatus == 'potensial' ? "warning" : "safe");
    Color statusColor = wlColor == 'critical' ? const Color(0xFFEF4444) : (wlColor == 'warning' ? Colors.orange : const Color(0xFF1DB954));
    
    // Improved SIAGA mapping
    String siagaLevel = "NORMAL";
    if (areaStatus == 'banjir') {
      siagaLevel = waterLevel > 200 ? "SIAGA I" : "SIAGA II";
    } else if (areaStatus == 'potensial') {
      siagaLevel = "SIAGA III";
    } else {
      siagaLevel = "SIAGA IV";
    }

    double rainfall = 0.0;
    String weatherStatus = "NORMAL";
    Color weatherColor = Colors.blue;
    if (_weatherForecast.isNotEmpty) {
      rainfall = (_weatherForecast[0]['rainfall'] as num).toDouble();
      weatherStatus = (_weatherForecast[0]['status'] as String).toUpperCase();
      if (weatherStatus.contains("CRITICAL")) {
        weatherColor = Colors.red;
      } else if (weatherStatus.contains("WARNING")) weatherColor = Colors.orange;
    }

    // Auto-fetch live weather when detail opens
    if (areaData != null && _liveWeather == null && !_isLoadingLiveWeather) {
      final lat = double.tryParse(areaData['latitude'].toString()) ?? -6.2297;
      final lon = double.tryParse(areaData['longitude'].toString()) ?? 106.8599;
      Future.microtask(() => _fetchLiveWeather(lat, lon));
    }

    return Column(
      children: [
        AppBar(
          leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: goBack),
          title: Text(_selectedLoc.isEmpty ? "Location Detail" : _selectedLoc),
          actions: [
            Container(
              margin: const EdgeInsets.only(right: 16),
              alignment: Alignment.center,
              child: ElevatedButton.icon(
                icon: Icon(_detailBookmarked ? Icons.bookmark : Icons.bookmark_border, size: 16),
                label: Text(_detailBookmarked ? "Saved" : "Save"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _detailBookmarked ? const Color(0xFF3478F6) : (widget.isDark ? Theme.of(context).cardColor : Colors.white),
                  foregroundColor: _detailBookmarked ? Colors.white : const Color(0xFF3478F6),
                  side: const BorderSide(color: Color(0xFF3478F6)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  elevation: 0,
                ),
                onPressed: () => setState(() => _detailBookmarked = !_detailBookmarked),
              ),
            )
          ],
        ),
        Expanded(
          child: SingleChildScrollView(
            child: Column(
              children: [
                if (_showSafetyBanner)
                  Container(
                    margin: const EdgeInsets.only(bottom: 16),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    decoration: const BoxDecoration(color: Color(0xFF1DB954)),
                    child: Row(
                      children: [
                        Container(
                          width: 36, height: 36,
                          decoration: BoxDecoration(color: Colors.white.withOpacity(0.2), borderRadius: BorderRadius.circular(8)),
                          child: const Icon(Icons.campaign, color: Colors.white, size: 20),
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text("PUBLIC SAFETY ANNOUNCEMENT", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
                              SizedBox(height: 2),
                              Text("Stay alert: High tide expected at 22:00 WIB.", style: TextStyle(color: Colors.white, fontSize: 13)),
                            ],
                          ),
                        ),
                        IconButton(icon: const Icon(Icons.close, color: Colors.white), onPressed: () => setState(() => _showSafetyBanner = false), padding: EdgeInsets.zero, constraints: const BoxConstraints())
                      ],
                    ),
                  ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (_isLoadingMedia)
                        const Center(child: CircularProgressIndicator())
                      else if (_cctvList.where((c) => c['area_name'] == _selectedLoc).isEmpty)
                        const Center(child: Text("No CCTV available for this area", style: TextStyle(color: Colors.grey)))
                      else
                        SizedBox(
                          height: 180,
                          child: ListView(
                            scrollDirection: Axis.horizontal,
                            children: [
                              ..._cctvList.where((c) => c['area_name'] == _selectedLoc).map((cctv) {
                                bool isFlood = cctv['detection_result'] == 'flood';
                                final streamUrl = cctv['stream_url'] as String? ?? '';
                                return GestureDetector(
                                  onTap: () {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(content: Text('CCTV URL: $streamUrl')),
                                    );
                                  },
                                  child: Container(
                                    width: 240,
                                    margin: const EdgeInsets.only(right: 12),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF111111),
                                      borderRadius: BorderRadius.circular(14),
                                      border: Border.all(color: isFlood ? Colors.red : Colors.green, width: 1.5),
                                    ),
                                    clipBehavior: Clip.hardEdge,
                                    child: Stack(
                                      children: [
                                        Positioned.fill(
                                          child: streamUrl.isNotEmpty
                                              ? SimVideoPlayer(url: streamUrl)
                                              : Column(
                                                  mainAxisAlignment: MainAxisAlignment.center,
                                                  children: [
                                                    const Icon(Icons.videocam_off, color: Colors.grey, size: 36),
                                                    const SizedBox(height: 6),
                                                    const Text('Tidak ada\nstream URL',
                                                        textAlign: TextAlign.center,
                                                        style: TextStyle(color: Colors.grey, fontSize: 11)),
                                                  ],
                                                ),
                                        ),
                                        Positioned(
                                          top: 8, left: 8,
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                                            decoration: BoxDecoration(
                                              color: const Color(0xFFEF4444),
                                              borderRadius: BorderRadius.circular(6)),
                                            child: const Row(mainAxisSize: MainAxisSize.min, children: [
                                              Icon(Icons.circle, color: Colors.white, size: 6),
                                              SizedBox(width: 4),
                                              Text('LIVE CCTV', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 10)),
                                            ]),
                                          ),
                                        ),
                                        Positioned(
                                          top: 8, right: 8,
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                                            decoration: BoxDecoration(
                                              color: isFlood ? Colors.red : Colors.green,
                                              borderRadius: BorderRadius.circular(6)),
                                            child: Text(isFlood ? 'FLOOD' : 'SAFE',
                                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 10)),
                                          ),
                                        ),
                                        Positioned(
                                          bottom: 0, left: 0, right: 0,
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                            color: Colors.black54,
                                            child: Text(cctv['name'] ?? '',
                                              overflow: TextOverflow.ellipsis,
                                              style: const TextStyle(color: Colors.white, fontSize: 11)),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                );
                              }),
                            ],
                          ),
                        ),
                      const SizedBox(height: 24),
                      Row(
                        children: [
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: widget.isDark ? Colors.grey.shade800 : Colors.grey.shade300, width: 0.5),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text("WATER LEVEL", style: TextStyle(fontSize: 11, color: Colors.grey, fontWeight: FontWeight.bold)),
                                  const SizedBox(height: 6),
                                  Row(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      Text("${waterLevel.toInt()}", style: TextStyle(color: statusColor, fontSize: 42, fontWeight: FontWeight.bold)),
                                      const Padding(padding: EdgeInsets.only(bottom: 6), child: Text(" cm", style: TextStyle(color: Colors.grey, fontSize: 16))),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                    decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(20)),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(Icons.trending_up, color: statusColor, size: 14),
                                        const SizedBox(width: 4),
                                        Text(siagaLevel, style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12)),
                                      ],
                                    ),
                                  )
                                ],
                              )
                            )
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: widget.isDark ? Colors.grey.shade800 : Colors.grey.shade300, width: 0.5),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text("RAINFALL", style: TextStyle(fontSize: 11, color: Colors.grey, fontWeight: FontWeight.bold)),
                                  const SizedBox(height: 6),
                                  Row(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      Text("${rainfall.toInt()}", style: TextStyle(color: widget.isDark ? Colors.white : Colors.black, fontSize: 42, fontWeight: FontWeight.bold)),
                                      const Padding(padding: EdgeInsets.only(bottom: 6), child: Text(" mm", style: TextStyle(color: Colors.grey, fontSize: 16))),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                    decoration: BoxDecoration(color: weatherColor.withOpacity(0.1), borderRadius: BorderRadius.circular(20)),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(Icons.cloud_outlined, color: weatherColor, size: 14),
                                        const SizedBox(width: 4),
                                        Expanded(child: Text(weatherStatus.split(':').last.trim(), overflow: TextOverflow.ellipsis, style: TextStyle(color: weatherColor, fontWeight: FontWeight.bold, fontSize: 10))),
                                      ],
                                    ),
                                  )
                                ],
                              )
                            )
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // ── Live Weather Cards ──
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Cuaca Real-time', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          if (_isLoadingLiveWeather)
                            const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                          else
                            GestureDetector(
                              onTap: () {
                                if (areaData != null) {
                                  final lat = double.tryParse(areaData['latitude'].toString()) ?? -6.2297;
                                  final lon = double.tryParse(areaData['longitude'].toString()) ?? 106.8599;
                                  setState(() => _liveWeather = null);
                                  _fetchLiveWeather(lat, lon);
                                }
                              },
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF3478F6).withOpacity(0.12),
                                  borderRadius: BorderRadius.circular(20)),
                                child: const Row(mainAxisSize: MainAxisSize.min, children: [
                                  Icon(Icons.refresh, size: 12, color: Color(0xFF3478F6)),
                                  SizedBox(width: 4),
                                  Text('Refresh', style: TextStyle(fontSize: 10, color: Color(0xFF3478F6), fontWeight: FontWeight.w600)),
                                ]),
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      if (_liveWeather == null && !_isLoadingLiveWeather)
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.grey.shade300)),
                          child: const Row(children: [
                            Icon(Icons.cloud_off, color: Colors.grey),
                            SizedBox(width: 8),
                            Text('Data cuaca belum tersedia', style: TextStyle(color: Colors.grey)),
                          ]),
                        )
                      else if (_liveWeather != null) ...[
                        Builder(builder: (ctx) {
                          final rLabel = _liveWeather!['flood_risk_label'] as String? ?? '-';
                          final rColorStr = _liveWeather!['flood_risk_color'] as String? ?? 'green';
                          final rScore = _liveWeather!['flood_risk_score'] as int? ?? 0;
                          final rColor = rColorStr == 'red' ? Colors.red : rColorStr == 'orange' ? Colors.orange : const Color(0xFF22C55E);
                          return Container(
                            width: double.infinity,
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            decoration: BoxDecoration(
                              color: rColor.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: rColor.withOpacity(0.3))),
                            child: Row(children: [
                              Icon(rColorStr == 'red' ? Icons.warning_amber_rounded : rColorStr == 'orange' ? Icons.info_outline : Icons.check_circle_outline, color: rColor, size: 22),
                              const SizedBox(width: 10),
                              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                Text('RISIKO BANJIR: $rLabel', style: TextStyle(color: rColor, fontWeight: FontWeight.bold, fontSize: 13)),
                                Text('Skor: $rScore / 100', style: TextStyle(color: rColor.withOpacity(0.7), fontSize: 11)),
                              ]),
                            ]),
                          );
                        }),
                        const SizedBox(height: 10),
                        GridView.count(
                          crossAxisCount: 2,
                          crossAxisSpacing: 10, mainAxisSpacing: 10,
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          childAspectRatio: 2.2,
                          children: [
                            _weatherTile(Icons.thermostat, 'Suhu', '${_liveWeather!["temperature"]}°C', Colors.orange, sub: '${_liveWeather!["description"]}'),
                            _weatherTile(Icons.water_drop, 'Kelembaban', '${_liveWeather!["humidity"]}%', (_liveWeather!['humidity'] as int? ?? 0) >= 85 ? Colors.red : Colors.blue),
                            _weatherTile(Icons.grain, 'Hujan 1j',
                              (_liveWeather!['rain_1h'] as num? ?? 0) <= 0
                                ? 'Tidak ada hujan'
                                : '${(_liveWeather!["rain_1h"] as num).toStringAsFixed(1)} mm',
                              (_liveWeather!['rain_1h'] as num? ?? 0) >= 10 ? Colors.red
                                : (_liveWeather!['rain_1h'] as num? ?? 0) > 0 ? Colors.orange
                                : Colors.green),
                            _weatherTile(Icons.air, 'Angin', '${_liveWeather!["wind_speed"]} km/h', (_liveWeather!['wind_speed'] as num? ?? 0) >= 30 ? Colors.red : Colors.blueGrey),
                            _weatherTile(Icons.compress, 'Tekanan', '${_liveWeather!["pressure"]} hPa', (_liveWeather!['pressure'] as int? ?? 1013) < 1005 ? Colors.orange : Colors.teal),
                            _weatherTile(Icons.cloud, 'Awan', '${_liveWeather!["cloud_pct"]}%', (_liveWeather!['cloud_pct'] as int? ?? 0) >= 80 ? Colors.blueGrey : Colors.lightBlue),
                            _weatherTile(Icons.visibility, 'Visibilitas', '${_liveWeather!["visibility_km"]} km', (_liveWeather!['visibility_km'] as num? ?? 10) < 2 ? Colors.red : Colors.indigo),
                            _weatherTile(Icons.water, 'Hujan 3j',
                              (_liveWeather!['rain_3h'] as num? ?? 0) <= 0
                                ? 'Tidak ada hujan'
                                : '${(_liveWeather!["rain_3h"] as num).toStringAsFixed(1)} mm',
                              (_liveWeather!['rain_3h'] as num? ?? 0) >= 20 ? Colors.red : Colors.cyan),
                          ],
                        ),
                      ],
                      const SizedBox(height: 24),
                      if (_weatherForecast.isNotEmpty) ...[
                        const Text("Rainfall Trend (Next 12h)", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        const SizedBox(height: 12),
                        Container(
                          height: 160,
                          width: double.infinity,
                          padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
                          decoration: BoxDecoration(
                            color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: widget.isDark ? Colors.grey.shade800 : Colors.grey.shade300, width: 0.5),
                          ),
                          child: CustomPaint(
                            painter: BarChartPainter(primaryColor, criticalColor, _weatherForecast),
                          ),
                        ),
                        const SizedBox(height: 24),
                      ],
                      const Text("Nearby Safe Zones", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                      const SizedBox(height: 12),
                      ListTile(
                        leading: Icon(Icons.check_circle, color: safeColor),
                        title: const Text("Monas Area"),
                        trailing: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(color: safeColor, borderRadius: BorderRadius.circular(8)),
                            child: const Text("SAFE", style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold))),
                        onTap: () => navigate('detail', loc: 'Monas Area'),
                      ),
                      ListTile(
                        leading: Icon(Icons.check_circle, color: safeColor),
                        title: const Text("Istora Mandiri"),
                        trailing: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(color: safeColor, borderRadius: BorderRadius.circular(8)),
                            child: const Text("SAFE", style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold))),
                        onTap: () => navigate('detail', loc: 'Istora Mandiri'),
                      ),
                      const SizedBox(height: 32),
                    ],
                  ),
                )
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildNotifications() {
    return Column(
      children: [
        AppBar(
          leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: goBack),
          title: const Text("Notifications"),
          actions: [
            TextButton(
                onPressed: () {},
                child: Text("Mark all read", style: TextStyle(color: primaryColor)))
          ],
        ),
        Expanded(
          child: _notifsList.isEmpty 
          ? const Center(child: Text("Tidak ada notifikasi", style: TextStyle(color: Colors.grey)))
          : ListView.separated(
            itemCount: _notifsList.length,
            separatorBuilder: (c, i) => const Divider(height: 1),
            itemBuilder: (ctx, i) {
              var n = _notifsList[i];
              return ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                onTap: () {
                  if (n['area_name'] != null) navigate('detail', loc: n['area_name']);
                },
                leading: CircleAvatar(backgroundColor: criticalColor.withOpacity(0.2), child: Icon(Icons.warning, color: criticalColor)),
                title: Text(n['title'] ?? 'Alert', style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text(n['body'] ?? ''),
                trailing: Icon(Icons.circle, color: criticalColor, size: 12),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildCommunity() {
    return Column(
      children: [
        AppBar(
          leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: goBack),
          title: const Text("Community Awareness"),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ExpansionTile(
                  title: const Text("Before a Flood", style: TextStyle(fontWeight: FontWeight.bold)),
                  leading: const Icon(Icons.cloud_queue),
                  children: const [
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Prepare an emergency kit with food, water, and meds.")),
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Know your evacuation routes and safe zones.")),
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Move valuables and furniture to upper floors.")),
                  ],
                ),
                ExpansionTile(
                  title: const Text("During a Flood", style: TextStyle(fontWeight: FontWeight.bold)),
                  leading: const Icon(Icons.water),
                  children: const [
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Stay calm and monitor live updates on Jakairta.")),
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Avoid walking or driving through floodwater.")),
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Evacuate immediately to nearby safe zones if instructed.")),
                  ],
                ),
                ExpansionTile(
                  title: const Text("After a Flood", style: TextStyle(fontWeight: FontWeight.bold)),
                  leading: const Icon(Icons.home_repair_service),
                  children: const [
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Check for structural damage before entering homes.")),
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Boil drinking water or use bottled water.")),
                    ListTile(leading: Icon(Icons.check, size: 16), title: Text("Report severe damages or needed rescues to authorities.")),
                  ],
                ),
                const SizedBox(height: 32),
                const Text("Emergency Contacts", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                Card(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  child: Column(
                    children: [
                      ListTile(
                          leading: const Icon(Icons.phone, color: Colors.blue),
                          title: const Text("BPBD DKI Jakarta"),
                          trailing: const Text("112", style: TextStyle(fontWeight: FontWeight.bold)),
                          onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Call feature not available in demo")))),
                      const Divider(height: 1),
                      ListTile(
                          leading: const Icon(Icons.phone, color: Colors.red),
                          title: const Text("PMI (Red Cross)"),
                          trailing: const Text("021-7992325", style: TextStyle(fontWeight: FontWeight.bold)),
                          onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Call feature not available in demo")))),
                      const Divider(height: 1),
                      ListTile(
                          leading: const Icon(Icons.phone, color: Colors.orange),
                          title: const Text("Basarnas"),
                          trailing: const Text("115", style: TextStyle(fontWeight: FontWeight.bold)),
                          onTap: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Call feature not available in demo")))),
                    ],
                  ),
                )
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _weatherTile(IconData icon, String label, String value, Color color, {String? sub}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.07),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(label, style: TextStyle(fontSize: 10, color: color.withOpacity(0.8), fontWeight: FontWeight.w600)),
                Text(value, style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color), overflow: TextOverflow.ellipsis),
                if (sub != null && sub.isNotEmpty)
                  Text(sub, style: const TextStyle(fontSize: 9, color: Colors.grey), overflow: TextOverflow.ellipsis, maxLines: 1),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class BarChartPainter extends CustomPainter {
  final Color primary;
  final Color critical;
  final List<dynamic> forecastData;

  BarChartPainter(this.primary, this.critical, this.forecastData);

  @override
  void paint(Canvas canvas, Size size) {
    if (forecastData.isEmpty) return;

    final paint = Paint()..style = PaintingStyle.fill;
    final textPainter = TextPainter(textDirection: TextDirection.ltr);

    // Filter only 4 items for the chart to keep it clean
    final displayItems = forecastData.take(4).toList();
    
    double barWidth = 40;
    double spacing = (size.width - (barWidth * displayItems.length)) / (displayItems.length - 1);
    
    // Find max rainfall for scaling
    double maxRain = 1.0;
    for (var item in displayItems) {
      double r = (item['rainfall'] as num).toDouble();
      if (r > maxRain) maxRain = r;
    }

    for (int i = 0; i < displayItems.length; i++) {
      final item = displayItems[i];
      double x = i * (barWidth + spacing);
      
      double rainfallValue = (item['rainfall'] as num).toDouble();
      // Calculate height ratio (min 0.1 for visibility if 0)
      double heightRatio = maxRain > 0 ? (rainfallValue / maxRain) : 0.1;
      if (heightRatio < 0.1) heightRatio = 0.1;
      
      double h = (size.height - 30) * heightRatio;
      double y = size.height - h - 20;

      final type = item['type'] as String? ?? 'safe';
      paint.color = type == 'critical' ? critical : (type == 'warning' ? Colors.orange : primary);
      
      canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x, y, barWidth, h), const Radius.circular(8)), paint);

      // Label (Time)
      textPainter.text = TextSpan(
        text: item['time'] ?? '', 
        style: const TextStyle(color: Colors.grey, fontSize: 10, fontWeight: FontWeight.bold)
      );
      textPainter.layout();
      textPainter.paint(canvas, Offset(x + (barWidth - textPainter.width) / 2, size.height - 15));
      
      // Value (mm)
      textPainter.text = TextSpan(
        text: "${rainfallValue.toStringAsFixed(1)}", 
        style: TextStyle(color: paint.color, fontSize: 9, fontWeight: FontWeight.bold)
      );
      textPainter.layout();
      textPainter.paint(canvas, Offset(x + (barWidth - textPainter.width) / 2, y - 15));
    }
  }

  @override
  bool shouldRepaint(covariant BarChartPainter oldDelegate) => oldDelegate.forecastData != forecastData;
}
