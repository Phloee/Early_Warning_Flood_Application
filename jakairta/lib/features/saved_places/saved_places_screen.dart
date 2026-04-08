import 'package:flutter/material.dart';
import '../../core/components/info_card.dart';
import '../../core/components/status_badge.dart';
import '../../core/theme/app_colors.dart';

class SavedPlacesScreen extends StatelessWidget {
  const SavedPlacesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  'Saved Places',
                  style: Theme.of(context).textTheme.displayLarge?.copyWith(fontSize: 28),
                ),
                const SizedBox(height: 24),
                // Banner (Insurance info)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.shield, color: Colors.white, size: 32),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Protect Your Assets',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Get flood insurance for your saved properties today.',
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.8),
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 16),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              children: [
                _buildSavedCard('Home', 'Sudirman Area', 'Normal', StatusType.safe),
                _buildSavedCard('Office', 'Kemang', 'Rising Water', StatusType.warning),
                _buildSavedCard('Parents House', 'Kampung Melayu', '+45cm/hr', StatusType.critical),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.add),
                  label: const Text('Add New Location'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: AppColors.primary,
                    side: const BorderSide(color: AppColors.primary),
                    padding: const EdgeInsets.all(16),
                    elevation: 0,
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSavedCard(String title, String address, String waterLevel, StatusType status) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: InfoCard(
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                ),
                StatusBadge(text: status.name.toUpperCase(), type: status),
              ],
            ),
            const Divider(height: 24),
            Row(
              children: [
                const Icon(Icons.location_on_outlined, color: AppColors.textSecondary, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    address,
                    style: const TextStyle(color: AppColors.textSecondary),
                  ),
                ),
                Row(
                  children: [
                    Icon(
                      status == StatusType.safe ? Icons.water_drop_outlined : Icons.water_drop,
                      color: status == StatusType.safe ? AppColors.safe : AppColors.critical,
                      size: 20,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      waterLevel,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                IconButton(
                  onPressed: () {},
                  icon: const Icon(Icons.edit_outlined, color: AppColors.primary),
                ),
                IconButton(
                  onPressed: () {},
                  icon: const Icon(Icons.delete_outline, color: AppColors.critical),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
