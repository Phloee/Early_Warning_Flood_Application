import 'package:flutter/material.dart';
import '../../core/components/info_card.dart';
import '../../core/theme/app_colors.dart';
import '../../core/session.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final session = UserSession();

  @override
  Widget build(BuildContext context) {
    final String name = session.userData?['name'] ?? 'Guest User';
    final String email = session.userData?['email'] ?? 'No Email';
    final String phone = session.userData?['phone'] ?? 'No Phone';
    final String initials = name.split(' ').where((e) => e.isNotEmpty).map((e) => e[0]).take(2).join().toUpperCase();

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Profile Header
            Center(
              child: Column(
                children: [
                  Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.1),
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.primary, width: 2),
                    ),
                    child: Center(
                      child: Text(
                        initials.isEmpty ? 'U' : initials,
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    name,
                    style: Theme.of(context).textTheme.displayMedium,
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.amber.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      'PLATINUM MEMBER',
                      style: TextStyle(
                        color: Colors.orange,
                        fontWeight: FontWeight.bold,
                        fontSize: 10,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.location_on, color: AppColors.textSecondary, size: 16),
                      SizedBox(width: 4),
                      Text('Jakarta Selatan', style: TextStyle(color: AppColors.textSecondary)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),
            // Personal Information
            Text(
              'Personal Information',
              style: Theme.of(context).textTheme.displayMedium?.copyWith(fontSize: 18),
            ),
            const SizedBox(height: 16),
            InfoCard(
              padding: EdgeInsets.zero,
              child: Column(
                children: [
                  _buildListTile('Name', name, Icons.person_outline),
                  const Divider(height: 1),
                  _buildListTile('Email', email, Icons.email_outlined),
                  const Divider(height: 1),
                  _buildListTile('Phone', phone, Icons.phone_outlined),
                ],
              ),
            ),
            const SizedBox(height: 32),
            // Security & Preferences
            Text(
              'Security & Preferences',
              style: Theme.of(context).textTheme.displayMedium?.copyWith(fontSize: 18),
            ),
            const SizedBox(height: 16),
            InfoCard(
              padding: EdgeInsets.zero,
              child: Column(
                children: [
                  _buildListTile('Notification Settings', 'Push, Email, SMS', Icons.notifications_active_outlined),
                  const Divider(height: 1),
                  _buildListTile('Language', 'English', Icons.language),
                  const Divider(height: 1),
                  _buildListTile('Change Password', 'Last updated recently', Icons.lock_outline),
                ],
              ),
            ),
            const SizedBox(height: 32),
            // Logout
            TextButton.icon(
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Text('Log Out'),
                    content: const Text('Are you sure you want to log out?'),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                      TextButton(
                        onPressed: () {
                          session.logout();
                          Navigator.pop(ctx);
                          // Handle navigation to login if needed
                          // Navigator.of(context).pushAndRemoveUntil(...)
                        },
                        child: const Text('Log Out', style: TextStyle(color: Colors.red)),
                      ),
                    ],
                  ),
                );
              },
              icon: const Icon(Icons.logout, color: AppColors.critical),
              label: const Text(
                'Log Out',
                style: TextStyle(color: AppColors.critical, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildListTile(String title, String subtitle, IconData icon) {
    return ListTile(
      leading: Icon(icon, color: AppColors.primary),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12)),
      trailing: const Icon(Icons.chevron_right, color: AppColors.textSecondary),
    );
  }
}
