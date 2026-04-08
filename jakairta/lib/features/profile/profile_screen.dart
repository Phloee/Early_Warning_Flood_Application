import 'package:flutter/material.dart';
import '../../core/components/info_card.dart';
import '../../core/theme/app_colors.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
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
                    child: const Icon(Icons.person, size: 50, color: AppColors.primary),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Budi Santoso',
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
                  _buildListTile('Name', 'Budi Santoso', Icons.person_outline),
                  const Divider(height: 1),
                  _buildListTile('Email', 'budi.santoso@email.com (Verified)', Icons.email_outlined),
                  const Divider(height: 1),
                  _buildListTile('Phone', '+62 812 3456 7890', Icons.phone_outlined),
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
                  _buildListTile('Change Password', 'Last updated 3 months ago', Icons.lock_outline),
                ],
              ),
            ),
            const SizedBox(height: 32),
            // Logout
            TextButton.icon(
              onPressed: () {},
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
