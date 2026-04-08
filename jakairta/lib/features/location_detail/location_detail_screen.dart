import 'package:flutter/material.dart';
import '../../core/components/info_card.dart';
import '../../core/theme/app_colors.dart';

class LocationDetailScreen extends StatelessWidget {
  const LocationDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Top Alert Banner
              Container(
                color: AppColors.critical,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                child: SafeArea(
                  bottom: false,
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: Colors.white),
                      const SizedBox(width: 8),
                      const Expanded(
                        child: Text(
                          'EVACUATION RECOMMENDED. SIAGA I STATUS.',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                      IconButton(
                        onPressed: () {},
                        icon: const Icon(Icons.close, color: Colors.white),
                      )
                    ],
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // App Bar equivalent
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        IconButton(
                          padding: EdgeInsets.zero,
                          alignment: Alignment.centerLeft,
                          icon: const Icon(Icons.arrow_back),
                          onPressed: () => Navigator.of(context).pop(),
                        ),
                        Text(
                          'Kampung Melayu',
                          style: Theme.of(context).textTheme.displayMedium?.copyWith(
                            fontSize: 20,
                          ),
                        ),
                        IconButton(
                          padding: EdgeInsets.zero,
                          alignment: Alignment.centerRight,
                          icon: const Icon(Icons.bookmark_outline),
                          onPressed: () {},
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    // Video Card Feed
                    ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      child: Container(
                        height: 200,
                        color: Colors.grey.shade900,
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            const Positioned(
                              top: 16,
                              left: 16,
                              child: Row(
                                children: [
                                  Icon(Icons.circle, color: Colors.red, size: 12),
                                  SizedBox(width: 8),
                                  Text(
                                    'LIVE FEED',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.5),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.play_arrow, color: Colors.white, size: 40),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    // Stats Cards side by side
                    Row(
                      children: [
                        Expanded(
                          child: InfoCard(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Water Level',
                                  style: Theme.of(context).textTheme.bodyMedium,
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '185 cm',
                                  style: Theme.of(context).textTheme.displayMedium,
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    const Icon(Icons.arrow_upward, color: AppColors.critical, size: 12),
                                    const SizedBox(width: 4),
                                    Text(
                                      'SIAGA II',
                                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                        color: AppColors.critical,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: InfoCard(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Rainfall',
                                  style: Theme.of(context).textTheme.bodyMedium,
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  '42 mm',
                                  style: Theme.of(context).textTheme.displayMedium,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'HEAVY RAIN',
                                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                    color: AppColors.primary,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 32),
                    // Trend Chart Title
                    Text(
                      '24h Trend',
                      style: Theme.of(context).textTheme.displayMedium?.copyWith(
                        fontSize: 18,
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Mock Bar Chart
                    InfoCard(
                      child: SizedBox(
                        height: 150,
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            _buildBar(40),
                            _buildBar(60),
                            _buildBar(80),
                            _buildBar(110),
                            _buildBar(140),
                            _buildBar(185, isCritical: true),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBar(double height, {bool isCritical = false}) {
    return Container(
      width: 24,
      height: height,
      decoration: BoxDecoration(
        color: isCritical ? AppColors.critical : AppColors.primary,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
      ),
    );
  }
}
