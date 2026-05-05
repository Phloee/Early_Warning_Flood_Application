import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

void main() {
  runApp(const JakairtaApp());
}

class JakairtaApp extends StatefulWidget {
  const JakairtaApp({Key? key}) : super(key: key);

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
    Key? key,
    required this.isDark,
    required this.onToggleTheme,
  }) : super(key: key);

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

  // Auth Controllers & State
  final TextEditingController _loginEmailCtrl = TextEditingController();
  final TextEditingController _loginPassCtrl = TextEditingController();
  final TextEditingController _regNameCtrl = TextEditingController();
  final TextEditingController _regEmailCtrl = TextEditingController();
  final TextEditingController _regPassCtrl = TextEditingController();
  bool _isAuthLoading = false;

  // CCTV & Simulasi States
  List<dynamic> _cctvList = [];
  List<dynamic> _simulasiList = [];
  bool _isLoadingMedia = false;

  // Saved Data
  List<Map<String, dynamic>> savedPlaces = [
    {"name": "Sudirman Area", "status": "Normal", "type": "safe"},
    {"name": "Office / Kemang", "status": "WARNING", "type": "warning"},
    {"name": "Parents House / Kampung Melayu", "status": "CRITICAL", "type": "critical"},
  ];

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    _splashAnimCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1000))..repeat();

    _fetchWeatherPrediction();
    _fetchCCTVAndSimulations();

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
      final String baseUrl = 'http://10.0.2.2:8080/api/auth/login/';
      final String fallbackUrl = 'http://127.0.0.1:8080/api/auth/login/';
      
      final body = json.encode({
        'email': _loginEmailCtrl.text.trim(),
        'password': _loginPassCtrl.text
      });
      
      var res = await http.post(Uri.parse(baseUrl), headers: {'Content-Type': 'application/json'}, body: body)
          .catchError((_) => http.post(Uri.parse(fallbackUrl), headers: {'Content-Type': 'application/json'}, body: body));
          
      if (res.statusCode == 200) {
        navigate('home', clearHistory: true);
      } else {
        final err = json.decode(res.body);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err['detail'] ?? 'Login failed')));
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
      final String baseUrl = 'http://10.0.2.2:8080/api/auth/register/';
      final String fallbackUrl = 'http://127.0.0.1:8080/api/auth/register/';
      
      final body = json.encode({
        'name': _regNameCtrl.text.trim(),
        'email': _regEmailCtrl.text.trim(),
        'password': _regPassCtrl.text
      });
      
      var res = await http.post(Uri.parse(baseUrl), headers: {'Content-Type': 'application/json'}, body: body)
          .catchError((_) => http.post(Uri.parse(fallbackUrl), headers: {'Content-Type': 'application/json'}, body: body));
          
      if (res.statusCode == 201) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Registration successful!')));
        navigate('login', clearHistory: true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Registration failed. Check your inputs.')));
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
      final String baseUrl = 'http://10.0.2.2:8080/api/cctv';
      final String fallbackUrl = 'http://127.0.0.1:8080/api/cctv';
      
      var cctvRes = await http.get(Uri.parse(baseUrl)).catchError((_) => http.get(Uri.parse(fallbackUrl)));
      if (cctvRes.statusCode == 200) {
        setState(() => _cctvList = json.decode(cctvRes.body));
      }

      var simRes = await http.get(Uri.parse('$baseUrl/simulations/')).catchError((_) => http.get(Uri.parse('$fallbackUrl/simulations/')));
      if (simRes.statusCode == 200) {
        setState(() => _simulasiList = json.decode(simRes.body));
      }
    } catch (e) {
      debugPrint("Gagal fetch CCTV/Simulasi: \$e");
    } finally {
      if (mounted) setState(() => _isLoadingMedia = false);
    }
  }

  Future<void> _fetchWeatherPrediction() async {
    setState(() => _isLoadingWeather = true);
    try {
      // Menggunakan 10.0.2.2 untuk Android Emulator agar bisa konek ke localhost komputer (port 8080)
      final response = await http.get(Uri.parse('http://10.0.2.2:8080/api/weather/forecast/'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          setState(() {
            _weatherForecast = data['data'];
            if (data['live_points'] != null && data['live_points'].isNotEmpty) {
              _weatherPoints = data['live_points'].join(', ');
            }
          });
        }
      } else {
        // Fallback untuk web/iOS local
        final res2 = await http.get(Uri.parse('http://127.0.0.1:8080/api/weather/forecast/'));
        if (res2.statusCode == 200) {
          final data = json.decode(res2.body);
          if (data['success'] == true) {
            setState(() {
              _weatherForecast = data['data'];
              if (data['live_points'] != null && data['live_points'].isNotEmpty) {
                _weatherPoints = data['live_points'].join(', ');
              }
            });
          }
        }
      }
    } catch (e) {
      debugPrint("Gagal fetch API prakiraan: \$e");
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
      if (loc.isNotEmpty) {
        _selectedLoc = loc;
      }
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
              GestureDetector(
                onTap: () => navigate('detail', loc: 'Kampung Melayu'),
                child: Container(
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
                            Text("Kampung Melayu", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: widget.isDark ? Colors.white : Colors.black)),
                            Text("Water level +45cm/hr", style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
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
              ),
              const SizedBox(height: 24),
              const Text("Potential Risk", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: _buildRiskCard('Kemang', 'WARNING', warningColor, "Rising Rain")),
                  const SizedBox(width: 12),
                  Expanded(child: _buildRiskCard('Kelapa Gading', 'WARNING', warningColor, "High Tide")),
                ],
              ),
              const SizedBox(height: 24),
              _buildWeatherForecastSection(),
              const SizedBox(height: 24),
              const Text("Safe Zones", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: ListTile(
                  onTap: () => navigate('detail', loc: 'Monas Area'),
                  leading: Icon(Icons.check_circle, color: safeColor, size: 36),
                  title: const Text("Monas Area", style: TextStyle(fontWeight: FontWeight.bold)),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(color: safeColor, borderRadius: BorderRadius.circular(8)),
                    child: const Text("SAFE", style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                ),
              ),
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
              child: Text(
                "Weather Forecast (${_weatherPoints.isNotEmpty ? _weatherPoints : 'Jakarta'})",
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            if (_isLoadingWeather)
              const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
          ],
        ),
        const SizedBox(height: 12),
        if (!_isLoadingWeather && _weatherForecast.isEmpty)
          const Text("No forecast data available at the moment.", style: TextStyle(color: Colors.grey)),
        if (_weatherForecast.isNotEmpty)
          SizedBox(
            height: 120,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _weatherForecast.length,
              itemBuilder: (context, index) {
                final forecast = _weatherForecast[index];
                bool isWarning = forecast['type'] == 'warning' || forecast['type'] == 'critical';
                return Container(
                  width: 100,
                  margin: const EdgeInsets.only(right: 12),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: widget.isDark ? Theme.of(context).cardColor : Colors.white,
                    border: Border.all(color: isWarning ? warningColor : (widget.isDark ? Colors.grey.shade800 : Colors.grey.shade300)),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(forecast['time'], style: const TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Icon(
                        isWarning ? Icons.thunderstorm : Icons.cloud,
                        color: isWarning ? warningColor : Colors.blue,
                        size: 28,
                      ),
                      const SizedBox(height: 8),
                      Text("${forecast['rainfall']} mm", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      Text("${forecast['temperature']}°C", style: const TextStyle(fontSize: 11, color: Colors.grey)),
                    ],
                  ),
                );
              },
            ),
          )
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
    return SingleChildScrollView(
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              const SizedBox(height: 16),
              const CircleAvatar(
                  radius: 50,
                  backgroundColor: Colors.lightBlueAccent,
                  child: Text("BS", style: TextStyle(fontSize: 32, color: Colors.white, fontWeight: FontWeight.bold))),
              const SizedBox(height: 16),
              const Text("Budi Santoso", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
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
                        value: "Budi Santoso",
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
                        value: "budi@example.com",
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
                        value: "+62 812-3456-7890",
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
                      else if (_cctvList.isEmpty && _simulasiList.isEmpty)
                        const Center(child: Text("No CCTV or Simulation available", style: TextStyle(color: Colors.grey)))
                      else
                        SizedBox(
                          height: 180,
                          child: ListView(
                            scrollDirection: Axis.horizontal,
                            children: [
                              ..._cctvList.map((cctv) {
                                bool isFlood = cctv['detection_result'] == 'flood';
                                return Container(
                                  width: 240,
                                  margin: const EdgeInsets.only(right: 12),
                                  decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(14)),
                                  clipBehavior: Clip.hardEdge,
                                  child: Stack(
                                    alignment: Alignment.center,
                                    children: [
                                      if (cctv['thumbnail_url'] != null && cctv['thumbnail_url'].toString().isNotEmpty)
                                        Image.network(cctv['thumbnail_url'], fit: BoxFit.cover, width: double.infinity, height: double.infinity, errorBuilder: (c, e, s) => const Icon(Icons.videocam_off, color: Colors.grey, size: 56))
                                      else
                                        Icon(Icons.play_circle_outline, color: Colors.white.withOpacity(0.7), size: 56),
                                        
                                      Positioned(
                                        top: 10,
                                        left: 10,
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(color: const Color(0xFFEF4444), borderRadius: BorderRadius.circular(6)),
                                          child: Row(
                                            children: [
                                              Container(width: 6, height: 6, decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle)),
                                              const SizedBox(width: 4),
                                              const Text("LIVE CCTV", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
                                            ],
                                          ),
                                        ),
                                      ),
                                      Positioned(
                                        top: 10,
                                        right: 10,
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(color: isFlood ? Colors.red : Colors.green, borderRadius: BorderRadius.circular(6)),
                                          child: Text(isFlood ? "FLOOD" : "SAFE", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
                                        ),
                                      ),
                                      Positioned(
                                        bottom: 8,
                                        left: 10,
                                        child: Text(cctv['name'] ?? "Unknown Camera", style: const TextStyle(color: Colors.white, fontSize: 12, backgroundColor: Colors.black54)),
                                      )
                                    ],
                                  ),
                                );
                              }).toList(),
                              
                              ..._simulasiList.map((sim) {
                                return Container(
                                  width: 240,
                                  margin: const EdgeInsets.only(right: 12),
                                  decoration: BoxDecoration(color: Colors.blueGrey.shade900, borderRadius: BorderRadius.circular(14)),
                                  clipBehavior: Clip.hardEdge,
                                  child: Stack(
                                    alignment: Alignment.center,
                                    children: [
                                      Icon(Icons.movie, color: Colors.white.withOpacity(0.7), size: 56),
                                      Positioned(
                                        top: 10,
                                        left: 10,
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                          decoration: BoxDecoration(color: Colors.orange, borderRadius: BorderRadius.circular(6)),
                                          child: const Text("SIMULASI", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11)),
                                        ),
                                      ),
                                      Positioned(
                                        bottom: 8,
                                        left: 10,
                                        child: Text(sim['title'] ?? "Simulasi Video", style: const TextStyle(color: Colors.white, fontSize: 12, backgroundColor: Colors.black54)),
                                      )
                                    ],
                                  ),
                                );
                              }).toList(),
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
                                  const Row(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      Text("185", style: TextStyle(color: Color(0xFFEF4444), fontSize: 42, fontWeight: FontWeight.bold)),
                                      Padding(padding: EdgeInsets.only(bottom: 6), child: Text(" cm", style: TextStyle(color: Colors.grey, fontSize: 16))),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                    decoration: BoxDecoration(color: const Color(0xFFFFEBEB), borderRadius: BorderRadius.circular(20)),
                                    child: const Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(Icons.trending_up, color: Color(0xFFEF4444), size: 14),
                                        SizedBox(width: 4),
                                        Text("SIAGA II", style: TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.bold, fontSize: 12)),
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
                                      Text("42", style: TextStyle(color: widget.isDark ? Colors.white : Colors.black, fontSize: 42, fontWeight: FontWeight.bold)),
                                      const Padding(padding: EdgeInsets.only(bottom: 6), child: Text(" mm", style: TextStyle(color: Colors.grey, fontSize: 16))),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                    decoration: BoxDecoration(color: const Color(0xFFE8F0FE), borderRadius: BorderRadius.circular(20)),
                                    child: const Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(Icons.cloud_outlined, color: Colors.blue, size: 14),
                                        SizedBox(width: 4),
                                        Text("HEAVY RAIN", style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold, fontSize: 12)),
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
                      const Text("24h Water Level Trend", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                      const SizedBox(height: 12),
                      Card(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        child: Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: SizedBox(
                            height: 150,
                            width: double.infinity,
                            child: CustomPaint(
                              painter: BarChartPainter(primaryColor, criticalColor),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
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
    List<Map<String, dynamic>> notifs = [
      {"icon": Icons.warning, "color": criticalColor, "title": "Kampung Melayu water level critical", "time": "5m ago", "lbl": "CRITICAL", "loc": "Kampung Melayu"},
      {"icon": Icons.warning_amber, "color": warningColor, "title": "High tide expected in Kelapa Gading", "time": "1h ago", "lbl": "WARNING", "loc": "Kelapa Gading"},
      {"icon": Icons.check_circle, "color": safeColor, "title": "Sudirman area cleared", "time": "3h ago", "lbl": "SAFE", "loc": "Sudirman"},
      {"icon": Icons.notifications, "color": primaryColor, "title": "Reminder: Check your saved locations", "time": "yesterday", "lbl": "INFO", "loc": ""},
    ];

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
          child: ListView.separated(
            itemCount: notifs.length,
            separatorBuilder: (c, i) => const Divider(height: 1),
            itemBuilder: (ctx, i) {
              var n = notifs[i];
              return ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                onTap: () {
                  if (n['loc'].toString().isNotEmpty) {
                    navigate('detail', loc: n['loc']);
                  }
                },
                leading: CircleAvatar(backgroundColor: (n['color'] as Color).withOpacity(0.2), child: Icon(n['icon'], color: n['color'])),
                title: Text(n['title'], style: const TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text(n['time']),
                trailing: n['lbl'] == 'INFO' ? null : Icon(Icons.circle, color: n['color'], size: 12),
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
}

class BarChartPainter extends CustomPainter {
  final Color primary;
  final Color critical;

  BarChartPainter(this.primary, this.critical);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;
    final textPainter = TextPainter(textDirection: TextDirection.ltr);

    final bars = [
      {"label": "00:00", "height": 0.3, "color": primary},
      {"label": "08:00", "height": 0.5, "color": primary},
      {"label": "16:00", "height": 0.7, "color": primary},
      {"label": "NOW", "height": 0.9, "color": critical},
    ];

    double barWidth = 40;
    double spacing = (size.width - (barWidth * 4)) / 3;

    for (int i = 0; i < bars.length; i++) {
      double x = i * (barWidth + spacing);
      double h = size.height * (bars[i]["height"] as double);
      double y = size.height - h - 20;

      paint.color = bars[i]["color"] as Color;
      canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(x, y, barWidth, h), const Radius.circular(8)), paint);

      textPainter.text = TextSpan(text: bars[i]["label"] as String, style: const TextStyle(color: Colors.grey, fontSize: 10, fontWeight: FontWeight.bold));
      textPainter.layout();
      textPainter.paint(canvas, Offset(x + (barWidth - textPainter.width) / 2, size.height - 15));
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
