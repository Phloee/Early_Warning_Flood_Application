class UserSession {
  static final UserSession _instance = UserSession._internal();
  factory UserSession() => _instance;
  UserSession._internal();

  Map<String, dynamic>? userData;
  String? token;

  bool get isLoggedIn => userData != null;

  void logout() {
    userData = null;
    token = null;
  }
}
