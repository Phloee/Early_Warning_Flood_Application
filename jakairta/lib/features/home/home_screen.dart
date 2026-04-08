import 'package:flutter/material.dart';
import '../../core/components/info_card.dart';
import '../../core/components/status_badge.dart';
import '../../core/theme/app_colors.dart';
import '../location_detail/location_detail_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.location_on, size: 16, color: AppColors.primary),
                        const SizedBox(width: 4),
                        Text(
                          'Jakarta Pusat',
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.primary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Jakairta',
                      style: Theme.of(context).textTheme.displayMedium,
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 10,
                      )
                    ],
                  ),
                  child: const Badge(
                    child: Icon(Icons.notifications_outlined),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            // Banner
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.secondary,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Community Awareness',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Learn what to do before, during, and after a flood.',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.9),
                            fontSize: 12,
                          ),
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () {},
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white,
                            foregroundColor: AppColors.secondary,
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            minimumSize: Size.zero,
                          ),
                          child: const Text('Learn More', style: TextStyle(fontSize: 12)),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Icon(Icons.menu_book, size: 64, color: Colors.white),
                ],
              ),
            ),
            const SizedBox(height: 32),
            // Danger Zones
            _buildSectionTitle('Danger Zones', context),
            const SizedBox(height: 16),
            InfoCard(
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const LocationDetailScreen()),
                );
              },
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.critical.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.warning, color: AppColors.critical),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Kampung Melayu',
                          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Water level +45cm/hr',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                      ],
                    ),
                  ),
                  const StatusBadge(text: 'CRITICAL', type: StatusType.critical),
                ],
              ),
            ),
            const SizedBox(height: 32),
            // Potential Risk
            _buildSectionTitle('Potential Risk', context),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(child: _buildRiskCard('Kemang', 'Rising Rain', StatusType.warning, context)),
                const SizedBox(width: 16),
                Expanded(child: _buildRiskCard('Kelapa Gading', 'High Tide', StatusType.warning, context)),
              ],
            ),
            const SizedBox(height: 32),
            // Safe Zones
            _buildSectionTitle('Safe Zones', context),
            const SizedBox(height: 16),
            InfoCard(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.safe.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.check_circle, color: AppColors.safe),
                      ),
                      const SizedBox(width: 16),
                      Text(
                        'Monas Area',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const StatusBadge(text: 'SAFE', type: StatusType.safe),
                ],
              ),
            ),
            const SizedBox(height: 24), // padding for bottom nav
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title, BuildContext context) {
    return Text(
      title,
      style: Theme.of(context).textTheme.displayMedium?.copyWith(
        fontSize: 20,
      ),
    );
  }

  Widget _buildRiskCard(String title, String subtitle, StatusType status, BuildContext context) {
    return InfoCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          StatusBadge(text: 'WARNING', type: status),
          const SizedBox(height: 12),
          Text(
            title,
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}
